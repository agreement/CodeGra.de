#!/bin/bash

install-pkg() {
    case "$OSTYPE" in
        linux*) sudo apt-get install "$*";;
        darwin*) brew install "$*";;
        *) echo "Not supported!"; exit 1;;
    esac
}

which psql > /dev/null || install-pkg "postgresql"
which npm > /dev/null || install-pkg "node"
which virtualenv > /dev/null || install-pkg "virtualenv"

if ! [[ -d env ]]; then
    virtualenv env -p python3
fi

source env/bin/activate

echo "Installing python requirements"
pip install -r requirements.txt > /dev/null

echo "Installing NPM requirements"
npm install > /dev/null
