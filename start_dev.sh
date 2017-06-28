#!/usr/bin/env bash

STOPPING=false
export NO_BROWSER="${1:-true}"
export CODEGRADE_DATABASE_URL="postgresql:///codegrade_dev"

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo 'You are not in the virtual env. Execute `source env/bin/activate` first!'
    exit 1
fi

echo "Migrating and upgrading database"
./manage.py db migrate
./manage.py db upgrade
./manage.py seed
./manage.py test_data

if [[ "${1:-true}" = "migrate" ]]; then
    exit 0
fi

echo "Echo starting python and NPM, press Ctrl-C to stop"

quit() {
    STOPPING=true
    echo "Stopping!"
    echo "$npm $python"
    kill "$python"
    kill -9 "$npm"
}

trap "quit" SIGINT SIGTERM

./run.py &
python="$!"
npm install
npm run dev &
npm="$!"

while true; do
    wait -n "$npm" "$python"
    status="$?"
    if $STOPPING || [[ $status -ne 0 ]]; then
        echo "NPM or python crashed!"
        $STOPPING || quit
        exit "$status"
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
