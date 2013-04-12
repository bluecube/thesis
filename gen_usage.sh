#!/bin/sh

find $(dirname $0)/impl -executable -name '*.py' | sort| while read file ; do
    echo
    echo $(basename $file)
    echo "========================"
    echo
    $file --help 2>/dev/null
    echo
    echo
    done
