#!/bin/sh

set -e
set -o pipefail

dir=$1

cd $(dirname $0)

if [ ! -d "$dir" ] ; then
    echo "First argument must be a directory"
    exit 1
fi

rm -rf $dir
mkdir $dir

git clone https://github.com/bluecube/thesis.git $dir/repository
cp -r $dir/repository/impl $dir
ln -s $(realpath data) $dir

make -C text all
cp -r text/build/thesis.pdf $dir

./gen_usage.sh > $dir/usage.txt
