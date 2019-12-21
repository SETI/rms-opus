#!/bin/sh
# Usage: add_release_test.sh tagname "Annotated message"
git tag -a $1 -m "$2"
git push origin $1
