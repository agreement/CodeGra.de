How to run CodeGra.de
==========================

This document describes how to run CodeGra.de. CodeGra.de consists of two
elements, its front-end and its backend. The front-end is build using Vue.JS and
the back-end is a flask website. This means that the two components have their
own build and deploy steps for running in the dev and production mode.

General steps
------------------

Production and dev mode share a few steps that are relevant for both. The first
is copying ``config.ini.example`` to ``config.ini``. Now you should read this
file and make the necessary changes. Especially the part about ``secret_key`` is
very important. After reading this you should setup your database, CodeGra.de is
tested using SQLite and PostgreSQL, but we recommend running with PostgreSQL for
production. So for this document we will assume that you are using this
database.

You should start by creating a new database and user in the postgres console and
granting the all the rights on the database to the new user. The easiest way to
grant the privileges is to change the owner of the new database. After doing
this you should edit ``config.ini`` with your new database information.

Now you can optionally create your own privacy statement. Please note that
CodeGra.de is not responsible for this privacy statement or the default in what
way whatsoever. Creating a custom privacy statement is done by placing a
``PRIVACY_STATEMENT.md`` in the root of the project directory. Please note that
after changing this file you need to build or restart the front-end again (this
step is explained later). Also note that while this file is in markdown, you may
include literal html tags, but you should not use any JavaScript for security
reasons.

After doing this you should setup a virtualenv in the root folder, the minimum
python version required to run Codegra.de is python 3.6. Now activate this
environment. After doing this you should install the dependencies, this is done
by installing ``postgresql`` and ``nodejs``. After doing this you should run
``npm install``, ``pip install -r requirements.txt`` and ``( cd
static/vendor/pdf.js && npm install )`` all from within the project root.

Now you should create the tables in the database. This is done by running ``make
db_upgrade``. After this you should populate the database with the seed data,
this is done by running ``make seed``.

Dev. mode
------------------

Starting the dev server is quite easy. As the project consists of two parts,
those two parts should both be running. This can be achieved by running ``make
start_dev_npm`` in a terminal and ``make start_dev_server`` in another terminal.
The first terminal now runs the front-end while the second runs the back-end.

Production mode
-------------------

Running CodeGra.de in production mode is a bit more complicated. The first step
is building the front-end code. This is done using ``make build_front-end``,
this builds these files to the ``dist`` folder. This folder should be served by
a webserver. This is the only folder that should be server by the webserver,
however all requests starting with ``/api/`` should be forwarded to our
back-end.

To do this we should first start the back-end in production mode. In the
example ini file (``config.ini.example``) we use ``uwsgi`` to do this. If you
also want to use ``uwsgi`` you can edit the relevant section and run the
back-end in production mode by executing ``uwsgi --ini config.ini`` in a
terminal (or by your favorite init system). This generates a ``psef.sock`` file
in the directory you configured as the base directory in ``psef.ini``. This
socket can be used to forward incoming requests in your webserver.