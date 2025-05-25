#!/bin/bash

# Prompt user for name of ANSI
echo "ENTER FILENAME WITH EXTENSION"
read name

# Extract base name and extension
base="${name%.*}"         # Everything before the last dot
ext="${name##*.}"         # Everything after the last dot

# Create cleaned filename: insert .clean before the extension
cleanname="${base}.clean.${ext}"

# Run sed to remove redundant ANSI escape sequences
sed -E -e :a -e $'s/(\e\\[[0-9;]*m)([[:print:]]*)\\1/\\1\\2/; ta' "$name" > "$cleanname"
