#!/bin/sh
$IMPL_DIR/errors-per-sv.py \
    $IMPL_DIR/../data/preprocessed/one_week_clock_offsets.npy \
    --no-show --only-sv 6 --save-pseudorange-errors $1,701000,150,726000,-150
