## Assembler

import logging
import coloredlogs

from ctypes import c_uint8

fmt = '[{levelname:7s}] {name:s}: {message:s}'
logger = logging.getLogger(__name__)
coloredlogs.DEFAULT_FIELD_STYLES['levelname']['color'] = 'white'
coloredlogs.install(level=logging.DEBUG, logger=logger, fmt=fmt, style='{')

class AssemblyError(Exception):
    pass

class Assembler:
    # (Object Code, Size)
    mnemonics_table = {
        "JP": (0x0, 2), "JZ": (0x1, 2), "JN": (0x2, 2), "CN": (0x3, 1),
        "+":  (0x4, 2), "-":  (0x5, 2), "*":  (0x6, 2), "/":  (0x7, 2),
        "LD": (0x8, 2), "MM": (0x9, 2), "SC": (0xA, 2), "OS": (0xB, 1),
        "IO": (0xC, 1),
    }

    pseudo_table = ['@', '#', '$', 'K']

    def __init__(self, filen=None, make_list=True, dump_tables=True):
        if not filen:
            raise RuntimeError('File name not provided to Assembler')

        logger.debug('Initializing Assembler')

        # Removes file extension
        self.filename = '.'.join(filen.split('.')[:-1])
        logger.debug('Base filename: %s', self.filename)

        self.labels = {}
        self.obj_code = []
        self.instruction_counter = 0
        self.initial_address = 0

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
                print('{}-----------'.format('-' * len(self.list_file)), file=f)
                print('ADDRESS   OBJECT    LINE   SOURCE', file=f)

        self.lb_table_file = None
        if (dump_tables):
            self.lb_table_file = self.filename + '.asm.labels'

            with open(self.lb_table_file, 'w') as f:
                print('{} LABEL TABLE FILE'.format(self.lb_table_file), file=f)
                print('{}-----------------'.format('-' * len(self.lb_table_file)), file=f)
                print('LABEL           VALUE', file=f)

        self.obj_file = self.filename + '.obj'

    def assemble(self):
        for self.step in [1, 2]:
            logger.debug('Initializing Step %d', self.step)

            self.instruction_counter = 0
            for lineno, code, comment in self.lines:
                # logger.debug('Processing line %d', lineno)

                if len(code) == 0: # Comment only, do nothing on first step
                    if self.step == 2:
                        self.list(line=lineno, comment=comment)

                elif len(code) == 1: # Label only
                    if self.step == 2:
                        self.list(line=lineno, comment=comment, code=code, address=self.instruction_counter)
                        continue

                    label = code[0]
                    if label in [*self.mnemonics_table, *self.pseudo_table]: # Lonely operation
                        raise AssemblyError('Assembly error on line {:d} "{}": operation must have operator'.format(lineno, ' '.join(code)))

                    if label in self.labels and self.labels[label] is not None: # Label already defined
                        raise AssemblyError('Assembly error on line {:d} label "{}" already defined'.format(lineno, label))

                    self.labels[label] = self.instruction_counter

                elif len(code) == 2: # Operation and Operator
                    self.process_code(lineno, code, comment)

                elif len(code) == 3: # Label, Operation and Operator
                    if self.step == 1:
                        label = code[0]
                        if   label in [*self.mnemonics_table, *self.pseudo_table]: # First element should be label
                            raise AssemblyError('Assembly error on line {:d} "{}": operation on label position'.format(lineno, ' '.join(code)))

                        if label in self.labels and self.labels[label] is not None: # Label already defined
                            raise AssemblyError('Assembly error on line {:d} label "{}" already defined'.format(lineno, label))

                        self.labels[label] = self.instruction_counter

                    self.process_code(lineno, code, comment)

                else:
                    raise AssemblyError('Assembly error on line {:d}: Too many things!!'.format(lineno))

            logger.debug('Finished Step %d', self.step)
            self.dump_label_table()
            self.save_obj()


    def process_code(self, lineno, code, comment):
        operation = code[-2]
        if operation not in [*self.mnemonics_table, *self.pseudo_table]: # Unknown operation
            raise AssemblyError('Assembly error on line {:d}: Unknown operation "{}"'.format(lineno, operation))

        try:
            operator = int(code[-1]) # try decimal
        except ValueError:
            try:
                if code[-1][0] == '/':
                    operator = int(code[-1][1:], 16) # try hex
                else:
                    raise
            except ValueError: # label
                if self.step == 1:
                    if code[-1] not in self.labels:
                        self.labels[code[-1]] = None
                    operator = None
                elif self.step == 2:
                    if self.labels[code[-1]] is None:
                        raise AssemblyError('Assembly error on line {:d}: undefined label "{}"'.format(lineno, code[-1]))
                    operator = self.labels[code[-1]]

        # Pseudo instruction
        if operation in self.pseudo_table:
            if operation != '#' and type(operator) != type(int()):
                raise AssemblyError('Assembly error on line {:d}: {} operator must be an integer!'.format(lineno, operation))

            if operation == '@':
                if operator > 0xFFFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.list(line=lineno, code=code, comment=comment)
                self.instruction_counter = operator
            elif operation == '$':
                if operator > 0xFFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.list(line=lineno, code=code, comment=comment, address=self.instruction_counter)
                self.instruction_counter += operator
                if self.step == 2:
                    self.obj_code.extend([c_uint8(0)] * operator)

            elif operation == 'K':
                if operator > 0xFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.list(line=lineno, code=code, comment=comment, address=self.instruction_counter, object=operator)
                if self.step == 2:
                    self.obj_code.append(c_uint8(operator))
                self.instruction_counter += 1
            elif self.step == 2 and operation == '#':
                if operator > 0xFFFF:
                    raise AssemblyError('Assembly error on line {:d}: operator out of range "{:0x}"'.format(lineno, operator))
                self.list(line=lineno, code=code, comment=comment)
                self.initial_address = operator

        # Normal instruction
        else:
            instruction_size = self.mnemonics_table[operation][1]
            if self.step == 1:
                self.instruction_counter += instruction_size
                return

            if instruction_size == 1:
                obj_code = self.mnemonics_table[operation][0] << 4 | operator
                self.obj_code.append(c_uint8(obj_code))
            elif instruction_size == 2:
                obj_code = self.mnemonics_table[operation][0] << 12 | operator
                self.obj_code.append(c_uint8(obj_code >> 8))
                self.obj_code.append(c_uint8(obj_code & 0xFF))

            self.list(line=lineno, code=code, comment=comment, address=self.instruction_counter, object=obj_code)
            self.instruction_counter += instruction_size

    def list(self, **kwargs):
        if self.list_file is None or self.step != 2:
            return

        comm = '; {:s}'.format(kwargs['comment']) if 'comment' in kwargs and kwargs['comment'] != '' else ''
        addr = '{:-04X}'.format(kwargs['address']) if 'address' in kwargs else '    '
        obj = '{:-6X}'.format(kwargs['object']) if 'object' in kwargs else '      '
        code = '{:s} '.format(' '.join(kwargs['code'])) if 'code' in kwargs else ''
        line = '{:-4d}'.format(kwargs['line']) if 'line' in kwargs else '    '

        with open(self.list_file, 'a') as f:
            print('   {}   {}    {}   {}{}'.format(
                addr, obj, line, code, comm), file=f)

    def dump_label_table(self):
        if self.lb_table_file is None or self.step != 1:
            return

        with open(self.lb_table_file, 'a') as f:
            for label in self.labels:
                print('{:<15s}  {:>04X}'.format(label, self.labels[label]), file=f)

    def save_obj(self):
        if self.step != 2:
            return

        chk = c_uint8(0xFF)
        with open(self.obj_file, 'w') as f:
            print('{:02X} {:02X}'.format(self.initial_address >> 8, self.initial_address & 0xFF), end=' ', file=f)
            print('{:02X}'.format(len(self.obj_code)), end=' ', file=f)
            i = 3
            for obj in self.obj_code:
                print('{:02X}'.format(obj.value), end=' ', file=f)
                chk.value ^= obj.value
                i += 1
                if i % 16 == 0:
                    print('', file=f)
            print('{:02X}'.format(chk.value), end='', file=f)
