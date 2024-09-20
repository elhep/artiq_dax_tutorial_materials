import typing

from dax.experiment import *

from demo_system.modules.util.dds import DDS9910
from demo_system.modules.util.state_controller import BinaryStateController


class MicrowaveModule(DDS9910, BinaryStateController, DaxModule):
    DEFAULT_QUBIT_FREQ = 120.034 * MHz
    DEFAULT_RABI_FREQ = 5.0 * MHz
    """The default microwave qubit frequency."""

    # System dataset keys
    QUBIT_FREQ_KEY = "qubit_freq"
    RABI_FREQ_KEY = "rabi_freq"

    def build(self):
        # Build Microwave Module
        DDS9910.build(
            self,
            dds_key="urukul0_ch0",
            default_freq=self.DEFAULT_QUBIT_FREQ,
            default_amp=0.5,
            default_att=10 * dB,
            min_att=10 * dB
        )

        BinaryStateController.build(
            self,
            set_cb=self._microwave_set,
            default_state=False
        )

    def init(self, *, force: bool = False) -> None:
        """Initialize this module.

        :param force: Force full initialization
        """
        super(MicrowaveModule, self).init()
        # Bug: For some reason, BSC init is not being called with super
        BinaryStateController.init(self)
        # System datasets for DDS
        self._qubit_freq = self.fetch_qubit_freq()
        self._rabi_freq = self.fetch_rabi_freq()
        self.set_default_pulse_duration(self.pi_time())
        self.update_kernel_invariants("_qubit_freq", "_rabi_freq")

        if force:
            # Initialize devices
            self.init_kernel()

    """Module functionality"""

    @portable
    def qubit_freq(self):
        return self._qubit_freq

    @portable
    def rabi_freq(self):
        return self._rabi_freq

    @portable
    def pi_time(self):
        return 0.5 / (self.rabi_freq())

    @host_only
    def fetch_qubit_freq(self, *, fallback: float = DEFAULT_QUBIT_FREQ) -> float:
        """Fetch the microwave qubit frequency from the dataset

        This function is safe to call at any time.
        """
        assert isinstance(fallback, float)
        _qubit_freq = self.get_dataset_sys(self.QUBIT_FREQ_KEY, fallback=fallback)
        return _qubit_freq

    @host_only
    def store_qubit_freq(self, freq: float) -> None:
        """Store the microwave qubit frequency in the dataset"""
        assert isinstance(freq, float)
        assert 0 * MHz < freq < 400 * MHz
        self.set_dataset_sys(self.QUBIT_FREQ_KEY, freq)

    @host_only
    def fetch_rabi_freq(
        self, *, fallback: typing.Optional[float] = DEFAULT_RABI_FREQ
    ) -> float:
        """Fetch the microwave Rabi frequency from the dataset

        This function is safe to call at any time.

        :param fallback: A fallback value in case no Rabi frequency is available
        """
        assert isinstance(fallback, float) or fallback is None
        _rabi_freq = self.get_dataset_sys(self.RABI_FREQ_KEY, fallback=fallback)
        return _rabi_freq

    def fetch_pi_time(self):
        """
        Fetch the microwave pi time from the dataset
        This function is safe to call at any time
        """
        _rabi_freq = self.fetch_rabi_freq()
        return 0.5 / (_rabi_freq)

    @host_only
    def store_rabi_freq(self, freq: float) -> None:
        """Store the microwave Rabi frequency in the dataset."""
        assert isinstance(freq, float)
        assert 0 * MHz < freq < 400 * MHz
        self.set_dataset_sys(self.RABI_FREQ_KEY, freq)

    @kernel
    def _microwave_set(self, state: TBool):
        # Set DDS
        self.set(state=state, realtime=True)
        pass
