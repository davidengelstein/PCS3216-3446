import sys

from system import Interpreter

interpreter = Interpreter()

try:
    interpreter.start()
except (KeyboardInterrupt, EOFError):
    print('bye!')
    sys.exit()
