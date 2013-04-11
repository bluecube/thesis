#!/bin/sh
$IMPL_DIR/errors-global.py \
    $IMPL_DIR/../data/preprocessed/one_week_clock_offsets.npy \
    --no-show --save-pseudorange-errors $1,701000,150,726000,-100
