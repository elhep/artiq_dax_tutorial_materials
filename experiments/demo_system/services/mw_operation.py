import numpy as np

from dax.experiment import *
from dax.interfaces.operation import OperationInterface

from demo_system.modules.properties import PropertiesModule
from demo_system.modules.microwave import MicrowaveModule
from demo_system.modules.pmt import PmtModule
from demo_system.services.state import StateService
from demo_system.services.detection import DetectionService
from demo_system.services.cool_prep import CoolInitService
from demo_system.modules.trigger_ttl import TriggerTTLModule
from demo_system.modules.scope import ScopeModule

# noinspection PyAbstractClass
class MicrowaveOperationService(DaxService, OperationInterface):
    SERVICE_NAME = "mw_operation"

    # System dataset keys
    DEFAULT_REALTIME_KEY = "default_realtime"

    _POW_BITS = 14
    """Number of bits in the phase offset word."""
    _POW_PI = np.int32(1 << (_POW_BITS - 1))
    """Pi as phase offset word."""
    _POW_PI_3_4 = np.int32(round((1 << _POW_BITS) * 0.75))
    """3/4ths Pi as phase offset word."""

    def build(self):
        # Kernel invariant class variables
        self.update_kernel_invariants("_POW_PI", "_POW_PI_3_4")
        # Kernel invariant properties
        self.update_kernel_invariants(
            "pi", "num_qubits"
        )

        # Get modules and services
        self._yb171 = self.registry.find_module(PropertiesModule)
        self._microwave = self.registry.find_module(MicrowaveModule)
        self._pmt = self.registry.find_module(PmtModule)
        self._state = self.registry.get_service(StateService)
        self._cool_pump = self.registry.get_service(CoolInitService)
        self._detection = self.registry.get_service(DetectionService)
        self._trigger: TriggerTTLModule = self.registry.find_module(TriggerTTLModule)
        self._scope: ScopeModule = self.registry.find_module(ScopeModule)
        self.update_kernel_invariants(
            "_yb171", "_microwave", "_pmt", "_state", "_cool_pump", "_detection", "_trigger", "_scope"
        )

    @host_only
    def init(self) -> None:
        # Realtime flag
        self._realtime: bool = self.get_dataset_sys(self.DEFAULT_REALTIME_KEY, False)
        self.update_kernel_invariants("_realtime")
        self._state.histogram.plot_histogram()
        self._state.histogram.plot_probability()
        # self._scope.setup()

    @host_only
    def post_init(self) -> None:
        pass

    """Properties and configuration"""

    @property
    def num_qubits(self) -> np.int32:
        return np.int32(self._yb171.num_ions)

    @host_only
    def set_realtime(self, realtime: bool) -> None:
        assert isinstance(realtime, bool), "Realtime flag must be of type bool"
        self._realtime = realtime

    @portable
    def _duration_pi_mu(self) -> TInt64:
        """Pulse duration for a pi pulse in machine units."""
        return self.core.seconds_to_mu(self._microwave.pi_time())

    @portable
    def _channel_map(self) -> TList(TInt32):
        """A map to convert qubit index to channel."""
        return self._pmt.active_channels()

    """Operations"""

    @kernel
    def prep_0_all(self):
        # self._trigger.pulse()
        # Cool
        delay(1 * us)
        self._cool_pump.cool.pulse()
        delay(1 * us)
        # Initialize
        self._cool_pump.prep.pulse()

    @kernel
    def m_z_all(self):
        # Detection
        self._detection.detect_active()

    """Measurement handling"""

    @kernel
    def get_measurement(self, qubit: TInt32) -> TInt32:
        return self._detection.measure(self._channel_map()[qubit])

    @kernel
    def get_measurement_all(self) -> TList(TInt32):
        return [self._detection.measure(ch) for ch in self._channel_map()]

    @kernel
    def store_measurements(self, qubits: TList(TInt32)):
        self._state.measure_channels([self._channel_map()[q] for q in qubits])
        # self._scope.store_waveform()

    """Gate functions"""

    @kernel
    def _pulse_mu(self, duration: TInt64, pow_: TInt32):
        """Arbitrary rotation (pulse duration) with arbitrary phase.

        :param duration: Angle to rotate by given as a pulse duration in machine units
        :param pow_: Phase of the MW DDS as a phase offset word
        """
        self._microwave.config_phase_mu(pow=pow_, realtime=self._realtime)
        self._microwave.pulse_mu(duration)

    @kernel(flags={"fast-math"})
    def _rotate_mu(self, theta: TFloat, pow_: TInt32):
        """Arbitrary rotation with arbitrary phase.

        :param theta: Angle to rotate by
        :param pow_: Phase of the MW DDS as a phase offset word
        """
        self._pulse_mu(self.core.seconds_to_mu(theta / self._duration_pi_mu()), pow_=pow_)

    @kernel(flags={"fast-math"})
    def rphi(self, theta: TFloat, phi: TFloat, qubit: TInt32 = -1):
        # TODO: the correctness of this function has not been verified yet
        self._rotate_mu(theta, pow_=self._microwave.turns_to_pow(phi / 2 * self.pi))

    @kernel
    def rx(self, theta: TFloat, qubit: TInt32 = -1):
        if theta >= 0.0:
            self._rotate_mu(theta, 0)
        else:
            self._rotate_mu(-theta, self._POW_PI)

    @kernel
    def ry(self, theta: TFloat, qubit: TInt32 = -1):
        if theta >= 0.0:
            self._rotate_mu(theta, self._POW_PI >> 1)
        else:
            self._rotate_mu(-theta, self._POW_PI_3_4)

    @kernel
    def rz(self, theta: TFloat, qubit: TInt32 = -1):
        # Z rotations are not native to Rabi interactions, requires a combination of X and Y rotations.
        # Using Euler angles, we can achieve this by performing the rotation Rx(pi/2)Ry(theta)Rx(-pi/2).
        self.sqrt_x_dag()
        self.ry(theta)
        self.sqrt_x()

    @kernel
    def i(self, qubit: TInt32 = -1):
        pass

    @kernel
    def x(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu(), 0)

    @kernel
    def y(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu(), self._POW_PI >> 1)

    @kernel
    def z(self, qubit: TInt32 = -1):
        self.sqrt_x_dag()
        self.y()
        self.sqrt_x()

    @kernel
    def sqrt_x(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, 0)

    @kernel
    def sqrt_x_dag(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI)

    @kernel
    def sqrt_y(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI >> 1)

    @kernel
    def sqrt_y_dag(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI_3_4)

    @kernel
    def sqrt_z(self, qubit: TInt32 = -1):
        self.sqrt_x_dag()
        self.sqrt_y()
        self.sqrt_x()

    @kernel
    def sqrt_z_dag(self, qubit: TInt32 = -1):
        self.sqrt_x_dag()
        self.sqrt_y_dag()
        self.sqrt_x()

    @kernel
    def h(self, qubit: TInt32 = -1):
        # Hadamard is equivalent to (1/sqrt(2))*(X + Z).
        # However, Z rotation is not native to Rabi oscillations.
        # We can achieve the same result with Rx(pi/2)(1/sqrt(2))*(X + Y)Rx(-pi/2).
        self.sqrt_x_dag()
        self._pulse_mu(self._duration_pi_mu(), self._POW_PI >> 2)
        self.sqrt_x()
