import numpy as np
from scipy.optimize import curve_fit

from dax.util.units import freq_to_str

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
from demo_system.util.functions import (
    get_sample_interval,
    find_oscillation_freq,
    rabi_oscillation_on_resonance,
)


class MicrowaveQubitTimeGateScan(GateScan, Experiment):
    """Microwave qubit time"""

    MW_GATE_TIME_KEY = "mw_gate_time"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.MW_GATE_TIME_KEY,
            "Microwave gate time",
            Scannable(
                [
                    RangeScan(1 * us, 200 * us, 200),
                    NoScan(100 * us),
                ],
                global_min=0 * us,
                unit="us",
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
        self.update_dataset = self.get_argument(
            "Update dataset",
            BooleanValue(True),
            tooltip="Store calibrated values in system datasets",
        )
        self.update_kernel_invariants("mw_freq")

    @kernel
    def gate_setup(self):
        self.microwave.config_freq(self.mw_freq)

    @kernel
    def gate_action(self, point, index):
        self.microwave.pulse(point.mw_gate_time)

    def host_exit(self) -> None:
        """Calibrate microwave Rabi frequency."""

        # Obtain x data
        scannables = self.get_scannables()
        time = np.asarray(scannables[self.MW_GATE_TIME_KEY])

        # Get probability
        prob = np.asarray(
            self.state.histogram.get_probabilities()[0]
        )  # active channel 0

        # Initial guess
        try:
            # initial_freq_guess = self.microwave.rabi_freq()
            time_step = get_sample_interval(time)
            initial_freq_guess = find_oscillation_freq(prob, time_step)
            self.logger.info(
                f"FFT analysis found modulation peak of {freq_to_str(initial_freq_guess)}"
            )
        except AttributeError:
            time_step = get_sample_interval(time)
            initial_freq_guess = find_oscillation_freq(prob, time_step)
            self.logger.info(
                f"FFT analysis found modulation peak of {freq_to_str(initial_freq_guess)}"
            )

        # Fit
        (mw_rabi_freq,), _ = curve_fit(
            rabi_oscillation_on_resonance,
            time,
            prob,
            p0=[initial_freq_guess],
            bounds=(0 * MHz, np.inf),
        )
        self.logger.info(
            f"Calculated microwave Rabi frequency: {freq_to_str(mw_rabi_freq)}"
        )
        fit = rabi_oscillation_on_resonance(time, mw_rabi_freq)
        self.plot_fit_single(fit)

        if self.update_dataset:
            # Update dataset
            self.microwave.store_rabi_freq(mw_rabi_freq)
