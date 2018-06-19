import sys

from system import Interpreter

interpreter = Interpreter()

try:
    interpreter.start()
except (KeyboardInterrupt, EOFError):
    interpreter.end()
    sys.exit()
