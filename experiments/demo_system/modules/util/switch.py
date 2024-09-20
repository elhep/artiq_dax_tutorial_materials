import artiq.coredevice.ttl

from dax.experiment import *
import numpy as np


class Switch(DaxModule):
    """A System Class for controlling Binary switch operations
    Implements state set with latency compensation"""

    SW_TYPE = artiq.coredevice.ttl.TTLOut
    """Switch device type."""

    ACTIVE_LOW_KEY = 'active_low'
    STATE_KEY = 'default_state'
    LATENCY_MU_KEY = 'latency'

    # noinspection PyMethodOverriding
    def build(self, *, sw_key: str, active_low: bool = False, default_state: bool = False) -> None:
        assert isinstance(sw_key, str)
        assert isinstance(active_low, bool)
        assert isinstance(default_state, bool)

        # Obtain switch device
        self._sw = self.get_device(sw_key, self.SW_TYPE)
        self.update_kernel_invariants('_sw')

        # Store build parameters
        self._active_low = active_low
        self._default_state = default_state
        self.update_kernel_invariants('_active_low', '_default_state')

    def init(self, force: bool = False) -> None:
        self._sw_latency_mu: np.int64 = self.get_dataset_sys(self.LATENCY_MU_KEY, np.int64(0))
        self.update_kernel_invariants('_sw_latency_mu')

        self._active_low: float = self.get_dataset_sys(self.ACTIVE_LOW_KEY, self._active_low)
        self._default_state: float = self.get_dataset_sys(self.STATE_KEY, self._default_state)

        self._current_state: float = self._default_state

        if force:
            self.init_kernel()

    @portable
    def current_state(self) -> TBool:
        return self._current_state

    @kernel
    def init_kernel(self):
        self.core.reset()
        self.core.break_realtime()
        self.reset()
        # Wait until event is submitted
        self.core.wait_until_mu(now_mu())

    def post_init(self) -> None:
        pass

    """Module functionality"""
    @kernel
    def safety_off(self):
        """Turn off Switch Safely"""
        self.core.break_realtime()
        self.set(state=False)
        self.core.wait_until_mu(now_mu())

    @kernel
    def set(self, state: TBool, realtime: TBool = False):
        """Set SW output state
        :param state: :const: `True` to enable DDS
        :param realtime: :const:`True` to compensate for programming latencies
        """
        if realtime:
            # Compensate for latency
            delay_mu(-self._sw_latency_mu)

        # Set output Sw
        new_state = state != self._active_low
        self._current_state = new_state
        self._sw.set_o(new_state)

        if realtime:
            # Compensate for latency, switch set is a 0-time operation in Artiq
            delay_mu(self._sw_latency_mu)

    @kernel
    def reset(self, realtime: TBool = False):
        """Reset SW state to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self.set(self._default_state, realtime=realtime)
