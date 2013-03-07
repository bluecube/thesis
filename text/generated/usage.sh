#!/bin/sh
echo '\begin{verbatim}' > $1
$IMPL_DIR/$(basename $0 | sed 's/-/_/g ;s/.sh$/.py/') --help 2>&1 >> $1
echo '\end{verbatim}' >> $1
