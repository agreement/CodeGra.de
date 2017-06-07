#!/bin/bash

STOPPING=false
export NO_BROWSER="${1:-true}"

echo "Echo starting python and NPM, press Ctrl-C to stop"

./run.py &
python="$!"
npm install
npm run dev &
npm="$!"

quit() {
    STOPPING=true
    echo "Stopping!"
    kill "$python" "$npm"
}

trap "quit" SIGINT SIGTERM

while true; do
    wait -n "$npm" "$python"
    status="$?"
    if [[ $status -ne 0 ]]; then
        if ! $STOPPING; then
            echo "NPM or python crashed!"
            quit
        fi
        exit $?
    fi
    if kill -0 "$python" 2> /dev/null; then
        echo "Restarting NPM"
        npm install
        npm run dev &
        npm="$!"
    else
        echo "Restarting Python"
        ./run.py &
        python="$!"
    fi
done
