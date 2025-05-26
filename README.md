# clean_escape
Bash script to remove redundant ANSI escape codes from text-mode art.

Removes consecutive, non-adjacent, identical escape sequences. (i.e. "\e[1;31mR\e[1;31mE\e[1;31mD" becomes "\e[1;31mRED")
