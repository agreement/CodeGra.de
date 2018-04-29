Building CodeGra.de
==========================

This document describes the process of building CodeGra.de and installing requirements. The steps below are
required for both a development build and a production build of CodeGra.de. Please
conduct the `running <running.html>`_ instructions for more information on running CodeGra.de after
building is finished.

Prerequisites
---------------
Building CodeGra.de requires an installation of the following software packages:

* Python 3.6 (or newer)
* PostgreSQL
* Nodejs

*Please note that the installation of some of the above packages is highly
recommended, however alternatives can be used.*

General Set-Up
------------------
Production and dev mode share a few steps that are relevant for both. The first
is copying ``config.ini.example`` to ``config.ini``. Now you should read this
file and make the necessary changes. Especially the part about ``secret_key`` is
very important. After reading this you should setup your database, CodeGra.de is
tested using SQLite and PostgreSQL, but we recommend running with PostgreSQL for
production. So for this document we will assume that you are using this
database.

Now we need to setup celery. Celery can be run using multiple brokers. For this
application the choice of the broker is important. It is highly recommended that
you read how celery works and the differences between brokers, however it is not
required. We recommend using RabbitMQ as the broker. After setting up your
broker you need to change this information in ``config.ini``.

You should start by creating a new database and user in the Postgres console and
granting the all the rights on the database to the new user. The easiest way to
grant the privileges is to change the owner of the new database. After doing
this you should edit ``config.ini`` with your new database information.

Privacy Statement
^^^^^^^^^^^^^^^^^^
Now you can optionally create your own privacy statement. Please note that
CodeGra.de is not responsible for this privacy statement or the default in what
way whatsoever. Creating a custom privacy statement is done by placing a
``PRIVACY_STATEMENT.md`` in the root of the project directory. Please note that
after changing this file you need to build or restart the front-end again (this
step is explained later). Also note that while this file is in markdown, you may
include literal html tags, but you should not use any JavaScript for security
reasons.

Installing further requirements
---------------------------------
After doing this you should setup a *virtualenv* in the root folder, the minimum
python version required to run Codegra.de is Python 3.6. Now activate this
environment. After doing this you should run
``npm install``, ``pip install -r requirements.txt`` and ``( cd
static/vendor/pdf.js && npm install )`` all from within the project root.

Populating the database
------------------------
Now you should create the tables in the database. This is done by running ``make
db_upgrade``. After this you should populate the database with the seed data,
this is done by running ``make seed``.
