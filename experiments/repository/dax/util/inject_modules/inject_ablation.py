from artiq.experiment import *

from demo_system.system import DemoSystem

import time


class InjectAblation(DemoSystem, EnvExperiment):
    """Inject Ablation"""

    kernel_invariants = {"ablation_state", "ablation_time", "pre_delay", "post_delay"}

    def build(self):
        # Get Devices
        super(InjectAblation, self).build()

        # Mirror Set
        self.ablation_state = self.get_argument(
            "Ablation State",
            processor=BooleanValue(True),
            group="Ablation",
            tooltip="Sets the Ablation State",
        )

        self.ablation_time = self.get_argument(
            "Ablation On Time",
            processor=NumberValue(10 * s, "s", min=0.0),
            group="Ablation",
            tooltip="Sets the Ablation On Time",
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

    def prepare(self):
        pass

    def run(self):
        self.dax_init()
        self.inject_ablation()

    @host_only
    def inject_ablation(self):
        # Time counter used to check for termination requests
        time_counter = 0 * s
        time_delay = 100 * ms

        if self.ablation_state:
            with self.ablation:
                self.ablation.on()
                while time_counter < self.ablation_time:
                    # Pause to check for termination requests
                    self.scheduler.pause()
                    time.sleep(time_delay)
                    time_counter += time_delay
        else:
            self.ablation.off()
