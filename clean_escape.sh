#!/bin/bash

# Check if a filename was passed as a command-line argument
if [ -n "$1" ]; then
    name="$1"
else
    echo "ENTER FILENAME WITH EXTENSION"
    read name
fi

# Extract base name and extension
base="${name%.*}"
ext="${name##*.}"

# Handle case where there is no extension
if [[ "$name" == "$ext" ]]; then
    cleanname="${name}.clean"
else
    cleanname="${base}.clean.${ext}"
fi

# Run sed to remove redundant ANSI escape sequences
sed -E -e :a -e $'s/(\e\\[[0-9;]*m)([[:print:]]*)\\1/\\1\\2/; ta' "$name" > "$cleanname"

echo "Cleaned file saved as: $cleanname"
