rm -fr ./c_src/build
mkdir ./c_src/build
cmake -S ./c_src -B ./c_src/build
make -C ./c_src/build
cp ./c_src/build/libAstar.so ./libAstar.so