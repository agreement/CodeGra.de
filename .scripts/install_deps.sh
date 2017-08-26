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
which virtualenv > /dev/null || pip3 install "virtualenv" --user

[[ -d './uploads' ]] || mkdir uploads

case "$OSTYPE" in
    darwin*) brew install bash;;
esac

if ! [[ -d env ]]; then
    virtualenv env -p python3
fi

source env/bin/activate

echo "Installing python requirements"
pip install -r requirements.txt > /dev/null

echo "Installing NPM requirements"
npm install > /dev/null
git submodule update --init static/vendor/pdf.js >/dev/null
cd static/vendor/pdf.js
npm install > /dev/null

echo "Initializing database"
export CODEGRADE_DATABASE_URL="postgresql:///codegrade_dev"
