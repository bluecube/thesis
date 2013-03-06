#!/bin/sh
echo '\begin{verbatim}' > $1
$IMPL_DIR/checksum.py --help 2>&1 >> $1
echo '\end{verbatim}' >> $1
