# Administration of thumbsup servers

This directory contains files that help maintain our Thumbsup production server(s). We are currently
using virtual servers on AWS Lightsail. The deployment is set up following this guide:
[How To Serve Flask Applications with Gunicorn and Nginx on Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04).

There are setup steps that are not covered by these scripts - pushing secrets to the server, nginx
setup, certbot installation, and certbot application to nginx configs.

The scripts in this repository are primarily concerned with keeping the service running once it is
up and with keeping it up-to-date with the code in this repository.
