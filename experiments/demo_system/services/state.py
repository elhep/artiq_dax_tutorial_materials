from dax.experiment import *
from dax.modules.hist_context import HistogramContext

from demo_system.modules.pmt import PmtModule
from demo_system.services.detection import DetectionService


class StateService(DaxService):
    SERVICE_NAME = 'state'

    # System dataset keys
    INIT_TIME_KEY = 'init_time'

    def build(self) -> None:
        # Obtain required modules
        self._pmt = self.registry.find_module(PmtModule)
        self._detection = self.registry.get_service(DetectionService)
        self.update_kernel_invariants('_pmt', '_detection')

        # Create histogram context
        self._histogram_context = HistogramContext(self, 'histogram',
                                                   plot_base_key='{scheduler.rid}', plot_group_base_key='dax')
        self.update_kernel_invariants('histogram', '_histogram_context')

    @host_only  # Added to prevent confusion with other functions
    def init(self) -> None:
        self._init_time: float = self.get_dataset_sys(self.INIT_TIME_KEY, 15 * us)
        self.update_kernel_invariants('_init_time')

    @host_only  # Added to prevent confusion with other functions
    def post_init(self) -> None:
        pass

    """Service functionality"""

    @property
    def histogram(self) -> HistogramContext:
        """Return the histogram context object.

        This context can be used with a `with` statement.
        Only inside this context it is possible to use the
        :func:`count` and :func:`measure` related functions.

        This context can be used inside or outside kernel context
        and relies on async RPC calls for enter and exit.

        The histogram context can be further configured by calling its functions.

        :return: The histogram context object
        """
        return self._histogram_context

    @kernel
    def count_channels(self, channels: TList(TInt32)):
        """Record the PMT counts of a list of channels.

        The count values are requested from the detection module and
        the results are stored in the histogram buffer.

        :param channels: The channels to record the counts of
        """

        # Append the list of detection counts to the histogram buffer
        self.histogram.append([self._detection.count(c) for c in channels])

    @kernel
    def count_all(self):
        """Record the PMT counts of all channels.

        The count values are requested from the detection module and
        the results are stored in the histogram buffer.
        """

        # Append the list of detection counts to the histogram buffer
        self.histogram.append([self._detection.count(c) for c in self._pmt.all_channels()])

    @kernel
    def count_active(self):
        """Record the PMT counts of active channels.

        The count values are requested from the detection module and
        the results are stored in the histogram buffer.
        """

        # Append the list of detection counts to the histogram buffer
        self.histogram.append([self._detection.count(c) for c in self._pmt.active_channels()])

    @kernel
    def count(self, channel: TList(TInt32)):
        """Record the PMT count of a specific channel.

        The count value is requested from the detection module and
        the result is stored in the histogram buffer.

        :param channel: The channel to record the count of
        """

        # Append the detection count to the histogram buffer
        self.histogram.append([self._detection.count(channel)])  # Make it a list for data uniformity

    @kernel
    def measure_channels(self, channels: TList(TInt32)):
        """Record the PMT counts of a list of channels discriminated against the state detection threshold.

        The count values are requested from the detection module and
        the results are discriminated and stored in the histogram buffer.

        :param channels: The channels to record the measurements of
        """
        self.histogram.append([self._detection.measure(c) for c in channels])

    @kernel
    def measure_all(self):
        """Record the PMT counts of all channels discriminated against the state detection threshold.

        The count values are requested from the detection module and
        the results are discriminated and stored in the histogram buffer.
        """
        self.histogram.append([self._detection.measure(c) for c in self._pmt.all_channels()])

    @kernel
    def measure_active(self):
        """Record the PMT counts of active channels discriminated against the state detection threshold.

        The count values are requested from the detection module and
        the results are discriminated and stored in the histogram buffer.
        """
        self.histogram.append([self._detection.measure(c) for c in self._pmt.active_channels()])

    @kernel
    def measure(self, channel: TInt32):
        """Record the PMT count of a specific channel discriminated against the state detection threshold.

        The count value is requested from the detection module and
        the result is discriminated and stored in the histogram buffer.

        :param channel: The channel to record the measurement of
        """
        self.histogram.append([self._detection.measure(channel)])  # Make it a list for data uniformity
