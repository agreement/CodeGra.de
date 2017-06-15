#!/usr/bin/env bash
echo "NOTE THIS IS VERY HACKY AND PROBABLY WON'T WORK WITH YOUR POSTGRESQL INSTALL"
echo "Dropping and creating database"
dropdb "codegrade_dev"
psql -c "create database codegrade_dev"
echo "Removing migrations and uploads directories"
rm -r migrations/
rm -r uploads/
echo "Deploying"
./deploy.sh
