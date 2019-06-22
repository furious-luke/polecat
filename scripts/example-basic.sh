#!/bin/bash
PYTHONPATH=`pwd` POLECAT_PROJECT_MODULE=examples.basic.project.BasicProject python polecat/cli/entrypoint.py server "$@"
