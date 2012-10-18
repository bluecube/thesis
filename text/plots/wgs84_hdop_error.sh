#!/bin/sh
DIR="$( cd "$( dirname "$0" )" && pwd )"/../../impl/
$DIR/wgs84_errors.py \
	$DIR/recordings/processed_numpy_arrays/month_wgs84.npy \
	--plotted-sample-count 10000 --max-plot-hdop 4 --max-plot-error 20 \
	--save-hdop-plot $1 --no-show
