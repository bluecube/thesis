#!/bin/sh
DIR="$( cd "$( dirname "$0" )" && pwd )"/../../impl/
$DIR/compare_hdop_histogram.py \
	$DIR/recordings/processed_numpy_arrays/month_wgs84.npy \
	$DIR/recordings/roboauto_merged.recording2 \
	--label '"Month" dataset','"Roboauto" dataset' \
	--max-plot-hdop 10 --save-hist-plot $1 --no-show
