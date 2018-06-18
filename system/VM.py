import logging
import coloredlogs

from ctypes import c_uint8, c_uint16, c_int16

fmt = '[{levelname:7s}] {name:s}: {message:s}'
logger = logging.getLogger(__name__)
coloredlogs.DEFAULT_FIELD_STYLES['levelname']['color'] = 'white'
coloredlogs.install(level=logging.DEBUG, logger=logger, fmt=fmt, style='{')

class VMError(Exception):
    pass

class VM:
    instructions_sizes = {
        0x0: 2, 0x1: 2, 0x2: 2, 0x3: 1,
        0x4: 2, 0x5: 2, 0x6: 2, 0x7: 2,
        0x8: 2, 0x9: 2, 0xA: 2, 0xB: 1,
        0xC: 1,
    }

    def __init__(self, banks=16, bank_size=4096):
        logger.debug("Initializing VM")
        logger.debug("Memory banks: %d", banks)
        logger.debug("Bank size: %d bytes", bank_size)

        self.instruction_decoders = {
            0x0: self._jump,
            0x1: self._jump_if_zero,
            0x2: self._jump_if_negative,
            0x3: self._control,
            0x4: self._sum,
            0x5: self._subtract,
            0x6: self._multiply,
            0x7: self._divide,
            0x8: self._load,
            0x9: self._store,
            0xA: self._subroutine_call,
            0xB: self._os_call,
            0xC: self._io,
            0xD: self._reserved,
            0xE: self._reserved,
            0xF: self._reserved
        }

        self.main_memory = [[c_uint8(0) for i in range(bank_size)] for j in range(banks)] # 16 banks of 4096 bytes
        self._ci = c_uint16(0)
        self._pc = c_uint16(0)
        self._acc = c_int16(0)

        self._cb = c_uint8(0)
        self.indirect_mode = False

    @property
    def current_instruction(self):
        return self._ci.value

    @current_instruction.setter
    def current_instruction(self, value):
        self._ci.value = value

    @property
    def instruction_counter(self):
        return self._pc.value

    @instruction_counter.setter
    def instruction_counter(self, value):
        self._pc.value = value

    @property
    def accumulator(self):
        return self._acc.value

    @accumulator.setter
    def accumulator(self, value):
        self._acc.value = value

    @property
    def current_bank(self):
        return self._cb.value

    @current_bank.setter
    def current_bank(self, value):
        self._cb.value = value

    def teste(self, file):
        self.fetch()
        self.decode_execute()

    def fetch(self):
        logger.debug('Fetching Instruction')
        logger.debug('Bank %d - PC: %X', self.current_bank, self.instruction_counter)
        instruction_type = self.main_memory[self.current_bank][self.instruction_counter].value >> 4
        instruction_size = self.instructions_sizes[instruction_type]

        logger.debug('Instruction type 0x%X - %d byte(s)', instruction_type, instruction_size)

        if instruction_size == 1:
            # Most significant byte
            self.current_instruction = self.main_memory[self.current_bank][self.instruction_counter].value << 8
        elif instruction_size == 2:
            self.current_instruction = (self.main_memory[self.current_bank][self.instruction_counter].value << 8) | \
                self.main_memory[self.current_bank][self.instruction_counter + 1].value

        logger.debug('Complete instruction: 0x%04X', self.current_instruction)

        self.instruction_counter += instruction_size

    def decode_execute(self):
        logger.debug('Decoding and Executing Instruction')
        instruction_type = self.current_instruction >> 12 # First nibble

        if instruction_type not in self.instruction_decoders:
            raise VMError('Bad instruction at address 0x{:01X}{:03X}'.format(self.current_bank, self.instruction_counter))

        self.instruction_decoders[instruction_type]()

    def _jump(self):
        operand = self.current_instruction & 0xFFF
        self.instruction_counter = operand

    def _jump_if_zero(self):
        if self.accumulator != 0:
            return

        operand = self.current_instruction & 0xFFF
        self.instruction_counter = operand

    def _jump_if_negative(self):
        if self.accumulator < 0:
            return

        operand = self.current_instruction & 0xFFF
        self.instruction_counter = operand

    def _control(self):
        pass

    def _sum(self):
        operand = self.current_instruction & 0xFFF
        self.accumulator += operand

    def _subtract(self):
        operand = self.current_instruction & 0xFFF
        self.accumulator -= operand

    def _multiply(self):
        operand = self.current_instruction & 0xFFF
        self.accumulator *= operand

    def _divide(self):
        operand = self.current_instruction & 0xFFF
        self.accumulator /= operand

    def _load(self):
        operand = self.current_instruction & 0xFFF
        self.accumulator = self.main_memory[self.current_bank][operand]

    def _store(self):
        operand = self.current_instruction & 0xFFF
        self.main_memory[self.current_bank][operand] = self.accumulator

    def _subroutine_call(self):
        pass

    def _os_call(self):
        pass

    def _io(self):
        operand = self.current_instruction &0x0F00 >> 8 # last nibble
        op_type = operand >> 2
        device = operand & 0x3

        if op_type == 0b00: # Get data
            pass
        elif op_type == 0b01: # Put data
            pass
        elif op_type == 0b10: # Enable Interrupt
            pass
        elif op_type == 0b11: # Disable Interrupt
            pass

    def _reserved(self):
        logger.warning('Tried to execute reserved instruction')
        logger.warning('This is probably not intendend and might mess the memory')
        logger.warning('Press enter to continue and skip byte (Ctrl+C to exit)')
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            raise VMError('Aborted after reserved instruction')
