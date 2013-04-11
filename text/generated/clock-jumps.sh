#!/bin/sh
$IMPL_DIR/clock-jumps.py \
    $IMPL_DIR/../data/preprocessed/one_week_clock_offsets.npy \
    --no-show --save-plot $1,701000,0.3,726000,-0.1
