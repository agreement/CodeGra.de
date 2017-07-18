<p align="center"
  <a href="https://codegra.de">
    <img src="https://codegra.de/static/img/codegrade-inv.svg" alt="CodeGrade" height="130">
  </a>
</p>
<p align="center"
  <a href="https://travis-ci.org/CodeGra-de/CodeGra.de">
    <img src="https://travis-ci.org/CodeGra-de/CodeGra.de.svg?branch=master"
      alt="Build Status">
  </a>
  <a href="https://coveralls.io/github/CodeGra-de/CodeGra.de?branch=master">
    <img src="https://coveralls.io/repos/github/CodeGra-de/CodeGra.de/badge.svg?branch=master"
      alt="Coverage Status">
  </a>
  <a href="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/">
    <img src="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/shield.svg"
      alt="Updates">
  </a>
  <a href="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/">
    <img src="https://pyup.io/repos/github/CodeGra-de/CodeGra.de/python-3-shield.svg"
      alt="Python 3">
  </a>
  <img src="https://img.shields.io/badge/style-%E2%9D%A4%EF%B8%8F%20&%20%F0%9F%8D%BB-ff69b4.svg?label=Made%20with"
    alt="Made with ❤ & ️🍻">
  <a href="https://codegra.de">
    <img src="https://img.shields.io/badge/style-CodeGra.de-blue.svg?label=Website"
      alt="CodeGra.de">
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
