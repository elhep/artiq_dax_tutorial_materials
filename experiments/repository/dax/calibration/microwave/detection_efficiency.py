from demo_system.system import *
from demo_system.templates.gate_scan import GateScan


class DetectionEfficiency(GateScan, Experiment):
    """Detection efficiency"""

    DELAY_TIME_KEY = "delay_time"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.DELAY_TIME_KEY,
            "Delay time",
            Scannable(
                [
                    RangeScan(0 * ms, 100 * ms, 100),
                    NoScan(10 * ms),
                ],
                global_min=0 * ms,
                global_step=1 * ms,
                unit="ms",
            ),
        )

        # Add regular arguments
        self.mw_freq = self.get_argument(
            "Microwave gate frequency",
            NumberValue(
                self.microwave.fetch_qubit_freq(),
                min=0 * MHz,
                max=400 * MHz,
                unit="MHz",
                ndecimals=12,
            ),
            tooltip="Refresh to set to latest microwave qubit frequency",
        )
        self.update_kernel_invariants("mw_freq")

    @kernel
    def gate_setup(self):
        self.microwave.config_freq(self.mw_freq)

    @kernel
    def gate_action(self, point, index):
        # Perform gate
        self.microwave.pulse(0.5 / self.microwave.rabi_freq())
        delay(point.delay_time)
