echo "Installing dependencies via APT...This will require root permissions."
sudo apt-get install make autoconf automake libtool pkg-config -y
sudo apt-get install gcc -y
echo "Dependencies installed. Build & install espeak to ./espeak.install ..."
cd espeak.src
./autogen.sh
./configure --prefix=$(pwd)/espeak.install/
make clean
make install
echo "build.sh complete. Please check espeak executable in ./espeak.install/bin/"
