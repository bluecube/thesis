#!/bin/sh
echo '\begin{verbatim}' > $1
$IMPL_DIR/record.py --help 2>&1 >> $1
echo '\end{verbatim}' >> $1
