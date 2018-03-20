# OPUS

OPUS is the Outer Planets Unified Search tool for the Ring-Moon Systems Node of NASA's Planetary Data System. It is built with [Python][0] and [JavaScript][1] using the [Django Web Framework][2].

[0]: https://www.python.org/
[1]: https://developer.mozilla.org/en-US/docs/Web/JavaScript
[2]: https://www.djangoproject.com/

## Technology Stack

	Python 2.7
	Django > 1.10
	MySQL 5.6
	Twitter Bootstrap 3
	jQuery 2

## Installation Guide

For installing locally see the [detailed installation guide](install.md)

The Ring-Moon Systems Node custom data import pipeline is in [a separate repo](https://github.com/SETI/pds-opus-admin)

## Project Layout

The client side JavaScript web application is defined in [static_media/js](static_media/js/) and [described here](static_media/js/README.md)

The server side Python scripts are found in [apps](apps/) and [described here](apps/README.md)

## Deployment

For deploying code updates to a remote webserver [see deploy/README.md](deploy/README.md)

## Running the Django Tests

	python manage.py test apps
