from artiq.coredevice.urukul import *
from artiq.language.core import kernel, portable
from artiq.language.types import TInt32, TFloat

import artiq.coredevice.urukul


class CPLD(artiq.coredevice.urukul.CPLD):

    @portable(flags={"fast-math"})
    def mu_to_att(self, att_mu: TInt32) -> TFloat:
        """Convert a digital attenuation setting to dB.

        :param att_mu: Digital attenuation setting.
        :return: Attenuation setting in dB.
        """
        return (255 - (att_mu & 0xff)) / 8

    @portable(flags={"fast-math"})
    def att_to_mu(self, att: TFloat) -> TInt32:
        """Convert an attenuation setting in dB to machine units.

        :param att: Attenuation setting in dB.
        :return: Digital attenuation setting.
        """
        code = int32(255) - int32(round(att * 8))
        if code < 0 or code > 255:
            raise ValueError("Invalid urukul.CPLD attenuation!")
        return code

    @kernel
    def get_att_mu_(self, channel: TInt32) -> TInt32:
        """Get digital step attenuator value for a channel in machine units.

        This method relies on the stored attenuator settings. Use
        :meth:`get_att_mu` to retrieve the hardware state set in previous experiments.

        .. seealso:: :meth:`get_att_mu`

        :param channel: Attenuator channel (0-3).
        :return: 8-bit digital attenuation setting:
            255 minimum attenuation, 0 maximum attenuation (31.5 dB)
        """
        return int32((self.att_reg >> (channel * 8)) & 0xff)

    @kernel
    def get_att(self, channel: TInt32) -> TFloat:
        """Get digital step attenuator value for a channel in SI units.

        .. seealso:: :meth:`get_att_mu_`

        :param channel: Attenuator channel (0-3).
        :return: Attenuation setting in dB. Higher value is more
            attenuation. Minimum attenuation is 0*dB, maximum attenuation is
            31.5*dB.
        """
        return self.mu_to_att(self.get_att_mu_(channel))

    """Other updates"""

    @kernel
    def set_att(self, channel, att):
        """Set digital step attenuator in SI units.

        This method will write the attenuator settings of all four channels.

        .. seealso:: :meth:`set_att_mu`

        :param channel: Attenuator channel (0-3).
        :param att: Attenuation setting in dB. Higher value is more
            attenuation. Minimum attenuation is 0*dB, maximum attenuation is
            31.5*dB.
        """
        self.set_att_mu(channel, self.att_to_mu(att))

    @kernel
    def get_att_mu(self):
        """Return the digital step attenuator settings in machine units.

        The result is stored and will be used in future calls of
        :meth:`set_att_mu` and :meth:`get_att_mu_`.

        .. seealso:: :meth:`get_att_mu_`

        :return: 32 bit attenuator settings
        """
        self.bus.set_config_mu(SPI_CONFIG | spi.SPI_INPUT, 32,
                               SPIT_ATT_RD, CS_ATT)
        self.bus.write(0)  # shift in zeros, shift out current value
        self.bus.set_config_mu(SPI_CONFIG | spi.SPI_END, 32,
                               SPIT_ATT_WR, CS_ATT)
        delay(10 * us)
        self.att_reg = self.bus.read()
        self.bus.write(self.att_reg)  # shift in current value again and latch
        return self.att_reg
