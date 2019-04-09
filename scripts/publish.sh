#!/bin/bash

# Waiting for graphql-server-core to update their package.
if [[ ! -d extern/graphql-server-core ]]; then
    mkdir -p extern
    git clone https://github.com/norman-thomas/graphql-server-core extern/graphql-server-core
fi
cp -r extern/graphql-server-core/graphql_server graphql_server

python setup.py sdist bdist_wheel
twine upload dist/polecat-$1.tar.gz

rm -rf graphql_server
