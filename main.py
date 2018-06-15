import sys

from system import Interpreter

interpreter = Interpreter()

try:
    interpreter.start()
except KeyboardInterrupt:
    print('bye!')
    sys.exit()
