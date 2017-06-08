# client

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

Change to the postgres user to setup the server and database:
```bash
sudo -u postgres -i
```

Initialize the server and exit out of the postgres user:
```bash
initdb -D "/var/lib/postgres/data"
exit
```

Startup postgres server:
```bash
sudo systemctl enable postgresql.service
sudo systemctl start postgresql.serive
```

Change to the postgres user again and execute the psql shell:
```bash
sudo -u postgres -i
psql
```

Create the database:
```bash
create database codegrade_dev;
```

### Deploying

``` bash
./deploy.sh
```

### Starting dev server

And later to start (false as command line argument to auto open the browser).
```bash
source env/bin/activate
./start_dev.sh
```

