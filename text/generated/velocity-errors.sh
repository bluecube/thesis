#!/bin/sh
$IMPL_DIR/errors-per-sv.py \
    $IMPL_DIR/../data/preprocessed/one_week_clock_offsets.npy \
    --no-show --only-sv 6 --save-velocity-errors $1,701000,6,726000,-6
