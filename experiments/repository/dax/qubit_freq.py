import numpy as np
from scipy.optimize import curve_fit

from dax.util.units import freq_to_str

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
from demo_system.util.functions import gaussian

from user import user_id

class MicrowaveQubitFreqGateScan(GateScan, Experiment):
    """Microwave qubit frequency"""

    MW_GATE_FREQ_KEY = "mw_gate_freq"

    DEFAULT_SPAN = 0.02 * MHz
    user_id = str(user_id)

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.MW_GATE_FREQ_KEY,
            "Microwave gate frequency",
            Scannable(
                [
                    RangeScan(
                        self.microwave.fetch_qubit_freq() - self.DEFAULT_SPAN / 2,
                        self.microwave.fetch_qubit_freq() + self.DEFAULT_SPAN / 2,
                        10,
                    )
                ],
                global_min=0 * MHz,
                global_max=400 * MHz,
                ndecimals=12,
                unit="MHz",
            ),
        )

        # Add regular arguments
        self.mw_gate_duration = self.get_argument(
            "Microwave gate duration",
            NumberValue(
                200 * us,
                min=0 * us,
                unit="us",
                ndecimals=3,
            ),
            tooltip="Refresh to calculate the pi rotation gate duration based on the latest microwave Rabi frequency",
        )
        self.update_dataset = self.get_argument(
            "Update dataset",
            BooleanValue(False),
            tooltip="Store calibrated values in system datasets",
        )
        self.update_kernel_invariants("mw_gate_duration")

    @kernel
    def gate_config(self, point, index):
        # Todo: Remove this because doing weird stuff with dax_init
        self.microwave.config_freq(point.mw_gate_freq)

    @kernel
    def gate_action(self, point, index):
        self.microwave.pulse(self.mw_gate_duration)

    def host_exit(self) -> None:
        """Calibrate microwave qubit frequency."""
        # Obtain x data
        scannables = self.get_scannables()
        freq = np.asarray(scannables[self.MW_GATE_FREQ_KEY])

        # Get probability
        prob = np.asarray(
            self.state.histogram.get_probabilities()[0]
        )  # active channel 0

        # Fit
        (peak, mw_qubit_freq, c), _ = curve_fit(
            gaussian,
            freq,
            prob,
            p0=[np.max(prob), self.microwave.DEFAULT_QUBIT_FREQ, 10 * kHz],
            bounds=([0.0, 0 * MHz, 0 * kHz], [1.0, np.inf, np.inf]),
        )
        self.logger.info(
            f"Calculated microwave qubit frequency: {freq_to_str(mw_qubit_freq)}"
        )
        fit = gaussian(freq, peak, mw_qubit_freq, c)
        self.plot_fit_single(fit)

        if self.update_dataset:
            # Update dataset
            self.microwave.store_qubit_freq(mw_qubit_freq)
