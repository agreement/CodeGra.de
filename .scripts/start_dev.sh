#!/usr/bin/env bash
export NO_BROWSER="true"
export CODEGRADE_DATABASE_URL="postgresql:///codegrade_dev"


if [[ "$1" = npm ]]; then
    npm run dev
elif [[ "$1" = python ]]; then
    if [[ -z "$VIRTUAL_ENV" ]]; then
        source ./env/bin/activate
    fi

    if [ "$TERM" != dumb ] && hash tput 2>/dev/null; then
        ./run.py 2>&1 | sed \
            -e 's/ \(2[[:digit:]]\{2\}\) -/ '$(tput setaf 2)'\1'$(tput sgr0)' -/' \
            -e 's/ \(3[[:digit:]]\{2\}\) -/ '$(tput setaf 3)'\1'$(tput sgr0)' -/' \
            -e 's/ \([45][[:digit:]]\{2\}\) -/ '$(tput setaf 1)'\1'$(tput sgr0)' -/'
    else
        ./run.py
    fi
fi
