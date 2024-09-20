# import numpy as np
# from scipy.optimize import curve_fit
# from dax.util.units import freq_to_str

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
# from demo_system.util.functions import (get_sample_interval)


class PumpScan(GateScan, Experiment):
    """Ideal pump time"""

    PUMP_TIME_KEY = "pump_time"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.PUMP_TIME_KEY,
            "Pump time",
            Scannable(
                [

                    RangeScan(
                        0.1 * us,
                        10 * ms,
                        100,
                    )
                ],
                global_min=0 * us,
                unit="us",
            ),
        )

    def initialize(self):
        pass

    @kernel
    def gate_action(self, point, index):
        self.core.break_realtime()
        self.cool_prep.prep.pulse(point.pump_time)
