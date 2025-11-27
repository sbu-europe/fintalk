#!/bin/bash
# Script to populate the database with dummy users

echo "Populating database with dummy users..."
docker exec fintalk-django python manage.py populate_dummy_users

echo "Done!"
