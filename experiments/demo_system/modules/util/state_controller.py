import numpy as np
import typing

from dax.experiment import *
from dax.base.system import DaxHasSystem


class BinaryStateController(DaxHasSystem):
    """A Module for controlling systems that have binary 'On/Off' states
    Implements Symmetric and Asymmetric operations"""

    __CB_T = typing.Callable[[], None]  # Callback function type
    _set_cb: __CB_T
    _default_state = False

    # System dataset keys
    DEFAULT_PULSE_DURATION_KEY = "default_pulse_duration"

    def build(self, *, set_cb: __CB_T, default_state: bool = False, **kwargs):

        assert isinstance(default_state, bool)
        assert callable(set_cb)

        self._set_cb = set_cb
        self._default_state = default_state
        self.update_kernel_invariants("_set_cb", "_default_state")

    @host_only
    def init(self) -> None:
        self._default_pulse_duration_mu = self.fetch_default_pulse_duration_mu()

    @host_only
    def post_init(self):
        pass

    @kernel
    def reset(self):
        """Reset to default state"""
        self.set_state(state=self._default_state)

    @kernel
    def set_state(self, state: TBool):
        """Set state (asymmetric operation).
        :param state: State to set
        """
        self._set_cb(state)

    @kernel
    def on(self):
        """Turn on (asymmetric operation)."""
        self.set_state(True)

    @kernel
    def off(self):
        """Turn off (asymmetric operation)."""
        self.set_state(False)

    @kernel
    def safety_off(self):
        """Turn off the system safely (add delay to avoid RTIO Underflow)"""
        self.core.break_realtime()
        self.off()
        self.core.wait_until_mu(now_mu())

    @kernel
    def pulse_mu(self, duration: TInt64 = 0):
        """Pulse for a given period of time (symmetric operation).

        :param duration: The pulse duration in machine units
        :param realtime: :const:`True` to compensate for programming latencies
        """
        if duration <= 0:
            # Use default cooling time
            duration = self._default_pulse_duration_mu
        try:
            # Switch devices
            self.on()
            delay_mu(duration)
            self.off()
        except RTIOUnderflow:
            self.safety_off()
            raise

    @kernel
    def pulse(self, duration: TFloat = 0.0):
        """Pulse for a given period of time (symmetric operation).
        :param duration: The pulse duration, use default duration if <= 0
        """
        self.pulse_mu(self.core.seconds_to_mu(duration))

    @host_only
    def set_default_pulse_duration(self, duration: TFloat):
        self.set_default_pulse_duration_mu(self.core.seconds_to_mu(duration))

    @host_only
    def set_default_pulse_duration_mu(self, duration_mu: TInt64):
        self._default_pulse_duration_mu = duration_mu

    @host_only
    def store_default_pulse_duration(self):
        self.set_dataset_sys(
            self.DEFAULT_PULSE_DURATION_KEY, self._default_pulse_duration_mu
        )

    @host_only
    def fetch_default_pulse_duration_mu(self, default: float = 1 * ms):
        assert isinstance(default, float)
        assert default > 0 * ms
        _pulse_duration_seconds = self.get_dataset_sys(self.DEFAULT_PULSE_DURATION_KEY, default=default)
        _default_pulse_duration_mu: np.int64 = self.core.seconds_to_mu(_pulse_duration_seconds)
        return _default_pulse_duration_mu

    @portable
    def default_pulse_duration_mu(self) -> TInt64:
        return self._default_pulse_duration_mu
