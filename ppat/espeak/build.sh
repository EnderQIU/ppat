#!/bin/bash
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
set -e
echo "[1/3] Installing dependencies via APT. Following packages will be ensured to be installed:"
echo "	make autoconf automake libtool pkg-config gcc git"
read -p "[1/3] Procceed? [y/N]" choice
if [ $choice == "y" ];
then
	sudo apt-get install make autoconf automake libtool pkg-config -y
	sudo apt-get install gcc -y
	echo "[1/3] Dependencies installed."
else
	echo "[1/3] You have passed make tools installation. Please make sure you already have packages installed above."
fi
echo "[2/3] Fetching espeak source code ..."
cd "$SCRIPTPATH/espeak.src" && count=`ls $*|wc -w`
if [ "$count" > "0" ];
then
	echo "[2/3] espeak source code maybe already exist."
	read -p "[2/3] Overwrite anyway? [y/N]" choice
	if [ $choice == "y" ];
	then
		cd "$SCRIPTPATH/espeak.src" && rm -rf ./*
		git submodule update --init --recursive
	else
		echo "[2/3] Canceled. Make sure you already have either espeak source code in ppat/espeak.src or ’espeak‘ executable installed."
	fi
else
	echo "[2/3] Fetching espeak source codes ..."
	git submodule update --init --recursive
fi
echo "[3/3] Build & install espeak to ppat/espeak/espeak.install ..."
read -p "[3/3] Start building espeak executable? [y/N]" choice
if [ $choice == "y" ];
then
	cd "$SCRIPTPATH/espeak.src" && ./autogen.sh
	cd "$SCRIPTPATH/espeak.src" && ./configure --prefix="$SCRIPTPATH/espeak.install/"
	cd "$SCRIPTPATH/espeak.src" && make clean
	cd "$SCRIPTPATH/espeak.src" && make install
	echo "[3/3] build.sh completed. espeak executable has been installed in ppat/espeak/espeak.install"
else
	echo "[3/3] Canceled. Make sure you already have either built espeak source code in ppat/espeak.install or ’espeak‘ executable installed."
fi
set +e
