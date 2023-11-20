#
# spec file for package protonmail-bridge
#


Name:           protonmail-bridge
Version:        3.6.1
Release:        0
Summary:        Proton Mail Bridge
License:        GPL-3.0-only
Group:          Productivity/Networking/Email/Utilities
URL:            https://proton.me/mail/bridge
Source0:        proton-bridge-3.6.1.tar.gz
Source1:        vendor.tar.gz
Patch0:         0001-Rely-on-package-manager-for-dependencies-not-vcpkg.patch
Patch1:         0002-Remove-Sentry-SDK-dependency.patch
Patch2:         0003-Fix-install.patch
BuildRequires:  golang >= 1.18
BuildRequires:  grpc-devel
BuildRequires:  libsecret-devel
BuildRequires:  protobuf-devel
BuildRequires:  qt6-base-common-devel >= 6.0
BuildRequires:  qt6-base-devel >= 6.0
BuildRequires:  qt6-base-private-devel >= 6.0
BuildRequires:  qt6-qml-devel >= 6.0
BuildRequires:  qt6-quick-devel >= 6.0
BuildRequires:  qt6-svg-devel >= 6.0
BuildRequires:  qt6-tools-devel >= 6.0
BuildRequires:  qt6-tools-linguist >= 6.0
BuildRequires:  qt6-widgets-devel
Requires:       dejavu-sans-fonts
Requires:       fontconfig
Requires:       glib2
Requires:       glibc
Requires:       grpc
Requires:       libEGL
Requires:       libQt6Core6 >= 6.0
Requires:       libQt6Qml6 >= 6.0
Requires:       libQt6Quick6 >= 6.0
Requires:       libQt6QuickControls2-6 >= 6.0
Requires:       libQt6Svg6 >= 6.0
Requires:       libQt6Widgets6 >= 6.0
Requires:       libgcc
Requires:       libglvnd-glx
Requires:       libicu
Requires:       libprotobuf.so
Requires:       libsecret
Requires:       libstdc++
Requires:       libxkbcommon-x11
Suggests:       gnome-keyring
Suggests:       pass
Provides:       proton-bridge

# Makefile version: ./utils/get_revision.sh
# build.sh version: git rev-parse --short=10 HEAD
%define revision 248fbf5e33

# Tag (just use version macro -- usually Version="${Tag}+git"):
# Makefile version: ./utils/get_revision.sh tag
# build.sh version: git describe --tags || echo 'NOTAG'
%define build_time %(date "+%{FT}%{T}%{z}")

%description
Proton Mail Bridge is a desktop application that runs in the background, encrypting and decrypting messages as they enter and leave your computer.

%prep
%autosetup -n proton-bridge-%{version} -p1
%setup -n proton-bridge-%{version} -T -D -a 1

%build

%make_build gofiles

%define go_constants github.com/ProtonMail/proton-bridge/v3/internal/constants
%define go_ldflags -X "%{go_constants}.FullAppName=%{summary}" -X "%{go_constants}.Version=%{version}" -X "%{go_constants}.Revision=%{revision}" -X "%{go_constants}.Tag=%{version}" -X "%{go_constants}.BuildTime=%{build_time}" -X "%{go_constants}.BuildEnv=rpmbuild"

mkdir -p build
go build -mod=vendor -tags='' -ldflags '%{go_ldflags}' -o build/bridge ./cmd/Desktop-Bridge/
go build -mod=vendor -tags='' -ldflags '%{go_ldflags}' -o build/proton-bridge ./cmd/launcher/

# upstream distributes 2 very similar desktop files, source only has 1
cp dist/proton-bridge.desktop dist/bridge-gui.desktop
echo NoDisplay=true >> dist/bridge-gui.desktop

%define __sourcedir internal/frontend/bridge-gui/bridge-gui
%cmake  \
	-D INSTALL_GTEST=OFF \
    -D BRIDGE_APP_FULL_NAME="%{summary}" \
    -D BRIDGE_VENDOR="Proton AG" \
    -D BRIDGE_REVISION="%{revision}" \
    -D BRIDGE_TAG="%{version}" \
    -D BRIDGE_BUILD_TIME="%{build_time}" \
    -D BRIDGE_BUILD_ENV="rpmbuild" \
    -D BRIDGE_APP_VERSION="%{version}"


%cmake_build

%install

mkdir -p "%{buildroot}%{_libexecdir}/protonmail/bridge"
install -m 0755 build/bridge "%{buildroot}%{_libexecdir}/protonmail/bridge/"
install -m 0755 build/proton-bridge "%{buildroot}%{_libexecdir}/protonmail/bridge/"

mkdir -p "%{buildroot}%{_bindir}"
ln -sr "%{buildroot}%{_libexecdir}/protonmail/bridge/proton-bridge" "%{buildroot}%{_bindir}/protonmail-bridge"

mkdir -p "%{buildroot}%{_datadir}/icons/hicolor/scalable/apps/"
cp -pf ./dist/bridge.svg "%{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg"

mkdir -p "%{buildroot}%{_datadir}/applications/"
cp -pf ./dist/proton-bridge.desktop "%{buildroot}%{_datadir}/applications/%{name}.desktop"
cp -pf ./dist/bridge-gui.desktop "%{buildroot}%{_datadir}/applications/ch.proton.bridge-gui.desktop"

%cmake_install

%files

%{_libexecdir}/protonmail/bridge
%{_bindir}/protonmail-bridge
%{_libdir}/libbridgepp.so

%{_datadir}/applications/ch.proton.bridge-gui.desktop
%{_datadir}/applications/protonmail-bridge.desktop
%{_datadir}/icons/hicolor/scalable/apps/protonmail-bridge.svg

# Destinations directories will be determined appropriately
%license LICENSE
%doc Changelog.md

%changelog
