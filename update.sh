#!/bin/bash

# Parameters
repo=ProtonMail/proton-bridge
releases=releases.json
archive=proton-bridge-VERSION.tar.gz
spec=protonmail-bridge.spec
changes=protonmail-bridge.changes
build=${DESTDIR:-build}

# Curl common args to access the GH API as an array
curl=(curl -s -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")
# You may skip tokens, or use one from env, etc.
if [ -n "$GITHUB_TOKEN" ]; then
	curl+=(-H "Authorization: Bearer $GITHUB_TOKEN")
else
	curl+=(-H "Authorization: Bearer `kwallet-query -r cimbali@github kdewallet`")
fi

# Bail if anything goes wrong
set -e

mkdir -p "$build/"

# Fetch/get tag
# -f = fetch? force? Anyways, get the latest from online and update local files accordingly
if [[ "$1" != "-f" ]] && (( $# )); then
	tag=$1

	if [[ "$tag" =~ ^v[0-9]+(\.[0-9]+){2}$ ]]; then
		echo Using tag $tag
	else
		echo "Tag $tag does not fit the expected format 'v{Major}.{Minor}.{Patch}'"
		exit 1
	fi
else
	"${curl[@]}" "https://api.github.com/repos/$repo/releases" -o "$build/$releases"
	tag=`jq -r 'map(select(.prerelease | not))[0].tag_name' "$build/$releases"`
	echo Latest tag fetched: $tag
fi

# Ensure we have the right files
build="`readlink -f "$build"`"
archive=${archive/VERSION/${tag#v}}
cd "`readlink -zf $0 | xargs -0 dirname`"

# Check tag revision
"${curl[@]}" "https://api.github.com/repos/$repo/tags" -o "$build/tags.json"
sha=`jq -r "map(select(.name == \"$tag\"))[0].commit.sha[:10]" "$build/tags.json"`

if (( $# )); then
	echo "Setting revision to $sha in spec file"
	sed -i "s/^\\(Version:\\s*\\)\\S*/\\1${tag#v}/;s/^\\(Source0:\\s*\\)\\S*/\\1${archive}/;s/^%define revision [0-9a-f]*\$/%define revision $sha/" "$spec"
elif ! grep -q "^Version:\\s*${tag#v}\\$" "$spec" || ! grep -q "^%define revision $sha\\$" "$spec"; then
	echo "Revision and tag in do not match in $spec: expected $sha for $tag"
	echo "To update from latest found online version, run: $0 -f"
	exit 1
else
	echo "Revision and tag match in $spec"
fi

if [ ! -f "$build/$archive" ]; then
	curl -L "https://github.com/$repo/archive/refs/tags/${tag}.tar.gz" -o "$build/$archive"
fi
if [ ! -f "$build/vendor.tar.gz" ] || [ "$build/$archive" -nt "$build/vendor.tar.gz" ]; then
	cd "$build"
	# can’t handle abs archive paths
	/usr/lib/obs/service/go_modules --archive "$archive" --outdir "$build"
	cd "$OLDPWD"
fi

# If running CI, just exit after downloading files
if [ -n "$CI" ]; then
	ls -l "$build/$archive"
	exit 0
fi

(
# Prepend version item to changelog
echo "- Update to version $tag"
# Also prepend pandoc-wrapped (for list awareness) body of github release
jq -r "map(select(.tag_name == \"$tag\"))[0].body" "$build/$releases" | sed -r \
	-e 's/^[-*]/  &/;s/\r$//;/^#+ (Added|Changed|Fixed)/d;/^$/d' \
	-e "s,(#|https://github.com/$repo/pull/)([0-9]+),gh#\\2,"
) | pandoc --from=markdown --to=markdown --columns=70 |
	sed -r 's/^ {8}/    /;s/^- {3}/- /;s/^ {4}- {3}/  * /;$a\\' |
	sed -i '0r/dev/stdin' "$changes"

# Update changelog
osc vc

# Build clean specfile and vendor archive
spec-cleaner "$spec" > "$build/$spec"

git ls-files -z \*.patch | xargs -r0 cp -lt "$build/"
rpmbuild -D "_topdir $build" -D "_sourcedir $build" -D "_srcrpmdir $build" -ba "$build/$spec"

git commit -em "Version $tag" "$spec" "$changes"
