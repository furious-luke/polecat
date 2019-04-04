#!/bin/bash
PYTHONPATH=`pwd` POLECAT_PROJECT=examples.basic.project.BasicProject python polecat/cli/entrypoint.py server "$@"
