#!/bin/bash
JWT_SECRET=test DATABASE_URL=postgres://postgres@localhost/postgres PYTHONPATH=`pwd` pytest "$@"
# JWT_SECRET=test DATABASE_URL=postgres://postgres@localhost/postgres PYTHONPATH=`pwd` pytest --cov=polecat "$@"
