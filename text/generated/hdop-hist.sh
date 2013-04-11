#!/bin/sh
$IMPL_DIR/compare_hdop_histogram.py \
	$IMPL_DIR/../data/preprocessed/month_wgs84.npy \
	$IMPL_DIR/../data/roboauto_merged.recording2 \
	$IMPL_DIR/../data/30_minutes_weak_signal.recording2 \
	--label '\enquote{Month} dataset','\enquote{Roboauto} dataset','\enquote{30 minutes} dataset' \
	--max-plot-hdop 10 --save-hist-plot $1 --no-show
