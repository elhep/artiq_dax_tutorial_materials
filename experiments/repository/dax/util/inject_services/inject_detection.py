from artiq.experiment import *

from demo_system.system import DemoSystem


class InjectDetection(DemoSystem, EnvExperiment):
    """Inject Detection"""

    _group = "Detection"

    def build(self):
        # Get Devices
        super(InjectDetection, self).build()

        # Detection
        self.detection_window = self.get_argument(
            "Detection Window",
            processor=NumberValue(100 * ms, "ms", min=0 * ms),
            group=self._group,
            tooltip="Set detection window",
        )

        self.mode = self.get_argument(
            "370 Mode",
            processor=EnumerationValue(self.l370.MODES.modes_list_str, "Cool"),
            group=self._group,
            tooltip="370 Mode",
        )

        self.do_pump = self.get_argument(
            "Do Pump",
            processor=BooleanValue(False),
            group=self._group,
            tooltip="Enable pump/init",
        )

        self.pump_time = self.get_argument(
            "Pump Time",
            processor=NumberValue(100 * ms, "ms", min=0 * ms),
            group=self._group,
            tooltip="Set pump time",
        )

        # Timing arguments
        self.pre_delay = self.get_argument(
            "Pre-delay time",
            processor=NumberValue(10 * ms, "ms", step=1 * ms, min=0 * ms),
            group="Delays",
            tooltip="Wait time before configuring the device",
        )
        self.post_delay = self.get_argument(
            "Post-delay time",
            processor=NumberValue(0 * s, "s", step=1 * s, min=0 * s),
            group="Delays",
            tooltip="Wait time after the device is configured",
        )

        self.update_kernel_invariants("detection_window", "do_pump", "pump_time", "mode", "pre_delay", "post_delay")

    def prepare(self):
        self.dax_init()
        self.l370_mode = self.l370.MODES.modes_list_str.index(self.mode)
        pass

    @kernel
    def run(self):
        # Reset the core
        self.core.reset()

        # Pre-delay
        delay(self.pre_delay)

        self.inject_detection()

        # Post-wait time
        delay(self.post_delay)
        self.idle()
        self.core.wait_until_mu(now_mu())

    @kernel
    def inject_detection(self):
        self.core.break_realtime()

        if self.do_pump:
            self.cool_prep.prep.pulse(self.pump_time)

        self.detection.detect_all(self.detection_window, mode=self.l370_mode)

        counts = [self.detection.count(c) for c in range(self.detection.NUM_CHANNELS())]
        self.logger.info("Counts: %s", counts)

        self.core.break_realtime()
