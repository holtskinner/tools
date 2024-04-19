#!/bin/bash

# Check if a directory is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

directory=$1

# Check if the directory exists
if [ ! -d "$directory" ]; then
    echo "Directory not found: $directory"
    exit 1
fi

# Use find command to list all non-hidden files in the directory recursively
# Sort the files by size in descending order
# Print the first 10 largest files
find "$directory" -type f -not -path '*/\.*' -exec du -h {} + | sort -rh | head -n 10
