#!/bin/bash

# Script to convert between .ipynb and .py using jupytext
# Full name: jtoggle
# Usage: jt filename.ipynb OR jt filename.py

if [ -z "$1" ]; then
    echo "Usage: jt <filename.ipynb|filename.py>"
    exit 1
fi

FILE=$1

if [[ "$FILE" == *.ipynb ]]; then
    echo "Converting $FILE to .py"
    jupytext --to py "$FILE"
elif [[ "$FILE" == *.py ]]; then
    echo "Converting $FILE to .ipynb"
    jupytext --to ipynb --update "$FILE"
else
    echo "Error: File must end in .ipynb or .py"
    exit 1
fi
