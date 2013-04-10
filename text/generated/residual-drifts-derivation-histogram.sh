#!/bin/sh
$IMPL_DIR/errors-per-sv-merged.py \
    $IMPL_DIR/../data/preprocessed/month_clock_offsets.npy \
    --no-show --save-residual-drifts-derivation-histogram $1
