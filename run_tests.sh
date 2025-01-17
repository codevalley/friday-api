#!/bin/bash

# Set environment variables for testing
export ENV=test
export DATABASE_DIALECT=mysql
export DATABASE_DRIVER=pymysql
export DATABASE_HOSTNAME=localhost
export DATABASE_NAME=test_fridaystore
export DATABASE_PASSWORD=1234567890
export DATABASE_PORT=3306
export DATABASE_USERNAME=root

# Run the tests
pytest "$@" 