#!/usr/bin/env python

import logging
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help='Add extra output to VM and interpreter', action='store_true')
parser.add_argument('-m', '--max-jobs', help='Maximum number of concurrent jobs', type=int, default=4)
args = parser.parse_args()

fmt = '[{levelname:7s}] {name:s}: {message:s}'
log_file = open('system/execution.log', 'w')

if args.debug:
    logging.basicConfig(stream=log_file, format=fmt, style="{", level=logging.DEBUG)
else:
    logging.basicConfig(stream=log_file, format=fmt, style="{", level=logging.INFO)

from system import Interpreter

interpreter = Interpreter(args)

try:
    interpreter.start()
except (KeyboardInterrupt, EOFError):
    interpreter.end()
    sys.exit()
