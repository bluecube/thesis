#!/bin/sh
$IMPL_DIR/compare_hdop_histogram.py \
	$IMPL_DIR/recordings/processed_numpy_arrays/month_wgs84.npy \
	$IMPL_DIR/recordings/roboauto_merged.recording2 \
	--label '"Month" dataset','"Roboauto" dataset' \
	--max-plot-hdop 10 --save-hist-plot $1 --no-show
