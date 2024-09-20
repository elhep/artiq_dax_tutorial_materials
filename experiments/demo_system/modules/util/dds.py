import numpy as np
import abc

import artiq.coredevice.ad9910
import artiq.coredevice.ad9912

from dax.experiment import *
from dax.util.units import time_to_str


class DDSBase(DaxModule, abc.ABC):
    CONFIG_LATENCY_MU_KEY = "dds_latency_mu"
    SW_LATENCY_MU_KEY = "sw_latency_mu"
    ATT_LATENCY_MU_KEY = "att_latency_mu"

    FREQ_KEY = "freq"
    PHASE_KEY = "phase"
    ATT_KEY = "att"
    SW_KEY = "sw"
    MIN_ATT_KEY = "min_att"

    # noinspection PyMethodOverriding
    def build(
        self,
        *,
        dds_key: str,
        default_freq: float = 100 * MHz,
        default_phase: float = 0.0,
        default_att: float = 31.5 * dB,
        default_sw: bool = False,
        min_att: float = 25 * dB,
        **kwargs
    ) -> None:
        # Defaults check
        assert isinstance(default_freq, float), "Frequency must be of type float"
        assert isinstance(default_phase, float), "Phase must be of type float"
        assert isinstance(default_att, float), "Attenuation must be of type float"
        assert isinstance(min_att, float), "Min Attenuation must be of type float"
        assert isinstance(default_sw, bool), "Sw must be of type bool"
        assert 0.0 <= default_freq <= 400 * MHz, "Frequency out of range"
        assert 0.0 <= default_phase <= 1.0, "Phase out of range"
        assert min_att <= default_att <= 31.5 * dB, "DDS attenuation out of range"
        assert 0.0 <= min_att <= 31.5 * dB, "DDS min attenuation out of range"

        # Uncommenting this line can be helpful to allow self._dds to be seen by the linter
        # self._dds = self.get_device(dds_key, artiq.coredevice.ad9912.AD9912)

        # Store default values
        self._default_freq = default_freq
        self._default_phase = default_phase
        self._default_att = default_att
        self._default_sw = default_sw
        self._min_att = min_att

    @kernel
    def init_kernel(self, debug: TBool = False):
        """Reset DDS Configuration
        :param debug: `True` to not reset the switch state"""
        # Reset DDS Configuration
        self.core.reset()
        self._dds.init()
        self.core.break_realtime()
        self.reset_config()
        self.core.break_realtime()
        self.reset_att()
        if not debug:
            self.core.break_realtime()
            self.reset_sw()

        self.core.wait_until_mu(now_mu())

    @host_only
    def post_init(self) -> None:
        pass

    """DDS Operations"""

    @abc.abstractmethod
    def config():
        pass

    @abc.abstractmethod
    def reset_config():
        pass

    @kernel
    def config_att(self, att: TFloat, realtime: TBool = False):
        """Configure the attenuation.

        :param att: Attenuation in dB
        :param realtime: :const:`True` to compensate for programming latencies
        """
        if realtime:
            # Compensate for latency
            delay_mu(-self._att_latency_mu)
        else:
            # Add some slack
            delay(200 * us)

        if att >= self._min_att:
            # Configure att
            self._dds.set_att(att)
        else:
            self.logger.error("Attenuation Set Out of Range")

    @kernel
    def reset_att(self, realtime: TBool = False):
        """Reset DDS attenuation to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_att(self._default_att, realtime=realtime)

    @kernel
    def safety_off(self):
        """Turn off DDS Safely"""
        self.core.break_realtime()
        self.set(state=False)
        self.core.wait_until_mu(now_mu())

    @kernel
    def set(self, state: TBool, realtime: TBool = False):
        """Set DDS output state
        :param state: :const: `True` to enable DDS
        :param realtime: :const:`True` to compensate for programming latencies
        """
        if realtime:
            # Compensate for latency
            delay_mu(-self._sw_latency_mu)

        # Set output Sw
        self._dds.sw.set_o(state)

        if realtime:
            # Compensate for latency, switch set does not increment cursor
            delay_mu(self._sw_latency_mu)

    @kernel
    def reset_sw(self, realtime: TBool = False):
        """Reset DDS state to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.set(state=self._default_sw, realtime=realtime)

    @kernel
    def reset(self, realtime: TBool = False):
        """Reset all DDS properties
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.reset_sw(realtime=realtime)
        self.reset_config(realtime=realtime)
        self.reset_att(realtime=realtime)

    """Latency Compensations"""

    @host_only
    def update_config_latency(self) -> None:
        """Update the latency."""
        # Reset the latency to zero
        self._config_latency_mu = np.int32(0)
        # Obtain current latency
        self._config_latency_mu = self.get_config_latency_mu()
        # Store latency
        self.logger.info(
            f"Obtained latency: {self._config_latency_mu} machine units "
            f"({time_to_str(self.core.mu_to_seconds(self._config_latency_mu))})"
        )
        self.set_dataset_sys(self.CONFIG_LATENCY_MU_KEY, self._config_latency_mu)

    @kernel
    def get_config_latency_mu(self) -> TInt32:
        # Reset core
        self.core.reset()

        # Reset the system
        self.reset_config()
        # Reset in real-time and capture start and end time
        delay(1 * ms)
        t_start_mu = now_mu()
        self.reset_config(realtime=True)
        t_end_mu = now_mu()
        self.core.wait_until_mu(t_end_mu)

        # Calculate and return latency
        return t_end_mu - t_start_mu

    @host_only
    def clear_config_latency(self):
        self._config_latency_mu = 0.0
        self.set_dataset_sys(self.CONFIG_LATENCY_MU_KEY, self._config_latency_mu)

    @host_only
    def update_att_latency(self) -> None:
        """Update the latency.
        :param test_cb: The method to test
        :param reset_cb: The method to begin and return to
        """
        # Reset the latency to zero
        self._att_latency_mu = np.int32(0)
        # Obtain current latency
        self._att_latency_mu = self.get_att_latency_mu()
        # Store latency
        self.logger.info(
            f"Obtained latency: {self._att_latency_mu} machine units "
            f"({time_to_str(self.core.mu_to_seconds(self._att_latency_mu))})"
        )
        self.set_dataset_sys(self.ATT_LATENCY_MU_KEY, self._att_latency_mu)

    @kernel
    def get_att_latency_mu(self) -> TInt32:
        # Reset core
        self.core.reset()

        # Reset the system
        self.reset_att()
        # Reset in real-time and capture start and end time
        delay(1 * ms)
        t_start_mu = now_mu()
        self.reset_att(realtime=True)
        t_end_mu = now_mu()
        self.core.wait_until_mu(t_end_mu)

        # Calculate and return latency
        return t_end_mu - t_start_mu

    @host_only
    def clear_att_latency(self):
        self._att_latency_mu = 0.0
        self.set_dataset_sys(self.ATT_LATENCY_MU_KEY, self._att_latency_mu)

    @host_only
    def set_sw_latency(self, latency: TInt32) -> None:
        self._sw_latency_mu = latency

    @host_only
    def store_sw_latency(self, latency: TInt32):
        self.set_dataset_sys(self.SW_LATENCY_MU_KEY, latency)

    @host_only
    def update_latency(self):
        self.update_sw_latency()
        self.update_att_latency()
        self.update_config_latency()

    @host_only
    def clear_latency(self):
        self.clear_sw_latency()
        self.clear_att_latency()
        self.clear_config_latency()


class DDS9912(DDSBase):

    def build(
        self,
        *,
        dds_key: str,
        default_freq: float = 100 * MHz,
        default_phase: float = 0.0,
        default_att: float = 31.5 * dB,
        default_sw: bool = False,
        min_att: float = 25 * dB,
        **kwargs
    ) -> None:
        # Defaults check
        assert isinstance(default_freq, float), "Frequency must be of type float"
        assert isinstance(default_phase, float), "Phase must be of type float"
        assert isinstance(default_att, float), "Attenuation must be of type float"
        assert isinstance(min_att, float), "Min Attenuation must be of type float"
        assert isinstance(default_sw, bool), "Sw must be of type bool"
        assert 0.0 <= default_freq <= 400 * MHz, "Frequency out of range"
        assert 0.0 <= default_phase <= 1.0, "Phase out of range"
        assert min_att <= default_att <= 31.5 * dB, "DDS attenuation out of range"
        assert 0.0 <= min_att <= 31.5 * dB, "DDS min attenuation out of range"

        # Get devices
        self._dds = self.get_device(dds_key, artiq.coredevice.ad9912.AD9912)
        self.update_kernel_invariants("_dds")

        # Store default values
        self._default_freq = default_freq
        self._default_phase = default_phase
        self._default_att = default_att
        self._default_sw = default_sw
        self._min_att = min_att

    @host_only
    def init(self, *, force: bool = False) -> None:
        # System datasets
        self._config_latency_mu: np.int64 = self.get_dataset_sys(
            self.CONFIG_LATENCY_MU_KEY, np.int64(0)
        )
        self._sw_latency_mu: np.int64 = self.get_dataset_sys(
            self.SW_LATENCY_MU_KEY, np.int64(0)
        )
        self._att_latency_mu: np.int64 = self.get_dataset_sys(
            self.ATT_LATENCY_MU_KEY, np.int64(0)
        )

        self._default_freq: float = self.get_dataset_sys(
            self.FREQ_KEY, self._default_freq
        )
        self._default_phase: float = self.get_dataset_sys(
            self.PHASE_KEY, self._default_phase
        )
        self._default_att: float = self.get_dataset_sys(self.ATT_KEY, self._default_att)
        self._default_sw: bool = self.get_dataset_sys(self.SW_KEY, self._default_sw)
        self._min_att: float = self.get_dataset_sys(self.MIN_ATT_KEY, self._min_att)

        self._default_ftw: TInt64 = self._dds.frequency_to_ftw(self._default_freq)
        # Bug: For some reason, this is returning as an int64, though `turns_to_pow` marks retrun type of int64
        self._default_pow: TInt32 = np.int32(self._dds.turns_to_pow(self._default_phase))

        self.update_kernel_invariants(
            "_config_latency_mu",
            "_sw_latency_mu",
            "_att_latency_mu",
            "_default_freq",
            "_default_phase",
            "_default_att",
            "_default_sw",
            "_min_att",
            "_default_ftw",
            "_default_pow",
        )

        # Set current values based on default
        self._current_ftw: TInt64 = self._dds.frequency_to_ftw(self._default_freq)
        self._current_pow: TInt32 = np.int32(self._dds.turns_to_pow(self._default_phase))

        if force:
            self.init_kernel()

    @kernel
    def config(
        self,
        freq: TFloat,
        phase: TFloat,
        realtime: TBool = False,
    ):
        """Configure the dds.

        :param freq: Frequency ``[0, 400MHz]``
        :param phase: Phase in turns ``[0.0, 1.0]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(
            ftw=self._dds.frequency_to_ftw(freq),
            pow=self._dds.turns_to_pow(phase),
            realtime=realtime)

    @kernel
    def config_mu(self, ftw: TInt64, pow: TInt32, realtime: TBool = False):
        """Configure the dds in mu for faster control.

        :param ftw: Frequency in ftw
        :param pow: Phase in pow
        :param realtime: :const:`True` to compensate for programming latencies
        """

        if realtime:
            # Compensate for DDS latency
            delay_mu(-self._config_latency_mu)
        else:
            # Add some slack
            delay(200 * us)

        self._dds.set_mu(ftw=ftw, pow_=pow)

        # Update current freq/phase mu values
        self._current_ftw = ftw
        self._current_pow = pow

        # No need for negative latency compensation, Artiq timeline moves ahead in `set`

    @kernel
    def config_freq_mu(self, ftw: TInt64, realtime: TBool = False):
        """Configure the dds frequency, use default phase.

        :param ftw: Frequency in ftw
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(ftw=ftw, pow=self._current_pow, realtime=realtime)

    @kernel
    def config_phase_mu(self, pow: TInt32, realtime: TBool = False):
        """Configure the dds phase, use default frequency.

        :param pow: Phase in pow
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(ftw=self._current_ftw, pow=pow, realtime=realtime)

    @kernel
    def config_freq(self, frequency: TFloat, realtime: TBool = False):
        """Configure the dds frequency, use default phase.

        :param frequency: Frequency ``[0, 400MHz]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_freq_mu(ftw=self._dds.frequency_to_ftw(frequency), realtime=realtime)

    @kernel
    def config_phase(self, phase: TFloat, realtime: TBool = False):
        """Configure the dds phase, use default frequency.

        :param pow: Phase in turns ``[0.0, 1.0]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_phase_mu(pow=self._dds.turns_to_pow(phase), realtime=realtime)

    @kernel
    def reset_config(self, realtime: TBool = False):
        """Reset DDS config to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(
            ftw=self._default_ftw,
            pow=self._default_pow,
            realtime=realtime,
        )


class DDS9910(DDSBase):
    AMP_KEY = "amp"
    MAX_AMP_KEY = "max_amp"

    # noinspection PyMethodOverriding
    def build(
        self,
        *,
        dds_key: str,
        default_freq: float = 100 * MHz,
        default_amp: float = 0.0,
        default_phase: float = 0.0,
        default_att: float = 31.5 * dB,
        default_sw: bool = False,
        min_att: float = 25 * dB,
        max_amp: float = 1.0,
        **kwargs
    ) -> None:
        # Defaults check
        assert isinstance(default_freq, float), "Frequency must be of type float"
        assert isinstance(default_amp, float), "Amplitude must be of type float"
        assert isinstance(default_phase, float), "Phase must be of type float"
        assert isinstance(default_att, float), "Attenuation must be of type float"
        assert isinstance(default_sw, bool), "Sw must be of type bool"
        assert isinstance(min_att, float), "Attenuation must be of type float"
        assert isinstance(max_amp, float), "Amplitude must be of type float"
        assert 0.0 <= default_freq <= 400 * MHz, "Frequency out of range"
        assert 0.0 <= default_amp <= 1.0, "Amplitude out of range"
        assert 0.0 <= default_phase <= 1.0, "Phase out of range"
        assert 0.0 <= default_att <= 31.5 * dB, "DDS attenuation out of range"
        assert 0.0 <= max_amp <= 1.0, "Max Amplitude out of range"
        assert 0.0 <= min_att <= 31.5 * dB, "DDS min attenuation out of range"

        # Get devices
        self._dds = self.get_device(dds_key, artiq.coredevice.ad9910.AD9910)
        self.update_kernel_invariants("_dds")

        # Store default values
        self._default_freq = default_freq
        self._default_amp = default_amp
        self._default_phase = default_phase
        self._default_att = default_att
        self._default_sw = default_sw
        self._min_att = min_att
        self._max_amp = max_amp

    @host_only
    def init(self, *, force: bool = False) -> None:
        # System datasets
        self._config_latency_mu: np.int64 = self.get_dataset_sys(
            self.CONFIG_LATENCY_MU_KEY, np.int64(0)
        )
        self._sw_latency_mu: np.int64 = self.get_dataset_sys(
            self.SW_LATENCY_MU_KEY, np.int64(0)
        )
        self._att_latency_mu: np.int64 = self.get_dataset_sys(
            self.ATT_LATENCY_MU_KEY, np.int64(0)
        )

        self._default_freq: float = self.get_dataset_sys(
            self.FREQ_KEY, self._default_freq
        )
        self._default_phase: float = self.get_dataset_sys(
            self.PHASE_KEY, self._default_phase
        )
        self._default_att: float = self.get_dataset_sys(self.ATT_KEY, self._default_att)
        self._default_sw: bool = self.get_dataset_sys(self.SW_KEY, self._default_sw)
        self._min_att: float = self.get_dataset_sys(self.MIN_ATT_KEY, self._min_att)
        self._max_amp: float = self.get_dataset_sys(self.MAX_AMP_KEY, self._max_amp)
        self._max_asf: float = self._dds.amplitude_to_asf(self._max_amp)

        self._default_ftw: TInt32 = self._dds.frequency_to_ftw(self._default_freq)
        self._default_pow: TInt32 = self._dds.turns_to_pow(self._default_phase)

        self.update_kernel_invariants(
            "_config_latency_mu",
            "_sw_latency_mu",
            "_att_latency_mu",
            # "_default_freq",
            # "_default_phase",
            # "_default_att",
            "_default_sw",
            "_min_att",
            "_max_amp",
            # "_default_ftw",
            # "_default_pow",
            "_max_asf",
        )

        self._default_amp: float = self.get_dataset_sys(self.AMP_KEY, self._default_amp)
        self._default_asf: TInt32 = self._dds.amplitude_to_asf(self._default_amp)
        # self.update_kernel_invariants("_default_amp", "_default_asf")

        # Set current values based on default
        self._current_ftw: TInt32 = self._dds.frequency_to_ftw(self._default_freq)
        self._current_asf: TInt32 = self._dds.amplitude_to_asf(self._default_amp)
        self._current_pow: TInt32 = self._dds.turns_to_pow(self._default_phase)

        if force:
            self.init_kernel()

    """DDS Operations"""
    @portable
    def set_default_freq(self, freq: TFloat):
        """Set the default frequency"""
        self._default_freq = freq
        self._default_ftw = self._dds.frequency_to_ftw(freq)

    @portable
    def set_default_amp(self, amp: TFloat):
        """Set the default amplitude"""
        self._default_amp = amp
        self._default_asf = self._dds.amplitude_to_asf(amp)

    @portable
    def set_default_phase(self, phase: TFloat):
        """Set the default phase"""
        self._default_phase = phase
        self._default_pow = self._dds.turns_to_pow(phase)

    @kernel
    def config(
        self,
        freq: TFloat,
        amp: TFloat,
        phase: TFloat,
        realtime: TBool = False,
    ):
        """Configure the dds.

        :param freq: Frequency
        :param amp: Amplitude ``[0.0, 1.0]``
        :param phase: Phase in turns ``[0.0, 1.0]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(
            ftw=self._dds.frequency_to_ftw(freq),
            pow=self._dds.turns_to_pow(phase),
            asf=self._dds.amplitude_to_asf(amp),
            realtime=realtime)

    @kernel
    def config_mu(self, ftw: TInt32, asf: TInt32, pow: TInt32, realtime: TBool = False):
        """Configure the dds in mu for faster control.

        :param ftw: Frequency in ftw
        :param asf: Amplitude in asf
        :param pow: Phase in pow
        :param realtime: :const:`True` to compensate for programming latencies
        """
        if realtime:
            # Compensate for DDS latency
            delay_mu(-self._config_latency_mu)
        else:
            # Add some slack
            delay(200 * us)

        if asf <= self._max_asf:
            self._dds.set_mu(ftw=ftw, pow_=pow, asf=asf)
        else:
            self.logger.error("Amplitude Set out of range")

        self._current_ftw = ftw
        self._current_asf = asf
        self._current_pow = pow

    @kernel
    def config_freq_mu(self, ftw: TInt32, realtime: TBool = False):
        """Configure the DDS frequency, use default amplitude and phase

        :param ftw: Frequency in ftw
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(ftw=ftw, pow=self._current_pow, asf=self._current_asf, realtime=realtime)

    @kernel
    def config_amp_mu(self, asf: TInt32, realtime: TBool = False):
        """Configure the DDS amplitude, use default frequency and phase

        :param asf: Amplitude in asf
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(ftw=self._current_ftw, pow=self._current_pow, asf=asf, realtime=realtime)

    @kernel
    def config_phase_mu(self, pow: TInt32, realtime: TBool = False):
        """Configure the DDS phase, use default frequency and amplitude

        :param pow: Phase in pow
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(ftw=self._current_ftw, pow=pow, asf=self._current_asf, realtime=realtime)

    @kernel
    def config_freq(self, frequency: TFloat, realtime: TBool = False):
        """Configure the dds frequency, use default phase and amplitude.

        :param frequency: Frequency ``[0, 400MHz]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_freq_mu(ftw=self._dds.frequency_to_ftw(frequency), realtime=realtime)

    @kernel
    def config_amp(self, amp: TFloat, realtime: TBool = False):
        """Configure the dds amplitude, use default phase and frequency.

        :param amp: Amplitude ``[0.0, 1.0]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_amp_mu(asf=self._dds.amplitude_to_asf(amp), realtime=realtime)

    @kernel
    def config_phase(self, phase: TFloat, realtime: TBool = False):
        """Configure the dds phase, use default frequency and amplitude.

        :param pow: Phase in turns ``[0.0, 1.0]``
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_phase_mu(pow=self._dds.turns_to_pow(phase), realtime=realtime)

    # No need for negative latency compensation, Artiq timeline moves ahead in `set`

    @kernel
    def reset_config(self, realtime: TBool = False,):
        """Reset DDS config to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.config_mu(
            ftw=self._default_ftw,
            asf=self._default_asf,
            pow=self._default_pow,
            realtime=realtime,
        )


class AmbiguousStateError(RuntimeError):
    """Raised if the state of the master switch is ambiguous.
    Run `dds.ms_safety_off()` to safely set the switches to the off state or
    Run `dds.reset()` to set the switches to the default state"""

    pass


class MasterSwitchDDSModuleBase(DDSBase):
    """
    This module manages the master shutter of the 370 system.
    The shutter should be open if any of the 370 systems is on (or logic)
    Before operation, each module should be set to a known state (the user should overload `init` to achieve this)
    ."""

    @kernel
    def _master_set(
        self,
        state: TBool,
        mask_n: TInt32,
        initial: TBool = False,
        realtime: TBool = False,
    ):
        """Reset DDS state to default state"""
        # Update state unknown register
        self._master_state_unknown &= mask_n

        # Update state register
        if state:
            self._master_state |= ~mask_n
        else:
            self._master_state &= mask_n

        # Verify that we do not have an ambiguous state
        if not self._master_state and bool(self._master_state_unknown) and not initial:
            # State is ambiguous if any unknown bit is high
            raise AmbiguousStateError("State of the master 370 switch is ambiguous")

        # Set the switch based on the join state
        self.set(bool(self._master_state), realtime=realtime)

    @portable
    def ms_build(self):
        # Bit register for the state
        self._master_state = np.int32(0)
        # Bit register with state unknown flags
        self._master_state_unknown = np.int32(
            0b11
        )  # Number of high bits == number of modules to share over

    @kernel
    def switch_set(
        self,
        switch: TInt32,
        state: TBool,
        realtime: TBool = False,
    ):
        """Set the local state of the Master Switch
        :param switch: indicates which switch to set
        :param state: :const:`True` to indicate the switch should be on
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self._master_set(state, ~(0b1 << switch), realtime=realtime)

    @kernel
    def ms_off(self, realtime: TBool = False):
        """Sets all switches to the "off" position without raising errors
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self._master_state = np.int32(0)
        self._master_state_unknown = np.int32(0b0)
        self.set(bool(self._master_state), realtime=realtime)

    @kernel
    def safety_off(self):
        """Sets all switches to the "off" position without raising errors"""
        self.core.break_realtime()
        self.ms_off()
        self.core.wait_until_mu(now_mu())


class MasterSwitchDDSModule9910(DDS9910, MasterSwitchDDSModuleBase):
    def build(self, *args, **kwargs):
        super(MasterSwitchDDSModule9910, self).build(*args, **kwargs)
        self.ms_build()


class MasterSwitchDDSModule9912(DDS9912, MasterSwitchDDSModuleBase):
    def build(self, *args, **kwargs):
        super(MasterSwitchDDSModule9912, self).build(*args, **kwargs)
        self.ms_build()
