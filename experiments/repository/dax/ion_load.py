import logging

from demo_system.system import *


class IonLoad(DemoSystem, Experiment):
    """Ion load"""

    def build(self):
        # Call super
        super(IonLoad, self).build()

        # Add general arguments
        self._num_ions = self.get_argument(
            "Number of ions",
            NumberValue(1, min=1, max=self.pmt.NUM_CHANNELS, step=1, ndecimals=0),
            tooltip="Use 0 for manual loading",
        )
        self._max_time = self.get_argument(
            "Maximum loading time",
            NumberValue(600 * s, min=0 * s, step=10 * s, unit="s"),
            tooltip="Abort procedure if maximum loading time is exceeded (0 for default)",
        )
        self._strict = self.get_argument(
            "Strict",
            BooleanValue(False),
            tooltip="Load exactly the desired number of ions, not more",
        )
        # self._ablation = self.get_argument(
        #     'Ablation',
        #     BooleanValue(True),
        #     tooltip='Use the ablation laser while loading'
        # )
        self._num_releases = self.get_argument(
            "Number of releases",
            NumberValue(10, min=-1, step=1, ndecimals=0),
            tooltip="Only relevant if `strict` is enabled (-1 for default)",
        )

        self._detection_window = self.get_argument(
            "Detection window",
            NumberValue(100 * ms, min=0 * ms, step=10 * ms, unit="ms"),
            tooltip="Detection window duration (0 for default)",
            group="PMT",
        )
        self._detection_delay = self.get_argument(
            "Detection delay",
            NumberValue(0 * ms, min=0 * ms, step=1 * ms, unit="ms"),
            tooltip="Pause duration between detection windows",
            group="PMT",
        )
        self._ion_absence_threshold = self.get_argument(
            "Ion absence threshold",
            NumberValue(5 * kHz, min=-1 * kHz, step=1 * kHz, unit="kHz"),
            tooltip="Ion absence threshold (-1 for default)",
            group="PMT",
        )

        self._buffer_size = self.get_argument(
            "Buffer size",
            NumberValue(
                self.ion_load.DEFAULT_BUFFER_SIZE, min=0, max=32, step=1, ndecimals=0
            ),
            group="Advanced",
        )
        self._cool_after_loading = self.get_argument(
            "Cool after loading", BooleanValue(True), group="Advanced"
        )

        self._plot = self.get_argument(
            "Plot PMT counts", BooleanValue(True), group="Plot"
        )
        self._close_plot = self.get_argument(
            "Close plots automatically", BooleanValue(True), group="Plot"
        )

    def prepare(self):
        # Adjust logging level
        self.ion_load.logger.setLevel(
            min(self.logger.getEffectiveLevel(), logging.INFO)
        )
        self.ion_load._update_num_ions(1)

    def run(self):
        # Call DAX init
        self.dax_init()

        if self._plot:
            self.ion_load.clear_counts_plot()  # Clear plot early for a better visual experience
            self.ion_load.plot_counts()

        try:
            # Call the ion load service
            self.ion_load.load_ions(
                num_ions=self._num_ions,
                strict=self._strict,
                cool_after_loading=self._cool_after_loading,
                # ablation=self._ablation,
                buffer_size=self._buffer_size,
                max_time=self._max_time,
                num_releases=self._num_releases,
                detection_window=self._detection_window,
                detection_delay=self._detection_delay,
                ion_absence_threshold=self._ion_absence_threshold,
            )
        except TerminationRequested:
            pass  # Messaging handled at service level

        self.idle()  # set system to default state

        if self._close_plot:
            self.ion_load.disable_counts_plot()
