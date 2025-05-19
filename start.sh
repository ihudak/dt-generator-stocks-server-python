#!/bin/sh

. venv/bin/activate

export INITSTOCKS=1000
export MAXSTOCKS=100000
#export LOG_DEST=stocks_py
export LOG_DEST=stocks
export CRASH_SIM=10

python ./stock_server.py

