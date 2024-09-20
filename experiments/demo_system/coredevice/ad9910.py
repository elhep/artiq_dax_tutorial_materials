from numpy import int32, int64

from artiq.language.core import kernel
from artiq.language.types import TInt32, TFloat, TTuple

import artiq.coredevice.ad9910


class AD9910(artiq.coredevice.ad9910.AD9910):

    @kernel
    def get_mu(self, profile: TInt32 = int32(0)) -> TTuple([TInt32, TInt32, TInt32]):
        """Get the frequency tuning word, phase offset word, and amplitude scale factor.

        .. seealso:: :meth:`get`

        :param profile: Profile number to get (0-7, default: 0)
        :return: A tuple ``(ftw, pow, asf)``
        """

        # Read data
        # noinspection PyProtectedMember
        data = int64(self.read64(artiq.coredevice.ad9910._AD9910_REG_PROFILE0 + profile))
        # Extract and return fields
        ftw = int32(data)
        pow_ = int32((data >> 32) & 0xffff)
        asf = int32((data >> 48) & 0x3fff)
        return ftw, pow_, asf

    @kernel
    def get(self, profile: TInt32 = int32(0)) -> TTuple([TFloat, TFloat, TFloat]):
        """Get the frequency, phase, and amplitude.

        .. seealso:: :meth:`get_mu`

        :param profile: Profile number to get (0-7, default: 0)
        :return: A tuple ``(frequency, phase, amplitude)``
        """

        # Get values
        ftw, pow_, asf = self.get_mu(profile)
        # Convert and return
        return self.ftw_to_frequency(ftw), self.pow_to_turns(pow_), self.asf_to_amplitude(asf)

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
