#!/usr/bin/bash

declare -a ptrns=("undeliv" "mailer-daemon" "delivery-status")
declare -a fields=("Envelope-to:" "Delivery-date:" "Diagnostic-Code:")

# Search Key Words
search () {
    echo -e "\e[94m$1\e[39m"
    count=0
    for ptrn in "${ptrns[@]}"
    do
        if grep -qi "$ptrn" $1; then
            count=$((count+$(grep -c "$ptrn" $1 | wc -l)))
        fi
    done

    if [ $count -gt 0 ]
    then
    echo -e "  \e[33m[+] Found \e[31m$count \e[33mindicator(s)\e[39m"
    
        for field in "${fields[@]}"
        do
            echo -e "  \e[90m$(grep -i "$field" $1)\e[39m"
        done
    else
        echo -e "  \e[31m[!] $(grep -i "no such user|recipient rejected" $1)\e[39m"
    fi
    return 0
}

# Locate files with bounce-like messages
f_list=$(find ~/mail \( -path \.Sent -o -path \.Drafts \) -prune -o -type f ! -iname *dovecot* -exec grep -li "return-path: <>" {} \;)

echo -e "\e[33m[*] Found \e[31m$( grep -c '^' $f_list | wc -l )\e[33m suspected bounce(s)\e[39m"

# Search for bounce indicator patterns and if there are any,
# store the headers for the report
while IFS= read -r file; do search $file; done <<< "$f_list"

