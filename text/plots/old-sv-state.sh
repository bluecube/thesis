#!/bin/sh
echo '\begin{verbatim}' > $1
$IMPL_DIR/old_sv_state.py --help 2>&1 >> $1
echo '\end{verbatim}' >> $1
