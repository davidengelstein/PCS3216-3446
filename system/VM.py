import logging
import coloredlogs

from ctypes import c_uint8

fmt = '[{levelname:7s}] {name:s}: {message:s}'
logger = logging.getLogger(__name__)
coloredlogs.DEFAULT_FIELD_STYLES['levelname']['color'] = 'white'
coloredlogs.install(level=logging.DEBUG, logger=logger, fmt=fmt, style='{')

class VM:
    def __init__(self, banks=0xF, bank_size=0xFFF):
        logger.debug("Initializing VM")
        logger.debug("Memory banks: %d", banks)
        logger.debug("Bank size: %d", bank_size)

        self.main_memory = [[c_uint8(0)] * bank_size] * banks # F banks of FFF bytes
        self.instruction_counter = 0
        self.accumulator = 0
