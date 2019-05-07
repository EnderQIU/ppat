#!/bin/bash
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
set -e
echo "[1/3] Installing dependencies via APT. Following packages will be ensured to be installed:"
echo "\tmake autoconf automake libtool pkg-config gcc git\n"
sudo apt-get install make autoconf automake libtool pkg-config -y
sudo apt-get install gcc -y
echo "Dependencies installed."
echo "[2/3] Fetching espeak source codes ..."
git submodule update --init --recursive
echo "[3/3] Build & install espeak to ppat/espeak/espeak.install ..."
cd "$SCRIPTPATH/espeak.src" && ./autogen.sh
cd "$SCRIPTPATH/espeak.src" && ./configure --prefix="$SCRIPTPATH/espeak.install/"
cd "$SCRIPTPATH/espeak.src" && make clean
cd "$SCRIPTPATH/espeak.src" && make install
echo "build.sh completed. espeak executable has been installed in ppat/espeak/espeak.install"
set +e
