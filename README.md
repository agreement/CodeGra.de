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
