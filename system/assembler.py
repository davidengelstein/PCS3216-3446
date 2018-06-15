## Assembler

import logging

from ctypes import c_uint8

fmt = '[%(levelname)-7s] %(name)s: %(message)s'
logging.basicConfig(format=fmt)

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

class AssemblyError(Exception):
    pass

class Assembler:
    # (Code, Size)
    mnemonics_table = {
        "JP": (0x0, 2),
        "JZ": (0x1, 2),
        "JN": (0x2, 2),
        "CN": (0x3, 1),
        "+":  (0x4, 2),
        "-":  (0x5, 2),
        "*":  (0x6, 2),
        "/":  (0x7, 2),
        "LD": (0x8, 2),
        "MM": (0x9, 2),
        "SC": (0xA, 2),
        "OS": (0xB, 1),
        "IO": (0xC, 1),
    }

    pseudo_table = ['@', '#', '$', 'K']

    # line_pattern = r'^(?P<label>\w*)?(?:\s*(?P<instr>JP|JZ|JN|CN|\+|\-|\*|\/|LD|MM|SC|OS|IO|@|#|\$|K?)\s+(?P<op>\/[0-9|A-F]{1,4})\s*$|$)'

    def __init__(self, filen=None, make_list=True):
        if not filen:
            raise RuntimeError('File name not provided to Assembler')

        logger.debug('Initializing Assembler')

        # Removes file extension
        self.filename = '.'.join(filen.split('.')[:-1])
        logger.debug('Base filename: %s', self.filename)

        self.labels = {}
        self.instruction_counter = 0

        try:
            with open(filen, 'r') as f:
                all_lines = f.readlines()
        except FileNotFoundError:
            logger.error('File %s not found', filen)
            raise AssemblyError('File not found')

        logger.debug('Preprocessing file')
        self.lines = []
        for i, line in enumerate(all_lines):
            # Separate comments
            command, comment = (l.strip() for l in line.split(';')) if ';' in line else (line.strip(), '')
            if command == '' and comment == '': # skip blank lines
                continue

            l = command.split()
            self.lines.append((i+1, l, comment))
        logger.debug('Finished preprocessing')

        self.list_file = None
        if (make_list):
            self.list_file = self.filename + '.lst'

            with open(self.list_file, 'w') as f:
                print('{} LIST FILE'.format(self.list_file), file=f)
                print('ADDRESS   OBJECT    LINE   SOURCE', file=f)

    def assemble(self):
        # out_file = open(self.filename + '.hex', 'w')

        logger.debug('Initializing First Step')
        # First Step
        self.step = 1
        for lineno, code, comment in self.lines:
            logger.debug('Processing line %d', lineno)

            if len(code) == 0: # Comment only, do nothing on first step
                continue

            if len(code) == 1: # Label only
                label = code[0]
                if label in [*self.mnemonics_table, *self.pseudo_table]: # Lonely operation
                    raise AssemblyError('Assembly error on line {:d} "{}": operation must have operator'.format(lineno, ' '.join(code)))

                if label in self.labels and self.labels[label] is not None: # Label already defined
                    raise AssemblyError('Assembly error on line {:d} label "{}" already defined'.format(lineno, label))

                self.labels[label] = self.instruction_counter

            elif len(code) == 2: # Operation and Operator
                self.process_code(lineno, code)

            elif len(code) == 3: # Label, Operation and Operator
                label = code[0]
                if label in [*self.mnemonics_table, *self.pseudo_table]: # First element should be label
                    raise AssemblyError('Assembly error on line {:d} "{}": operation on label position'.format(lineno, ' '.join(code)))

                if label in self.labels and self.labels[label] is not None: # Label already defined
                    raise AssemblyError('Assembly error on line {:d} label "{}" already defined'.format(lineno, label))

                self.labels[label] = self.instruction_counter
                self.process_code(lineno, code[1:])

            else:
                raise AssemblyError('Assembly error on line {:d}: Too many things!!'.format(lineno))

        logger.debug('Finished First Step')

        logger.debug('Initializing Second Step')
        # Second Step
        self.step = 2
        for lineno, code, comment in self.lines:
            logger.debug('Processing line %d', lineno)

            if len(code) == 0: # Comment only, list
                self.list(line=lineno, comment=comment)

            elif len(code) == 1: # Label only, list
                self.list(line=lineno, address=self.instruction_counter, code=code, comment=comment)

            elif len(code) <= 3: # [label] Operation and Operator
                obj_code = self.process_code(lineno, code)
                if obj_code is None:
                    self.list(line=lineno, address=self.instruction_counter, code=code, comment=comment)
                else:
                    self.list(line=lineno, object=obj_code, address=self.instruction_counter, code=code, comment=comment)

            elif len(code) == 3: # Label, Operation and Operator
                obj_code = self.process_code(lineno, code[1:])
                if obj_code is None:
                    self.list(line=lineno, address=self.instruction_counter, code=code, comment=comment)
                else:
                    self.list(line=lineno, object=obj_code, address=self.instruction_counter, code=code, comment=comment)

            else:
                raise AssemblyError('Assembly error on line {:d}: Too many things!!'.format(lineno))


    def process_code(self, lineno, code):
        operation = code[0]
        if operation not in [*self.mnemonics_table, *self.pseudo_table]: # Unknown operation
            raise AssemblyError('Assembly error on line {:d}: Unknown operation "{}"'.format(lineno, operation))

        if '/' not in code[1]: # Label
            if self.step == 1:
                if code[1] not in self.labels:
                    self.labels[code[1]] = None
                operator = code[1]
            elif self.step == 2:
                if code[1] not in self.labels:
                    raise AssemblyError('Assembly error on line {:d}: undefined label "{}"'.format(lineno, code[1]))
                operator = self.labels[code[1]]
        else:
            try:
                operator = int(code[1][1:], 16)
                if operator > 0xFFFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
            except ValueError:
                raise AssemblyError('Assembly error on line {:d}: invalid operator "{}"'.format(lineno, code[1]))

        # Pseudo instruction
        if operation in self.pseudo_table:
            if operation != '#' and type(operator) != type(int()):
                raise AssemblyError('Assembly error on line {:d}: {} operator must be an integer!'.format(lineno, operation))

            if operation == '@':
                self.instruction_counter = operator
            elif operation == '$':
                if operator > 0xFFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.instruction_counter += operator
            elif operation == 'K':
                if operator > 0xFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.instruction_counter += 1
                return operator

        # Normal instruction
        else:
            self.instruction_counter += self.mnemonics_table[operation][1]
            if self.step == 1:
                return

            obj_code = self.mnemonics_table[operation][0] << 12 | operator
            return obj_code


    def list(self, **kwargs):
        if self.list_file is None:
            return

        comm = '; {:s}'.format(kwargs['comment']) if 'comment' in kwargs and kwargs['comment'] != '' else ''
        addr = '{:-04X}'.format(kwargs['address']) if 'address' in kwargs else '    '
        obj = '{:-6X}'.format(kwargs['object']) if 'object' in kwargs else '      '
        code = '{:s}'.format(' '.join(kwargs['code'])) if 'code' in kwargs else ''
        line = '{:-4d}'.format(kwargs['line']) if 'line' in kwargs else '    '

        with open(self.list_file, 'a') as f:
            print('   {}   {}    {}   {} {}'.format(
                addr, obj, line, code, comm), file=f)
