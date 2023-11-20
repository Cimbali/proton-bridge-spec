#!/bin/bash

mkdir -p build
spec-cleaner protonmail-bridge.spec > build/protonmail-bridge.spec

absbuild=`readlink -f build/`
rpmbuild -D "_topdir $absbuild" -D "_sourcedir $absbuild/.." -D "_srcrpmdir $absbuild" -D "_rpmdir $absbuild" -ba "$absbuild/protonmail-bridge.spec"
