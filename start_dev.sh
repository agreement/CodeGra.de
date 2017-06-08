#!/usr/bin/env bash

STOPPING=false
export NO_BROWSER="${1:-true}"
export CODEGRADE_DATABASE_URL="postgresql://localhost/codegrade_dev"

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo 'You are not in the virtual env. Execute `source env/bin/activate` first!'
    exit 1
fi

echo "Migrating and upgrading database"
./manage.py db migrate
./manage.py db upgrade

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
