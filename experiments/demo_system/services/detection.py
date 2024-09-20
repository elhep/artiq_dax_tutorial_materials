import typing
import numpy as np

import artiq.coredevice.edge_counter

from dax.experiment import *
from dax.interfaces.detection import DetectionInterface

from demo_system.modules.pmt import PmtModule
from demo_system.modules.cw_laser import MODES370, Laser370


class DetectionService(DaxService, DetectionInterface):
    SERVICE_NAME = "detection"

    # System dataset keys
    DETECTION_TIME_KEY = "detection_time"

    def build(self):
        # Get the relevant modules
        self._pmt = self.registry.find_module(PmtModule)
        self._370 = self.registry.find_module(Laser370)
        self.update_kernel_invariants("_pmt", "_370")

    def init(self) -> None:
        # Default detection time
        self._detection_time: float = self.get_dataset_sys(
            self.DETECTION_TIME_KEY, 20 * us
        )
        self.update_kernel_invariants("_detection_time")

    def post_init(self) -> None:
        pass

    """Detection functions"""

    @kernel
    def detect_channels_mu(
        self,
        channels: TList(TInt32),
        duration: TInt64 = 0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using the PMT array (symmetric operation).

        Counts can be obtained using the :func:`count` and :func:`measure` functions.

        :param channels: List of PMT channels
        :param duration: Duration of detection in machine units, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, default `True`
        """
        trigger_shutter = True
        if duration <= 0:
            # Use default duration
            duration = self.core.seconds_to_mu(self._detection_time)

        try:
            # Configure DDS and shutter
            if mode != MODES370.NONE:
                self._370.config_mode(mode=mode)
            if trigger_shutter:
                self._370.set_shutter(True)

            # Perform Detection
            self._pmt.detect_channels_mu(channels, duration)

            # Reset shutter
            if trigger_shutter:
                self._370.set_shutter(False)
        except RTIOUnderflow:
            self.logger.error("RTIO Underflow")
            self.core.break_realtime()
            self._370.reset()
            self.core.wait_until_mu(now_mu())
            raise
        except IndexError:
            self.logger.error("Index Error")
            self.core.break_realtime()
            self._370.reset()
            self.core.wait_until_mu(now_mu())
            raise

    @kernel
    def detect_channels(
        self,
        channels: TList(TInt32),
        duration: TFloat = 0.0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using the PMT array (symmetric operation).

        Counts can be obtained using the :func:`count` and :func:`measure` functions.

        :param channels: List of PMT channels
        :param duration: Duration of detection in seconds, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_channels_mu(
            channels,
            duration=self.core.seconds_to_mu(duration),
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect_all_mu(
        self,
        duration: TInt64 = 0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using all PMT channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with all channels.

        :param duration: Duration of detection in machine units, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_channels_mu(
            channels=list(self._pmt.all_channels()),
            duration=duration,
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect_all(
        self,
        duration: TFloat = 0.0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using all PMT channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with all channels.

        :param duration: Duration of detection in seconds, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_all_mu(
            duration=self.core.seconds_to_mu(duration),
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect_active_mu(
        self,
        duration: TInt64 = 0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using active PMT channelsMODES370 (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with only active channels.
        Note that the active channels parameter has to be set earlier.

        :param duration: Duration of detection in machine units, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_channels_mu(
            channels=self._pmt.active_channels(),
            duration=duration,
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect_active(
        self,
        duration: TFloat = 0.0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using active PMT channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with only active channels.
        Note that the active channels parameter has to be set earlier.

        :param duration: Duration of detection in seconds, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_active_mu(
            duration=self.core.seconds_to_mu(duration),
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect_mu(
        self,
        channel: TInt32,
        duration: TInt64 = 0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using a PMT channel (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with a single channel.
        If ions need to be detected in parallel, please use :func:`detect_channels_mu`.

        :param channel: The PMT channel of interest
        :param duration: Duration of detection in machine units, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_channels_mu(
            channels=[channel],
            duration=duration,
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    @kernel
    def detect(
        self,
        channel: TInt32,
        duration: TFloat = 0.0,
        mode: TInt32 = MODES370.DETECT,
        trigger_shutter: TBool = True,
    ):
        """Detect ions using a PMT channel (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with a single channel.
        If ions need to be detected in parallel, please use :func:`detect_channels`.

        :param channel: The PMT channel of interest
        :param duration: Duration of detection in seconds, default value if none is given
        :param mode: The mode to use for detection, default `MODES370.DETECT`
        :param trigger_shutter: Whether to trigger the 370 shutter, defaul `True`
        """
        self.detect_mu(
            channel=channel,
            duration=self.core.seconds_to_mu(duration),
            mode=mode,
            trigger_shutter=trigger_shutter,
        )

    """Fetch functions"""

    @kernel
    def count(self, channel: TInt32) -> TInt32:
        """Return the PMT count of a specific channel.

        This function can be used in a list comprehension to obtain the counts of a list of channels:

        ``results = [count(c) for c in channels]``

        This function can not directly return the array with results due to
        limitations in the compiler (dynamic memory management).

        :param channel: The PMT channel
        :return: The count of the given PMT channel
        """
        return self._pmt.count(channel)

    @kernel
    def measure(self, channel: TInt32) -> TBool:
        """Read the PMT count of a specific channel and discriminate against the state detection threshold.

        This function can be used in a list comprehension to obtain the measurements of a list of channels:

        ``results = [measure(c) for c in channels]``

        This function can not directly return the array with results due to
        limitations in the compiler (dynamic memory management).

        :param channel: The PMT channel
        :return: True if the number of detected events was above the threshold
        """
        return self._pmt.measure(channel)

    """Interface functions"""

    @portable
    def all_channels(self) -> TRange32:
        """Return a range with all channels.

        The range can be converted to a list using `list()` if desired.

        :return: Range object covering all channels
        """
        return self._pmt.all_channels()

    def NUM_CHANNELS(self) -> TInt32:
        """Return the number of PMT channels.

        :return: Number of PMT channels
        """
        return self._pmt.NUM_CHANNELS

    @host_only
    def get_pmt_array(self) -> typing.List[artiq.coredevice.edge_counter.EdgeCounter]:
        return self._pmt.get_pmt_array()

    @host_only
    def get_state_detection_threshold(self) -> int:
        return self._pmt.get_state_detection_threshold()

    @host_only
    def get_default_detection_time(self) -> float:
        return self._detection_time

    @host_only
    def set_active_channels(self, active_channels: typing.Sequence[np.int32]) -> None:
        """Update the list of active channels after ion loading.

        :param active_channels: The list of active channels
        """
        self._pmt.set_active_channels(active_channels=active_channels)
