import abc
import typing

import numpy as np

from dax.scan import DaxScan
from dax.modules.hist_context import HistogramAnalyzer
from dax.util.artiq import is_kernel

# from dax_pulse.scan import RFSoCScan

from demo_system.system import *

__all__ = ["GateScan"]  # , 'RFSoCGateScan']


class GateScan(DaxScan, DemoSystem, abc.ABC):
    """Base class for gate scan experiments."""

    DEFAULT_LAZY_TIMING: typing.ClassVar[bool] = False
    """Default setting for lazy timing option."""

    @abc.abstractmethod
    def build_gate_scan(self):
        """Build the gate scan experiment."""
        pass

    @kernel
    def gate_setup(self):
        """Define the gate setup function, which runs once at the start of the scan."""
        pass

    @kernel
    def gate_config(self, point, index):
        """Define the gate configuration for each point."""
        pass

    @kernel
    def gate_pre_action(self, point, index):
        """Define a pre-gate action for each sample, which is called before cool and initialization pulses."""
        pass

    @abc.abstractmethod
    def gate_action(self, point, index):
        """Define the gate action for each sample."""
        pass

    @kernel
    def initialize(self):
        if self._enable_initialization:
            # Initialize
            self.cool_prep.prep.pulse()
            pass

    @kernel
    def detect(self):
        self.detection.detect_active()

    def build_scan(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        # Check functions
        assert is_kernel(
            self.gate_config
        ), "The gate_config() function must be a kernel"
        assert is_kernel(
            self.gate_pre_action
        ), "The gate_setup() function must be a kernel"
        assert is_kernel(
            self.gate_action
        ), "The gate_action() function must be a kernel"

        # Add scans
        self.build_gate_scan(*args, **kwargs)  # type: ignore[call-arg]

        # General arguments
        self._gate_scan_num_samples: int = self.get_argument(
            "Num samples",
            NumberValue(10, ndecimals=0, scale=1, step=1, min=0),
            tooltip="Number of samples per point",
        )
        self._gate_scan_cooling_duration: float = self.get_argument(
            "Cooling duration", NumberValue(10 * us, min=0 * ms, unit="ms")
        )
        self.update_kernel_invariants(
            "_gate_scan_num_samples", "_gate_scan_cooling_duration"
        )

        # Advanced arguments
        self._buffer_size: int = self.get_argument(
            "Buffer size",
            NumberValue(8, min=0, max=32, step=1, ndecimals=0),
            group="Advanced",
        )
        self._lazy_timing: bool = self.get_argument(
            "Lazy timing",
            BooleanValue(self.DEFAULT_LAZY_TIMING),
            group="Advanced",
            tooltip="Insert extra delays to prevent underflow exceptions",
        )
        self._enable_cool: bool = self.get_argument(
            "Enable cool",
            BooleanValue(True),
            group="Advanced",
            tooltip="Enable cooling pulse",
        )
        self._enable_initialization: bool = self.get_argument(
            "Enable initialization",
            BooleanValue(True),
            group="Advanced",
            tooltip="Enable state initialization pulse",
        )
        self._enable_gate_action: bool = self.get_argument(
            "Enable action",
            BooleanValue(True),
            group="Advanced",
            tooltip="Enable gate action",
        )
        self.update_kernel_invariants(
            "_buffer_size",
            "_lazy_timing",
            "_enable_cool",
            "_enable_initialization",
            "_enable_gate_action"
        )

        # Plot arguments
        self._plot_histogram: bool = self.get_argument(
            "Plot PMT count histograms", BooleanValue(True), group="Plot"
        )
        self._plot_probability: bool = self.get_argument(
            "Plot state probability", BooleanValue(True), group="Plot"
        )
        self._plot_mean_count: bool = self.get_argument(
            "Plot mean count", BooleanValue(False), group="Plot"
        )

        self._view_scope: bool = self.get_argument(
            "View Scope", BooleanValue(False)
        )

    def host_enter(self) -> None:
        # Check number of scans (i.e. dimensions)
        self.__scannables = self.get_scannables()
        assert len(self.__scannables) > 0, "There must be at least one scan"

        # Limit buffer size in case of a low number of samples
        self._buffer_size = min(self._buffer_size, self._gate_scan_num_samples)
        # Generate a fit dataset key
        self._fit_dataset_key = f"plot.{self.scheduler.rid}.fit"

    def host_setup(self) -> None:
        # Call DAX init
        self.dax_init()

        # Prepare plot kwargs
        plot_kwargs = {
            "fit": self._fit_dataset_key,
        }

        if self.is_infinite_scan:
            # Set a sliding window and no X values
            plot_kwargs["sliding_window"] = 300
        elif len(self.__scannables) == 1 and (
            self._plot_probability or self._plot_mean_count
        ):
            # Extract extra plot data and add plot kwargs
            label, _ = self.__scannables.copy().popitem()
            x_dataset_key = f"plot.{self.scheduler.rid}.{label}"
            plot_kwargs["x_label"] = label
            plot_kwargs["x"] = x_dataset_key

            # Broadcast scan values for plotting
            self.set_dataset(
                x_dataset_key, self.__scannables[label], broadcast=True, archive=False
            )

        if self._plot_probability:
            # Plot probability
            self.state.histogram.plot_probability(**plot_kwargs)

        if self._plot_mean_count:
            # Plot mean counts
            self.state.histogram.plot_mean_count(**plot_kwargs)

        if self._plot_histogram:
            # Plot histograms
            self.state.histogram.plot_histogram()

        self._slop_time_mu = self.core.seconds_to_mu(1 * us)
        self._detect_time_mu = self.core.seconds_to_mu(100 * us)
        self._cool_time_mu = self.core.seconds_to_mu(200 * us) # self._gate_scan_cooling_duration)

        self.update_kernel_invariants("_slop_time_mu", "_detect_time_mu", "_cool_time_mu")

    @kernel
    def device_setup(self):  # type: () -> None
        # Reset core
        self.core.reset()

        # Gate setup
        self.core.break_realtime()
        self.gate_setup()

    
    @kernel
    def _gate_scan_run_point(self, point, index):
        if self._lazy_timing or self._buffer_size == 0:
            self.core.break_realtime()

        # Gate pre-init action
        self.gate_pre_action(point, index)

        self.core.break_realtime()
        self.trigger_ttl.pulse_mu()
        delay_mu(self._slop_time_mu)
        self.cool_prep.cool.pulse_mu(self._cool_time_mu)
        self.gate_action(point, index)
        # Detect state
        delay_mu(self._slop_time_mu) 
        self.detection.detect_active_mu(duration=self._detect_time_mu)
        self.core.break_realtime()

    @kernel
    def run_point(self, point, index):
        if self._view_scope:
            self.scope.setup()
        # Guarantee slack
        self.core.break_realtime()
        # Configure gate
        self.gate_config(point, index)

        with self.state.histogram:
            # Build up a buffer
            for _ in range(self._buffer_size):
                self._gate_scan_run_point(point, index)

            # Pipelined execution
            for _ in range(self._gate_scan_num_samples - self._buffer_size):
                self._gate_scan_run_point(point, index)
                self.state.count_active()

            # Clear buffers
            for _ in range(self._buffer_size):
                self.state.count_active()

        if self._view_scope:
            self.scope.store_waveform()
        self.core.break_realtime()

    @kernel
    def device_cleanup(self):  # type: () -> None
        # Gain slack
        self.core.break_realtime()
        # System Idle
        self.idle()
        # Sync
        self.core.wait_until_mu(now_mu())

    def analyze(self):
        if not self.is_infinite_scan and not self.is_terminated_scan:
            # Only analyze if we were not in an infinite scan
            h = HistogramAnalyzer(self)

            if len(self.__scannables) == 1:
                label, values = self.__scannables.copy().popitem()
                h.plot_all_probabilities(x_label=label, x_values=values)
            else:
                h.plot_all_probabilities()

    """User functions"""

    @host_only
    def plot_fit(self, data):
        """Plot the fit (adds fit to the probability plot).

        See also :func:`plot_fit_single`.

        :param data: Fit data of multiple graphs
        """
        self.set_dataset(
            self._fit_dataset_key,
            np.asarray(data).transpose(),
            broadcast=True,
            archive=False,
        )

    @host_only
    def plot_fit_single(self, data):
        """Plot the fit for a single-ion experiment (adds fit to the probability plot).

        See also :func:`plot_fit`.

        :param data: Fit data
        """
        # Nest data in a list
        self.plot_fit([data])

    def clear_fit(self) -> None:
        """Clear the fit data."""
        self.plot_fit([])


# class RFSoCGateScan(GateScan, RFSoCScan, abc.ABC):
#     SCAN_POINT_SCHEDULE_DURATION_KEY = 'schedule_duration_mu'
#     """The point object will be mutated during ``RFSoCScan.host_setup`` to include this key with a value corresponding
#     to the duration of the uploaded pulse schedule in ARTIQ machine units. The value will be accessible the same way
#     the scan parameters are -- e.g. ``point.schedule_duration_mu``."""
#     COMPILE_DURING_RUN = True
#     """Wait to evaluate/compile schedules until the run phase (``host_enter``)
#     so that dataset values from previous experiments are available."""

#     def build_scan(self, *args: typing.Any, **kwargs: typing.Any) -> None:
#         super(RFSoCGateScan, self).build_scan(*args, **kwargs)
#         # add RFSoC-specific arguments
#         self._use_lookup_tables = self.get_argument(
#             'Use lookup tables',
#             BooleanValue(True),
#             group='RFSoC',
#             tooltip='Set to True to use the lookup tables, False to use streaming mode'
#         )

#     def host_enter(self, **compile_kwargs) -> None:
#         GateScan.host_enter(self)
#         RFSoCScan.host_enter(self, **compile_kwargs)

#     def host_setup(self, **upload_kwargs) -> None:
#         """``upload_kwargs`` are passed (via ``RFSoCScan.host_setup``) to ``RFSoCModule.upload()``.

#         See module for details.
#         """
#         # a plain super() call won't work since neither GateScan nor RFSoCScan calls super().host_setup()
#         GateScan.host_setup(self)
#         # insert GateScan's `loop_number` as `num_repeats_per_schedule`
#         if 'num_repeats_per_schedule' in upload_kwargs:
#             self.logger.warning(f'Overwriting upload_kwargs using self._gate_scan_num_samples '
#                                 f'({self._gate_scan_num_samples}) as "num_repeats_per_schedule"')
#         upload_kwargs['num_repeats_per_schedule'] = self._gate_scan_num_samples
#         if 'streaming' in upload_kwargs:
#             self.logger.warning('Overwriting "streaming" argument using self._use_lookup_tables.')
#         upload_kwargs['streaming'] = not self._use_lookup_tables
#         # need to override some internal RFSoC scan behavior since we changed the signature of rfsoc_compile
#         self._beam_targets, self._rfsoc_scan_compiled_schedule_list = self._rfsoc_scan_compiled_schedule_list
#         RFSoCScan.host_setup(self, **upload_kwargs)
