<p align="center">
  <a href="https://codegra.de">
    <img src="https://codegra.de/static/img/codegrade-inv.svg" alt="CodeGra.de" title="CodeGra.de" height="130">
  </a>
</p>
<p align="center">
  <!--<a href="https://github.com/CodeGra-de/CodeGra.de/releases">
    <img src="https://img.shields.io/github/downloads/CodeGra-de/CodeGra.de/total.svg?maxAge=2592000"
      alt="Downloads" title="Downloads">
  </a>-->
  <a href="https://travis-ci.org/CodeGra-de/CodeGra.de">
    <img src="https://img.shields.io/travis/CodeGra-de/CodeGra.de.svg"
      alt="Build Status" title="Build Status">
  </a>
  <a href="https://coveralls.io/github/CodeGra-de/CodeGra.de?branch=master">
    <img src="https://img.shields.io/coveralls/CodeGra-de/CodeGra.de.svg"
      alt="Coverage Status" title="Coverage Status">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de">
    <img src="https://5ezz6jithh.execute-api.us-east-1.amazonaws.com/prod/lambda-shield-redirect?user=CodeGra-de&repo=CodeGra.de"
      alt="Source Lines of Code" title="Source Lines of Code">
  </a>
  <a href="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/">
    <img src="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/shield.svg"
      alt="Python updates" title="Python updates">
  </a>
  <a href="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/">
    <img src="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/python-3-shield.svg"
      alt="Python 3 ready" title="Python 3 ready" style="margin-right: -7px;">
  </a>
  <a href="https://codegra.de">
    <img src="https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20&%20%F0%9F%8D%BB-ff69b4.svg"
      alt="Made with ❤ & ️🍻" title="Made with ❤ & ️🍻">
  </a>
  <a href="https://codegra.de">
    <img src="https://img.shields.io/badge/website-CodeGra.de-blue.svg"
      alt="Website: CodeGra.de" title="Website: CodeGra.de">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/tags">
    <img src="https://img.shields.io/github/tag/CodeGra-de/CodeGra.de.svg"
      alt="Latest git tag" title="Latest git tag">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/releases">
    <img src="https://img.shields.io/github/release/CodeGra-de/CodeGra.de.svg"
      alt="Latest release" title="Latest release">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/releases">
    <img src="https://img.shields.io/badge/semVer-✓-green.svg"
      alt="Semantic Version: ✓" title="Semantic Version">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/issues">
    <img src="https://img.shields.io/github/issues-raw/CodeGra-de/CodeGra.de.svg"
      alt="Open GitHub Issues" title="Open GitHub Issues">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/issues">
    <img src="https://img.shields.io/github/issues-closed-raw/CodeGra-de/CodeGra.de.svg"
      alt="Closed GitHub Issues" title="Closed GitHub Issues">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/issues">
    <img src="https://img.shields.io/issuestats/i/github/CodeGra-de/CodeGra.de.svg"
      alt="Closed GitHub Issues" title="Closed GitHub Issues">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/pulls">
    <img src="https://img.shields.io/github/issues-pr-raw/CodeGra-de/CodeGra.de.svg"
      alt="Open GitHub Pull Requests" title="Open GitHub Pull Requests">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/pulls">
    <img src="https://img.shields.io/issuestats/p/github/CodeGra-de/CodeGra.de.svg"
      alt="Open GitHub Pull Requests" title="Open GitHub Pull Requests">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de">
    <img src="https://reposs.herokuapp.com/?path=CodeGra-de/CodeGra.de"
      alt="Repository size" title="Repository size">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg"
      alt="License AGPL-3.0" title="License AGPL-3.0">
  </a>
  <a href="https://matrix.to/#/#CodeGra.de:matrix.org">
    <img src="https://img.shields.io/badge/matrix-user-43ad8d.svg"
      alt="Chat on Matrix: #CodeGra.de:matrix.org"
      title="Chat on Matrix: #CodeGra.de:matrix.org">
  </a>
  <a href="https://matrix.to/#/#DevCodeGra.de:matrix.org">
    <img src="https://img.shields.io/badge/matrix-dev-4e42aa.svg"
      alt="Chat as developer on Matrix #DevCodeGra.de:matrix.org"
      title="Chat as developer on Matrix #DevCodeGra.de:matrix.org">
  </a>
</p>
<p align="center">
  <a href="https://waffle.io/CodeGra-de/CodeGra.de/metrics">
    <img src="https://graphs.waffle.io/CodeGra-de/CodeGra.de/throughput.svg"
      alt="Metrics on waffle.io" title="Metrics on waffle.io">
  </a>
</p>

A code review tool

## Build Setup

### PostgreSQL initial setup for local development

```bash
sudo apt-get install postgresql postgresql-contrib
```

Set a password for the postgres user:
```bash
sudo passwd postgres
```

Change to the postgres user to setup the server and database (only when using
Arch):
```bash
sudo -u postgres initdb -D "/var/lib/postgres/data"
```

Startup postgres server:
```bash
sudo systemctl enable postgresql.service
sudo systemctl start postgresql.serive
```

Change to the postgres user again and execute the psql shell (replace $USERNAME
with your username):
```bash
sudo -u postgres -i 
createuser -s $USERNAME
exit
sudo -u postgres psql
```

Create the database:
```sql
create database codegrade_dev;
\q
```

### Deploying

```bash
./deploy.sh
```

### Starting dev server

And later to start (false as command line argument to auto open the browser).
```bash
source env/bin/activate
./start_dev.sh
```

### Resetting database

Sometimes just migrating is not enough and this will fail with a bunch of errors.
In this case we need to remove and add the database again:

```bash
sudo -u postgres psql
```

```sql
drop database codegrade_dev;
create database codegrade_dev;
\q
```

Remove the migrations directory and redeploy and restart the dev server.
```bash
rm -rf migrations/
./deploy.sh
./start_dev.sh
```
