#!/usr/bin/env bash
echo "NOTE THIS IS VERY HACKY AND PROBABLY WON'T WORK WITH YOUR POSTGRESQL INSTALL"
echo "Dropping and creating database"
dropdb "codegrade_dev"
psql -c "create database codegrade_dev"
if [[ "$1" = "prod" ]]; then
    psql -d "codegrade_dev" -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA  public TO "www-data"'
    psql -d "codegrade_dev" -c 'GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO "www-data"'
    psql -d "codegrade_dev" -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "www-data"'
    psql -d "codegrade_dev" -c 'GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO "www-data"'
    psql -c 'grant all privileges on database codegrade_dev  to "www-data";'
    psql -d "codegrade_dev" -c 'GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO "www-data"'
    psql -d "codegrade_dev" -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "www-data"'
fi
echo "Removing migrations and uploads directories"
rm -r migrations/
rm -fr uploads/
echo "Deploying"
./deploy.sh
