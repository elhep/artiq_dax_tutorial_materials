from demo_system.system import *
from demo_system.templates.gate_scan import GateScan


class MicrowaveRamseyInfiniteScan(GateScan, Experiment):
    """Microwave Ramsey infinite scan"""

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            'n_repeat',
            "N Repeats",
            Scannable(
                [
                    RangeScan(0, 1, 10000),
                ],
                global_min=0
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
        self.ramsey_delay_time = self.get_argument(
            "Ramsey delay time",
            NumberValue(100 * us, min=0 * ms, step=100 * us, unit="us"),
        )
        self.update_kernel_invariants("mw_freq", 'ramsey_delay_time')

    @kernel
    def gate_setup(self):
        self.microwave.config_freq(self.mw_freq)

    @kernel
    def gate_action(self, point, index):
        # Perform gate
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())
        delay(self.ramsey_delay_time)
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())
