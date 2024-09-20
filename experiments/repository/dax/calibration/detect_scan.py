# import numpy as np
# from scipy.optimize import curve_fit
# from dax.util.units import freq_to_str

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
# from demo_system.util.functions import (get_sample_interval)


class DetectScan(GateScan, Experiment):
    """Ideal detect time"""

    DETECT_TIME_KEY = "detect_time"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.DETECT_TIME_KEY,
            "Detection time",
            Scannable(
                [

                    RangeScan(
                        1 * us,
                        10 * ms,
                        100,
                    )
                ],
                global_min=0 * us,
                unit="us",
            ),
        )
        self._bright_state: bool = self.get_argument(
            "Start in Bright State?", BooleanValue(True)
        )

        self._mw_freq = self.microwave.fetch_qubit_freq()

    def detect(self):
        pass

    @kernel
    def gate_setup(self):
        self.microwave.config_freq(self._mw_freq)

    @kernel
    def gate_action(self, point, index):
        self.core.break_realtime()
        if self._bright_state:
            # self.microwave.pulse(self.microwave.pi_time())
            # self.microwave.pulse_mu()
            self.microwave.pulse()
        self.detection.detect_active(point.detect_time)
