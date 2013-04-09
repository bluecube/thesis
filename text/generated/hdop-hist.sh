#!/bin/sh
$IMPL_DIR/compare_hdop_histogram.py \
	$IMPL_DIR/../data/preprocessed/month_wgs84.npy \
	$IMPL_DIR/../data/roboauto_merged.recording2 \
	--label '"Month" dataset','"Roboauto" dataset' \
	--max-plot-hdop 10 --save-hist-plot $1 --no-show
