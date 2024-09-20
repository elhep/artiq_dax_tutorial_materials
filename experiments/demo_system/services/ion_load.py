import typing

import numpy as np

from dax.experiment import *
from dax.util.ccb import get_ccb_tool

from demo_system.modules.ablation import AblationModule
from demo_system.modules.pmt import PmtModule
from demo_system.modules.properties import PropertiesModule

from demo_system.services.cool_prep import CoolInitService
from demo_system.services.detection import DetectionService

from demo_system.modules.cw_laser import Laser355, MODES370


class IonLoadError(RuntimeError):
    """Error raised when the system failed to load the desired number of ions in the given constraints."""
    pass


class IonReleaseError(RuntimeError):
    """Error raised when the system failed to release the ions in the given constraints."""
    pass


class IonLoadService(DaxService):
    SERVICE_NAME = 'ion_load'

    # Constants for plotting
    COUNT_PLOT_KEY: typing.ClassVar[str] = 'plot.load.counts'
    COUNT_PLOT_NAME: typing.ClassVar[str] = 'load'
    COUNT_PLOT_Y_SCALE_LABEL: typing.ClassVar[str] = 'kHz'
    assert COUNT_PLOT_Y_SCALE_LABEL in globals(), 'Invalid scale'
    COUNT_PLOT_Y_SCALE: typing.ClassVar[str] = globals()[COUNT_PLOT_Y_SCALE_LABEL]
    COUNT_PLOT_DEFAULT_KWARGS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'sliding_window': 300,
        'y_label': f'Counts per second ({COUNT_PLOT_Y_SCALE_LABEL})',
        'plot_names': 'PMT'
    }
    PLOT_GROUP: typing.ClassVar[str] = 'load'

    _MANUAL_LOAD = PmtModule.NUM_CHANNELS + 1
    """Constant used for num ions to indicate manual load."""

    DEFAULT_BUFFER_SIZE = 3
    """Default buffer size for loading."""

    # System dataset keys
    ION_ABSENCE_THRESHOLD_KEY: typing.ClassVar[str] = 'ion_absence_threshold'
    LOAD_DETECTION_WINDOW_KEY: typing.ClassVar[str] = 'load_detection_window'
    LOAD_MAX_TIME_KEY: typing.ClassVar[str] = 'load_max_time'
    LOAD_NUM_RELEASES_KEY: typing.ClassVar[str] = 'load_num_releases'

    def build(self) -> None:
        # Get modules
        self._ablation = self.registry.find_module(AblationModule)
        self._yb171 = self.registry.find_module(PropertiesModule)

        self.update_kernel_invariants('_ablation')

        # Get services
        self._cool_prep: CoolInitService = self.registry.get_service("cool_prep")
        self._detection: DetectionService = self.registry.get_service("detection")

        # Get ionization module
        self._l355: Laser355 = self.registry.find_module(Laser355)

        self.update_kernel_invariants('_l355')

        # Get scheduler
        self._scheduler = self.get_device('scheduler')
        self.update_kernel_invariants('_scheduler')

        # Get a CCB tool
        self._ccb = get_ccb_tool(self)

    def init(self) -> None:
        # Service configuration
        self._ion_absence_threshold: float = self.get_dataset_sys(self.ION_ABSENCE_THRESHOLD_KEY, 5 * kHz)
        self.update_kernel_invariants('_ion_absence_threshold')

        # Load ion default configuration
        self._load_detection_window: float = self.get_dataset_sys(self.LOAD_DETECTION_WINDOW_KEY, 100 * ms)
        self._load_max_time: float = self.get_dataset_sys(self.LOAD_MAX_TIME_KEY, 300 * s)
        self._load_num_releases: int = self.get_dataset_sys(self.LOAD_NUM_RELEASES_KEY, 10)

    def post_init(self) -> None:
        pass

    """Service functionality"""

    @host_only
    def load_ions(
            self,
            num_ions: int,
            *,
            strict: bool = False,
            cool_after_loading: bool = True,
            # ablation: bool = True,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            max_time: float = -1.0,
            num_releases: int = -1,
            detection_window: float = -1.0,
            detection_delay: float = 0.0,
            ion_absence_threshold: float = -1.0
    ) -> None:
        """Load ions.

        :param num_ions: Number of ions to load (zero to load without an ion limit)
        :param strict: Load exactly the desired number of ions, not more
        :param cool_after_loading: :const:`True` to keep cooling enabled after loading
        :param ablation: Enable ablation laser
        :param buffer_size: Buffer size
        :param max_time: Maximum loading time before aborting
        :param num_releases: Maximum number of times to release when using strict loading
        :param detection_window: The duration of a detection window
        :param detection_delay: The pause duration between detection windows
        :param ion_absence_threshold: Threshold frequency for ion presence/absence in Hz
        :raises IonLoadError: Raised if the desired number of ions could not be loaded
        :raises ValueError: Raised if any of the parameters is invalid
        """
        # Load default values
        if max_time <= 0 * s:
            max_time = self._load_max_time
        if num_releases < 0:
            num_releases = self._load_num_releases
        if detection_window <= 0 * s:
            detection_window = self._load_detection_window
        if ion_absence_threshold < 0 * Hz:
            ion_absence_threshold = self._ion_absence_threshold

        # Check parameters
        assert isinstance(num_ions, (int, np.integer)) and 0 <= num_ions <= self._detection.NUM_CHANNELS()
        assert isinstance(strict, bool)
        assert isinstance(cool_after_loading, bool)
        # assert isinstance(ablation, bool)
        assert isinstance(buffer_size, int) and 0 <= buffer_size <= 32
        assert isinstance(max_time, float) and max_time > 0 * s
        assert isinstance(num_releases, (int, np.integer)) and num_releases >= 0
        assert isinstance(detection_window, float) and detection_window > 0 * s
        assert isinstance(detection_delay, float) and detection_delay >= 0 * s
        assert isinstance(ion_absence_threshold, float) and ion_absence_threshold > 0 * Hz

        if num_ions == 0:
            # Manual loading
            self.logger.warning('Manual loading enabled')
            num_ions = self._MANUAL_LOAD

        # Casts, conversions, and limits
        num_ions = np.int32(num_ions)
        num_releases = np.int32(num_releases)
        max_time_mu = self.core.seconds_to_mu(max_time)
        detection_delay_mu = np.int64(max(self.core.seconds_to_mu(detection_delay), self.core.ref_multiplier))

        # Initial assumption is that there are no ions
        current_num_ions = 0

        # Clear plot
        self.clear_counts_plot()

        while max_time_mu > 0 and current_num_ions < num_ions:
            if self._scheduler.check_pause():
                # Pause the experiment
                self.logger.debug('Pausing ion loading process')
                self.core.comm.close()
                try:
                    self._scheduler.pause()
                except TerminationRequested:
                    self.logger.warning('Ion loading process aborted by user')
                    raise

            # TODO: detune/set beatnote lock

            # Do the actual loading in a kernel
            self.logger.info('Attempting to load ions...')
            current_num_ions, max_time_mu = self._load_ions(
                num_ions=num_ions,
                buffer_size=buffer_size,
                max_time_mu=max_time_mu,
                cool_after_loading=cool_after_loading,
                detection_window=detection_window,
                detection_delay_mu=detection_delay_mu,
                ion_absence_threshold=ion_absence_threshold
            )

            # Log messages
            if max_time_mu <= 0:
                self.logger.warning('Loading aborted due to timeout')
            self.logger.info(f'{current_num_ions} ion(s) loaded')

            # Update the number of ions
            self._update_num_ions(current_num_ions)

            # TODO: at some point, wait and reset beatnote lock

            if num_ions != self._MANUAL_LOAD and strict and current_num_ions > num_ions:
                self.logger.error('Overloaded ions but release ions functionality not implemented')
                break

        if num_ions != self._MANUAL_LOAD:
            if current_num_ions < num_ions:
                # Raise an exception if we did not load enough ions
                raise IonLoadError(f'Could not load requested number of ions: '
                                   f'{current_num_ions} out of {num_ions} ion(s) loaded')
            if strict and current_num_ions != num_ions:
                # Raise an exception if we did not load the exact number of ions
                raise IonLoadError(f'Could not strictly load requested number of ions: '
                                   f'{current_num_ions} ion(s) loaded instead of {num_ions} ion(s)')

    @kernel
    def _load_ions(
            self,
            num_ions: TInt32,
            buffer_size: TInt32,
            max_time_mu: TInt64,
            cool_after_loading: TBool,
            detection_window: TFloat,
            detection_delay_mu: TInt64,
            ion_absence_threshold: TFloat
    ) -> TTuple([TInt32, TInt64]):
        """Kernel for loading ions.

        Note: This method does NOT guarantee any checks on input parameters, the caller is responsible.
        """

        # Reset core
        self.core.reset()

        # Early check to see if we already have enough ions before loading
        self._detection.detect_all(detection_window)
        current_num_ions = self._get_num_ions(detection_window, ion_absence_threshold)
        if current_num_ions >= num_ions:
            return current_num_ions, max_time_mu

        # Store timestamps
        t_start = now_mu()
        t_stop = t_start + max_time_mu

        # Guarantee slack
        self.core.break_realtime()

        # Loading procedure
        try:
            # Switch lasers
            self._cool_prep.cool.set_state(state=True)
            # Todo: Add Ionization
            self._l355.set_shutter(True)
            # self._carrier.on()

            with self._ablation:
                self._ablation.on()
                current_num_ions = num_ions
                # self._load_ions_loop(
                #     num_ions=num_ions,
                #     buffer_size=buffer_size,
                #     detection_window=detection_window,
                #     detection_delay_mu=detection_delay_mu,
                #     ion_absence_threshold=ion_absence_threshold,
                #     t_stop=t_stop,
                #     current_num_ions=current_num_ions,
                # )
                self._ablation.off()

            # Store actual stop timestamp
            t_stop = now_mu()

        finally:
            # Gain slack
            self.core.break_realtime()

            # Switch lasers
            # Todo: Turn off ionization
            self._l355.set_shutter(False)
            # self._carrier.off()

            self._cool_prep.cool.set_state(state=True)

            # Sync
            self.core.wait_until_mu(now_mu())

        # Subtract time spent of the max time
        max_time_mu -= t_stop - t_start
        # Return the current number of ions and the leftover time for further processing
        return current_num_ions, max_time_mu

    @kernel
    def _load_ions_loop(
            self,
            num_ions: TInt32,
            buffer_size: TInt32,
            detection_window: TFloat,
            detection_delay_mu: TInt64,
            ion_absence_threshold: TFloat,
            t_stop: TInt64,
            current_num_ions: TInt32,
    ) -> TInt32:
        # Guarantee slack
        self.core.break_realtime()

        detection_window_mu = self.core.seconds_to_mu(detection_window)

        # Build up a buffer
        for _ in range(buffer_size):
            delay_mu(detection_delay_mu)
            self._detection.detect_all_mu(duration=detection_window_mu,
                                          mode=MODES370.NONE, trigger_shutter=False)

        while current_num_ions < num_ions and now_mu() < t_stop and not self._scheduler.check_pause():
            # Detect and obtain the number of loaded ions
            delay_mu(detection_delay_mu)
            self._detection.detect_all_mu(
                detection_window_mu, mode=MODES370.NONE, trigger_shutter=False)
            current_num_ions = self._get_num_ions(detection_window, ion_absence_threshold)

        # Empty buffers
        for _ in range(buffer_size):
            current_num_ions = self._get_num_ions(detection_window, ion_absence_threshold)

        # Return the number of ions
        return current_num_ions

    @kernel
    def _isqrt(self, n: TInt32) -> TTuple([TInt32, TInt32]):
        """Use Newton's method to calculate the integer square root of n
        The iterative formula is root=0.5*(X+N/X) where X is the guess root"""

        x = n
        # Initial guess4
        y = (x + 1) // 2
        count = 0
        while y < x:
            count += 1
            x = y
            # Newton's method
            y = (x + n // x) // 2
        return x, count

    @kernel(flags='fast-math')
    def _get_num_ions(self, detection_window: TFloat, ion_absence_threshold: TFloat) -> TInt32:
        """Calculate the number of ions from the last PMT counts."""

        # Get the PMT counts and plot them
        counts = [self._detection.count(channel) for channel in range(self._detection.NUM_CHANNELS())]
        self._plot_counts(counts, detection_window)

        # Form an array of PMT input frequencies
        pmt_vec = np.array(counts, dtype=np.int32) // detection_window

        # Check if any signal meets the threshold
        for input_freq in pmt_vec:
            if input_freq >= ion_absence_threshold:
                break
        else:
            # No signal meets the threshold, there are no ions
            return 0

        # Normalize the data
        sum_sq = 0.0
        for input_freq in pmt_vec:
            sum_sq += input_freq ** 2
        x, count = self._isqrt(np.int32(sum_sq // 10000))
        pmt_norm = pmt_vec // x

        # Reference matrix
        ref_matrix = np.array([
            [0, 100, 0],
            [30, 60, 30],
            [50, 50, 50]
        ], dtype=np.int32)

        # Find the maximum dot product between observed signals and reference matrix
        result = ref_matrix @ np.transpose(pmt_norm)
        max_index = 0
        max_val = 0.0
        for i in range(len(result)):
            if result[i] > max_val:
                max_index = i
                max_val = result[i]
        current_num_ions = max_index + 1  # Correct indexing

        # Return, no slack is left because of count() functions
        return current_num_ions

    @rpc(flags={'async'})
    def _plot_counts(self, counts, detection_window):
        data = [c / detection_window / self.COUNT_PLOT_Y_SCALE for c in counts]
        self.append_to_dataset(self.COUNT_PLOT_KEY, data)

    @host_only
    def _update_num_ions(self, num_ions: int) -> None:
        # Todo: delete
        num_ions = 1
        active_channels = [
            [],
            [0],
            [0, 1],
            [0, 1, 2]
        ][num_ions]

        # Store the number of ions
        self._yb171.set_num_ions(num_ions)
        # Store the active channels
        self._detection.set_active_channels(active_channels)

    @kernel
    def get_num_ions(self, detection_window: TFloat = -1.0, ion_absence_threshold: TFloat = -1.0) -> TInt32:
        """Perform a detection and get the current number of ions.

        This function does not update any datasets and instead just returns the current number of ions detected.
        The caller is responsible for slack at the start of this function.
        When this function returns, no slack is left.

        :param detection_window: The duration of a detection window
        :param ion_absence_threshold: Threshold frequency for ion presence/absence in Hz
        :return The current number of ions
        """

        # Load default values
        if detection_window <= 0 * s:
            detection_window = self._load_detection_window
        if ion_absence_threshold < 0 * Hz:
            ion_absence_threshold = self._ion_absence_threshold

        # Detect
        self._detection.detect_all(detection_window)
        # Return number of ions
        return self._get_num_ions(detection_window=detection_window, ion_absence_threshold=ion_absence_threshold)

    """Plotting functions."""

    @rpc(flags={'async'})
    def plot_counts(self, **kwargs):  # type: (typing.Any) -> None
        """Plot PMT counts during loading.

        :param kwargs: Extra keyword arguments for the plot
        """
        # Set defaults
        kwargs.setdefault('title', f'RID {self._scheduler.rid}')
        for k, v in self.COUNT_PLOT_DEFAULT_KWARGS.items():
            kwargs.setdefault(k, v)

        # Plot
        self._ccb.plot_xy_multi(self.COUNT_PLOT_NAME, self.COUNT_PLOT_KEY, group=self.PLOT_GROUP, **kwargs)

    @rpc(flags={'async'})
    def clear_counts_plot(self):  # type: () -> None
        """Clear the counts plot."""
        self.set_dataset(self.COUNT_PLOT_KEY, [], broadcast=True, archive=False)

    @rpc(flags={'async'})
    def disable_counts_plot(self):  # type: () -> None
        """Close the counts plot."""
        self._ccb.disable_applet(self.COUNT_PLOT_NAME, self.PLOT_GROUP)
