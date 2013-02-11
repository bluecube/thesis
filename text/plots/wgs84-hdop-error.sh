#!/bin/sh
$IMPL_DIR/wgs84_errors.py \
	$IMPL_DIR/recordings/processed_numpy_arrays/month_wgs84.npy \
	--plotted-sample-count 10000 --max-plot-hdop 4 --max-plot-error 20 \
	--save-hdop-plot $1 --no-show
