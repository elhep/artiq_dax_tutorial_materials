import typing
import numpy as np

import artiq.coredevice.ttl
import artiq.coredevice.edge_counter

from dax.experiment import *


class PmtModule(DaxModule):
    # System dataset keys
    STATE_DETECTION_THRESHOLD_KEY = 'state_detection_threshold'
    ACTIVE_CHANNELS_KEY = 'active_channels'

    NUM_CHANNELS: typing.ClassVar[int] = 3
    """Total number of channels"""

    # PMT TTL and EC device keys (linear orientation)
    _PMT_TTL_KEYS = [f'ttl{i + 4}' for i in range(NUM_CHANNELS)]
    _PMT_EC_KEYS = [f'{k}_counter' for k in _PMT_TTL_KEYS]
    assert len(_PMT_EC_KEYS) == NUM_CHANNELS

    def build(self):
        # Make class variables kernel invariant
        self.update_kernel_invariants('NUM_CHANNELS')

        # PMT array
        self._ttl: typing.List[artiq.coredevice.ttl.TTLInOut] = [
            self.get_device(k, artiq.coredevice.ttl.TTLInOut) for k in self._PMT_TTL_KEYS]
        self._counter: typing.List[artiq.coredevice.edge_counter.EdgeCounter] = [
            self.get_device(k, artiq.coredevice.edge_counter.EdgeCounter) for k in self._PMT_EC_KEYS]
        self.update_kernel_invariants('_ttl', '_counter')

    def init(self, *, force: bool = False) -> None:
        """Initialize this module.

        :param force: Force full initialization
        """

        # Threshold for discriminating states
        self._state_detection_threshold: int = self.get_dataset_sys(self.STATE_DETECTION_THRESHOLD_KEY, 2)
        # The list of active PMT channels
        self._active_channels: typing.List[np.int32] = self.get_dataset_sys(self.ACTIVE_CHANNELS_KEY, [])
        # Add attributes to the kernel invariants
        self.update_kernel_invariants('_state_detection_threshold', '_active_channels')

        if force:
            # Initialize devices
            self.init_kernel()

    @kernel
    def init_kernel(self):
        # For initialization, always reset core first
        self.core.reset()

        # Set direction of PMT TTL pins
        for ttl in self._ttl:
            ttl.input()
            delay_mu(np.int64(self.core.ref_multiplier))  # Added minimal delay to make the events sequential

        # Wait until all events have been submitted, always required for initialization
        self.core.wait_until_mu(now_mu())

    def post_init(self) -> None:
        pass

    """Detection functions"""

    @kernel
    def detect_channels_mu(self, channels: TList(TInt32), duration: TInt64):
        """Parallel PMT detection using the PMT array (symmetric operation).

        Counts can be obtained using the :func:`count` and :func:`measure` functions.

        :param channels: List of PMT channels
        :param duration: Duration of detection in machine units
        :raise RTIOUnderflow: Could be raised in case of an underflow
        :raise IndexError: If a channel index is out of range
        """
        if len(channels) == 0:
            # Check that channel list is not empty
            raise ValueError('Channel list can not be empty')
        # Perform parallel detection (using low-level control for maximum performance)
        for c in channels:
            self._counter[c].set_config(True, False, False, True)
        delay_mu(duration)
        for c in channels:
            self._counter[c].set_config(False, False, True, False)

    @kernel
    def detect_channels(self, channels: TList(TInt32), duration: TFloat):
        """Parallel PMT detection using the PMT array (symmetric operation).

        Counts can be obtained using the :func:`count` and :func:`measure` functions.

        :param channels: List of PMT channels
        :param duration: Duration of detection in seconds
        """
        self.detect_channels_mu(channels, self.core.seconds_to_mu(duration))

    @kernel
    def detect_all_mu(self, duration: TInt64):
        """PMT detection using all channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with all channels.

        :param duration: Duration of detection in machine units
        """
        self.detect_channels_mu(list(self.all_channels()), duration)

    @kernel
    def detect_all(self, duration: TFloat):
        """PMT detection using all channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with all channels.

        :param duration: Duration of detection in seconds
        """
        self.detect_all_mu(self.core.seconds_to_mu(duration))

    @kernel
    def detect_active_mu(self, duration: TInt64):
        """PMT detection using active channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with only active channels.
        Note that the active channels parameter has to be set earlier.

        :param duration: Duration of detection in machine units
        """
        self.detect_channels_mu(self._active_channels, duration)

    @kernel
    def detect_active(self, duration: TFloat):
        """PMT detection using active channels (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with only active channels.
        Note that the active channels parameter has to be set earlier.

        :param duration: Duration of detection in seconds
        """
        self.detect_active_mu(self.core.seconds_to_mu(duration))

    @kernel
    def detect_mu(self, channel: TInt32, duration: TInt64):
        """PMT detection using a single channel (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with a single channel.
        If ions need to be detected in parallel, please use :func:`detect_channels_mu`.

        :param channel: The PMT channel of interest
        :param duration: Duration of detection in machine units
        """
        self.detect_channels_mu([channel], duration)

    @kernel
    def detect(self, channel: TInt32, duration: TFloat):
        """PMT detection using a single channel (symmetric operation).

        This method is a convenience function for calling :func:`detect_channels` with a single channel.
        If ions need to be detected in parallel, please use :func:`detect_channels`.

        :param channel: The PMT channel of interest
        :param duration: Duration of detection in seconds
        """
        self.detect_mu(channel, self.core.seconds_to_mu(duration))

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
        count = self._counter[channel].fetch_count()
        return count

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
        return self.count(channel) >= self._state_detection_threshold

    """Getters"""

    @host_only
    def get_pmt_array(self) -> typing.List[artiq.coredevice.edge_counter.EdgeCounter]:
        """Return the array with edge counters."""
        return self._counter.copy()  # Copy to prevent accidental mutation

    @host_only
    def get_state_detection_threshold(self) -> int:
        """Return the state detection threshold."""
        return self._state_detection_threshold

    """Channel helpers"""

    @portable
    def all_channels(self) -> TRange32:
        """Return a range with all channels.

        The range can be converted to a list using `list()` if desired.

        :return: Range object covering all channels
        """
        return range(self.NUM_CHANNELS)

    @portable
    def active_channels(self) -> TList(TInt32):
        """Get the list of active channels.

        :return: List of active channels
        """
        return self._active_channels

    @host_only
    def set_active_channels(self, active_channels: typing.Sequence[np.int32]) -> None:
        """Update the list of active channels after ion loading.

        :param active_channels: The list of active channels
        """
        # Store value locally and in the dataset
        assert len(active_channels) <= self.NUM_CHANNELS, 'Too many channels'
        assert all(0 <= c < self.NUM_CHANNELS for c in active_channels), 'Channel out of range'
        assert len(set(active_channels)) == len(active_channels), 'Duplicate channels'
        self._active_channels = [np.int32(c) for c in active_channels]
        self.set_dataset_sys(self.ACTIVE_CHANNELS_KEY, self._active_channels)
