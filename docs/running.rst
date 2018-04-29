Running CodeGra.de
==========================

This document describes the process of running CodeGra.de. CodeGra.de consists of two
elements, its front-end and its backend. The front-end is build using `Vue.js <https://github.com/vuejs/vue>`_ and
the back-end makes use of the `Flask <https://github.com/pallets/flask>`_  framework. This means that the two components have their
own build and deploy steps for running in the development and production mode.

Please conduct the instructions on `building <building.html>`_ CodeGra.de before attempting the steps below.

Development Mode
------------------

Starting the dev server is quite easy. As the project consists of two parts,
those two parts should both be running. This can be achieved by running ``make
start_dev_npm`` in a terminal, this starts the front-end. To start the backend
we first need to run ``make start_dev_celery`` in a terminal and then run ``make
start_dev_server`` in another terminal.

The development mode of CodeGra.de should now be successfully running!

Production Mode
-------------------

Running CodeGra.de in production mode is a bit more complicated. The first step
is starting celery. Running celery is done by executing ``celery multi start
psef_celery_worker1 --app=runcelery:celery`` in the *virtualenv*. Stopping celery
is done by running ``celery multi stopwait
psef_celery_worker1 --app=runcelery:celery`` in the same *virtualenv*. It is
important that you restart celery every time you restart the back-end. You can
configure celery further, see ``celery worker --help`` for more information.

The second step is building the front-end code. This is done using ``make
build_front-end``, this builds these files to the ``dist`` folder. This folder
should be served by a webserver. This is the only folder that should be server
by the webserver, however all requests starting with ``/api/`` should be
forwarded to our back-end.

To do this we should first start the back-end in production mode. In the
example ini file (``config.ini.example``) we use ``uwsgi`` to do this. If you
also want to use ``uwsgi`` you can edit the relevant section and run the
back-end in production mode by executing ``uwsgi --ini config.ini`` in a
terminal (or by your favourite init system). This generates a ``psef.sock`` file
in the directory you configured as the base directory in ``psef.ini``. This
socket can be used to forward incoming requests in your web-server.
