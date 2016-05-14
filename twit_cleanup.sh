#!/usr/bin/bash

# Condenses whitespace in a file (maintains line breaks)

prompt="Please enter a file to scrub > "

# If a filename was passed at the command line
# and it exists, scrub that file
if [ $# -eq 2 ]; then
    f = $1
else
    echo -n $prompt
    read f
fi

while true; do
    # Test to ensure file exists and prompt
    # until a valid file is entered
    if ! [ -e $f ]; then
        echo "Invalid file : $f"
        echo -n $prompt
        read f
    else
        echo "File confirmed : $f"
        break
    fi
done

opath="$f.scrubbed"
touch $opath

set -f
while read line; do
    set -- $line
    line=$*
    echo $line >> $opath # Use when keeping newlines
    #echo  -n $line >> $opath # Will strip newlines as well.
done < $f
set +f

mv $f $f.$(date +%s).bak
mv $opath $f
echo "Scrubbed extra whitespace"
