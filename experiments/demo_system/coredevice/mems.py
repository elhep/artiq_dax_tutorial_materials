"""
Core device driver for the Duke Red Chamber MEMS system using the HV209 and DAC8734 with shared wiring.
"""

import numpy as np

from artiq.language.core import kernel, portable, delay
from artiq.language.types import TFloat, TInt32
from artiq.language.units import *
from artiq.coredevice import spi2 as spi
from artiq.coredevice.ttl import TTLOut


class MemsSystem:
    # Flags to configure the HV209 SPI bus
    _SW_SPI_CONFIG = 0x00

    # Flags to configure the DAC8734 SPI bus
    _DAC_SPI_CONFIG = spi.SPI_CLK_PHASE
    _DAC_SPI_CS = 0b1

    # DAC7834 addresses
    _DAC_DATA_ADDR = [0b0100 << 16, 0b0101 << 16, 0b0110 << 16, 0b0111 << 16]  # 16 bit
    _DAC_ZERO_ADDR = [0b1000 << 16, 0b1001 << 16, 0b1010 << 16, 0b1011 << 16]  # 9 bit
    _DAC_GAIN_ADDR = [0b1100 << 16, 0b1101 << 16, 0b1110 << 16, 0b1111 << 16]  # 8 bit
    _DAC_CMD_ADDR = 0b0000 << 16
    _DAC_MON_ADDR = 0b0001 << 16

    kernel_invariants = {
        '_SW_SPI_CONFIG',
        '_DAC_SPI_CONFIG',
        '_DAC_SPI_CS',
        '_DAC_DATA_ADDR',
        '_DAC_ZERO_ADDR',
        '_DAC_GAIN_ADDR',
        '_DAC_CMD_ADDR',
        '_DAC_MON_ADDR',
        '_v_ref',
        '_gain',
        'core',
        '_sw_spi',
        '_sw_clr',
        '_dac_spi',
        '_dac_rst_n',
        '_ldac_n',
        '_sw_spi_clk_div',
        '_dac_spi_clk_div',
    }

    def __init__(self, device_manager,
                 sw_spi: str, sw_clr: str,
                 dac_spi: str, dac_rst: str,
                 ldac: str, core_device: str = 'core',
                 v_ref: float = 5.0 * V):
        assert isinstance(v_ref, float), 'Reference voltage must be of type float'

        # Store parameters
        self._v_ref: float = v_ref
        self._gain: int = 4
        assert self._v_ref > 0 * V, 'Reference voltage must be larger than zero'
        assert self._gain in {2, 4}, 'Gain value is invalid'

        # Obtain low-level devices
        self.core = device_manager.get(core_device)
        self._sw_spi: spi.SPIMaster = device_manager.get(sw_spi)
        self._sw_clr: TTLOut = device_manager.get(sw_clr)
        self._dac_spi: spi.SPIMaster = device_manager.get(dac_spi)
        self._dac_rst_n: TTLOut = device_manager.get(dac_rst)
        self._ldac_n: TTLOut = device_manager.get(ldac)

        # Calculate constants
        self._sw_spi_clk_div: np.int32 = np.int32(self._sw_spi.frequency_to_div(5 * MHz))
        self._dac_spi_clk_div: np.int32 = np.int32(self._dac_spi.frequency_to_div(30 * MHz))

    """HV209 low_level functions"""

    @kernel
    def sw_write(self, data: TInt32):
        """Write to 6 bit shift register of HV209.

        Bit 0 to 6 represent the state of switch 0 to 6.

        :param data: Right-aligned binary data to write out over SPI
        """
        self._sw_spi.set_config_mu(self._SW_SPI_CONFIG | spi.SPI_END, 6, self._sw_spi_clk_div, 0b1)
        self._sw_spi.write(data << 26)

    @kernel
    def sw_clear(self):
        """Clear the HV209."""
        self._sw_clr.pulse(150 * ns)

    """DAC8734 low-level functions"""

    @kernel
    def dac_write(self, data: TInt32):
        """Write 24 bit into the DAC8734 shift register (8 bit flags, 16 bit data).

        :param data: 8+16 bit right-aligned binary data to write out over SPI
        """
        self._dac_spi.set_config_mu(self._DAC_SPI_CONFIG | spi.SPI_END, 24, self._dac_spi_clk_div, self._DAC_SPI_CS)
        self._dac_spi.write(data << 8)

    @kernel
    def dac_write_data(self, addr: TInt32, fsr: TInt32):
        """Write DAC data register.

        :param addr: DAC output address [0..3]
        :param fsr: Full-scale range (16 bit)
        :raises IndexError: Raised if the address is out of range
        """
        self.dac_write(self._DAC_DATA_ADDR[addr] | (fsr & 0xFFFF))

    @kernel
    def dac_write_zero(self, addr: TInt32, zero: TInt32):
        """Write DAC zero register.

        :param addr: DAC output address [0..3]
        :param zero: Zero offset (9 bit two's complement)
        :raises IndexError: Raised if the address is out of range
        """
        self.dac_write(self._DAC_ZERO_ADDR[addr] | (zero & 0x1FF))

    @kernel
    def dac_write_gain(self, addr: TInt32, gain: TInt32):
        """Write DAC gain register.

        :param addr: DAC output address [0..3]
        :param gain: Gain offset (8 bit two's complement)
        :raises IndexError: Raised if the address is out of range
        """
        self.dac_write(self._DAC_GAIN_ADDR[addr] | (gain & 0xFF))

    @kernel
    def dac_reset(self):
        """Reset the DAC8734."""
        self._dac_rst_n.set_o(not True)
        delay(25 * ns)
        self._dac_rst_n.set_o(not False)

    @portable(flags={'fast-math'})
    def dac_vout_to_fsr(self, v_out: TFloat) -> TInt32:
        """Convert output voltage to full-scale range.

        :param v_out: Output voltage
        :return: Full-scale range value (16 bit)
        """
        fsr = np.int32(round(float(v_out / self._gain / self._v_ref * (1 << 16))))
        if not (-(1 << 15) <= fsr < (1 << 15)):
            raise ValueError('Voltage out of range')
        return fsr

    @portable(flags={'fast-math'})
    def dac_fsr_to_vout(self, fsr: TInt32) -> TFloat:
        """Convert full-scale range to output voltage.

        :param fsr: Full-scale range value (16 bit)
        :return: Output voltage
        """
        if not (-(1 << 15) <= fsr < (1 << 15)):
            raise ValueError('FSR out of range')
        return fsr / (1 << 16) * self._v_ref * self._gain

    """Shared low-level functions"""

    @kernel
    def init(self):
        """Initialize devices.

        Can be called safely at any time, but should be called at least once before operation.
        """
        self._sw_clr.off()
        self._dac_rst_n.set_o(not False)
        self._ldac_n.set_o(not False)

    @kernel
    def write_update(self):
        """Pulse the LDAC signal to transfer configuration data to control registers.

        The LDAC signal is shared between the HV209 and the DAC8734.
        """
        self._ldac_n.set_o(not True)
        delay(150 * ns)
        self._ldac_n.set_o(not False)
