import numpy as np
from scipy.optimize import curve_fit

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
from demo_system.util.functions import (
    sinusoidal
)


class MicrowaveRamseyPhaseCalibration(GateScan, Experiment):
    """Microwave Ramsey phase scan"""

    PHASE_KEY = "phase"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.PHASE_KEY,
            "Phase in turns",
            Scannable(
                [
                    RangeScan(
                        0.0, 1.0, 10
                    ),  # TODO: reconsider the unit and turn until 1.0 means zero phase
                    NoScan(0.0),
                ],
                global_min=0.0,
                global_max=1.0,
            ),
            tooltip="Phase in turns [0, 1)",
        )

        # Add regular arguments
        self.ramsey_delay_time = self.get_argument(
            "Ramsey delay time",
            NumberValue(10 * ms, min=0 * ms, step=10 * ms, unit="ms"),
        )
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
        self.update_kernel_invariants("ramsey_delay_time", "mw_freq")

    @kernel
    def gate_setup(self):
        self.microwave.set_default_freq(self.mw_freq)
        self.microwave.config_freq(self.mw_freq)

    @kernel
    def gate_pre_action(self, point, index):
        # Reset the phase
        self.microwave.config_phase(0.0)

    @kernel
    def gate_action(self, point, index):
        # Perform gate
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())
        delay(self.ramsey_delay_time)
        self.microwave.config_phase(point.phase, realtime=True)
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())

    def host_exit(self) -> None:
        # Obtain phase data
        scannables = self.get_scannables()
        phase = np.asarray(scannables[self.PHASE_KEY])

        # Get probability
        prob = np.asarray(
            self.state.histogram.get_probabilities()[0]
        )  # active channel 0

        # Fit
        popt, pcov = curve_fit(
            sinusoidal,
            phase,
            prob,
            p0=[0.5, 1.0, 0.0, 0.5],
            bounds=([0.0, 0.9, -2 * np.pi, 0.0], [0.5, 1.1, 2 * np.pi, 1.0]),
        )

        # Plot fits
        fit = sinusoidal(phase, *popt)
        self.plot_fit_single(fit)

        # Print fits result
        amp = popt[0]
        offset = popt[3]
        max = amp + offset
        min = offset - amp
        self.logger.info(popt)
        self.logger.info([max, min])  # For constrast calculation
