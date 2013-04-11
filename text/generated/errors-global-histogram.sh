#!/bin/sh
$IMPL_DIR/errors-global.py \
    $IMPL_DIR/../data/preprocessed/one_week_clock_offsets.npy \
    --no-show --save-pseudorange-histogram $1
