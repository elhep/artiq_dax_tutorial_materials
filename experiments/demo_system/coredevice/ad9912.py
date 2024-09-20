from numpy import int64

from artiq.language.core import kernel, portable, delay
from artiq.language.types import TInt32, TInt64, TFloat, TTuple
from artiq.language.units import us, ms

import artiq.coredevice.ad9912
from artiq.coredevice.ad9912 import AD9912_SER_CONF, AD9912_PRODIDH, AD9912_PWRCNTRL1, AD9912_N_DIV, AD9912_PLLCFG


class AD9912(artiq.coredevice.ad9912.AD9912):
    """A backwards compatible extension of the standard AD9912 driver."""

    def __init__(self, dmgr, chip_select, cpld_device, sw_device=None,
                 pll_n=10, pll_en=1):
        self.kernel_invariants = {"cpld", "core", "bus", "chip_select",
                                  "pll_n", "pll_en", "ftw_per_hz"}
        self.cpld = dmgr.get(cpld_device)
        self.core = self.cpld.core
        self.bus = self.cpld.bus
        assert 4 <= chip_select <= 7
        self.chip_select = chip_select
        if sw_device:
            self.sw = dmgr.get(sw_device)
            self.kernel_invariants.add("sw")
        self.pll_n = pll_n
        self.pll_en = pll_en
        clk = self.cpld.refclk / [1, 1, 2, 4][self.cpld.clk_div]
        if pll_en:
            sysclk = clk * pll_n
        else:
            sysclk = clk
        assert sysclk <= 1e9
        self.ftw_per_hz = 1 / sysclk * (int64(1) << 48)

    @kernel
    def init(self):
        """Initialize and configure the DDS.
        Sets up SPI mode, confirms chip presence, powers down unused blocks,
        and configures the PLL. Does not wait for PLL lock. Uses the
        IO_UPDATE signal multiple times.
        """
        # SPI mode
        self.write(AD9912_SER_CONF, 0x99, length=1)
        self.cpld.io_update.pulse(2 * us)
        # Verify chip ID and presence
        prodid = self.read(AD9912_PRODIDH, length=2)
        if (prodid != 0x1982) and (prodid != 0x1902):
            raise ValueError("Urukul AD9912 product id mismatch")
        delay(50 * us)
        # HSTL power down, CMOS power down
        pwr_ctl1 = 0x80
        if not self.pll_en:
            pwr_ctl1 |= 1 << 4  # PLL power down
        self.write(AD9912_PWRCNTRL1, pwr_ctl1, length=1)
        self.cpld.io_update.pulse(2 * us)

        if self.pll_en:
            self.write(AD9912_N_DIV, self.pll_n // 2 - 2, length=1)
            self.cpld.io_update.pulse(2 * us)
            # I_cp = 375 µA, VCO high range
            self.write(AD9912_PLLCFG, 0b00000101, length=1)
            self.cpld.io_update.pulse(2 * us)
        delay(1 * ms)

    @portable(flags={"fast-math"})
    def pow_to_turns(self, pow_: TInt32) -> TFloat:
        """Return the phase in turns corresponding to a given phase offset word.

        :param pow_: Phase offset word.
        :return: Phase in turns.
        """
        return pow_ / (1 << 14)

    @kernel
    def get_mu(self) -> TTuple([TInt64, TInt32]):
        """Get the frequency tuning word and phase offset word.

        .. seealso:: :meth:`get`

        :return: A tuple ``(ftw, pow)``.
        """

        # Read data
        upper = self.read(artiq.coredevice.ad9912.AD9912_POW1, 4)
        self.core.break_realtime()  # Regain slack to perform second read
        lower = self.read(artiq.coredevice.ad9912.AD9912_FTW3, 4)
        # Extract and return fields
        ftw = (int64(upper & 0xffff) << 32) | (int64(lower) & int64(0xffffffff))
        pow_ = (upper >> 16) & 0x3fff
        return ftw, pow_

    @kernel
    def get(self) -> TTuple([TFloat, TFloat]):
        """Get the frequency and phase.

        .. seealso:: :meth:`get_mu`

        :return: A tuple ``(frequency, phase)``.
        """

        # Get values
        ftw, pow_ = self.get_mu()
        # Convert and return
        return self.ftw_to_frequency(ftw), self.pow_to_turns(pow_)

    @kernel
    def get_att_mu(self) -> TInt32:
        """Get digital step attenuator value in machine units.

        .. seealso:: :meth:`artiq.coredevice.urukul.CPLD.get_att_mu_`

        :return: Attenuation setting, 8 bit digital.
        """
        return self.cpld.get_att_mu_(self.chip_select - 4)

    @kernel
    def get_att(self) -> TFloat:
        """Get digital step attenuator value in SI units.

        .. seealso:: :meth:`artiq.coredevice.urukul.CPLD.get_att`

        :return: Attenuation in dB.
        """
        return self.cpld.get_att(self.chip_select - 4)
