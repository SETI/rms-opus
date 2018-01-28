# OPUS

OPUS is an outer planets data search tool for the Ring-Moon Systems Node, built with [Python][0] using the [Django Web Framework][1].

## Technology Stack

	Python 2.7
	Django > 1.10
	MySQL 5.6
	Twitter Bootstrap 3
	jQuery 2

## Installation Guide

- We have a [detailed installation guide](install.md) for installing locally

- Our custom import pipeline for the Rings Node is in this [separate repo](https://github.com/basilleaf/opus_admin)

## Project Layout

The client side javascript web application is defined in [static_media/js/](static_media/js/) and [described here](static_media/js/README.md)

The server side python scripts are found in [apps/](apps/) and [described here](apps/README.md)

## Run the Django Tests

	python manage.py test apps


[0]: https://www.python.org/
[1]: https://www.djangoproject.com/
