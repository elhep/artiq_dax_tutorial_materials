import numpy as np
from scipy.optimize import curve_fit

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
from demo_system.util.functions import gaussian

from dax.util.units import freq_to_str, time_to_str
from dax.util.sub_experiment import SubExperiment


class MicrowaveRamseyFreqCalibration(GateScan, Experiment):
    """Microwave Ramsey frequency calibration"""

    MW_GATE_FREQ_KEY = "mw_gate_freq"

    MW_GATE_FREQ_LABEL = "Microwave gate frequency"
    RAMSEY_DELAY_TIME_LABEL = "Ramsey delay time"
    UPDATE_DATASET_LABEL = "Update dataset"

    DEFAULT_SPAN = 0.001 * MHz

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.MW_GATE_FREQ_KEY,
            self.MW_GATE_FREQ_LABEL,
            Scannable(
                [
                    CenterScan(
                        self.microwave.fetch_qubit_freq(),
                        self.DEFAULT_SPAN,
                        self.DEFAULT_SPAN / 100,
                    ),
                    RangeScan(
                        self.microwave.fetch_qubit_freq() - self.DEFAULT_SPAN / 2,
                        self.microwave.fetch_qubit_freq() + self.DEFAULT_SPAN / 2,
                        100,
                    ),
                    NoScan(self.microwave.fetch_qubit_freq()),
                ],
                global_min=0 * MHz,
                global_step=1 * kHz,
                ndecimals=12,
                unit="MHz",
            ),
        )

        # Add regular arguments
        self.ramsey_delay_time = self.get_argument(
            self.RAMSEY_DELAY_TIME_LABEL,
            NumberValue(10 * ms, min=0 * ms, step=10 * ms, unit="ms"),
        )
        self.update_dataset = self.get_argument(
            self.UPDATE_DATASET_LABEL,
            BooleanValue(True),
            tooltip="Store calibrated values in system datasets",
        )
        self.update_kernel_invariants("ramsey_delay_time")

    def host_enter(self) -> None:
        # Call super
        super(MicrowaveRamseyFreqCalibration, self).host_enter()

        # Clear the fit data (useful when this experiment is used as a sub-experiment)
        self.clear_fit()

    @kernel
    def gate_pre_action(self, point, index):
        # Set microwave frequency and reset phase
        self.microwave.config_freq(point.mw_gate_freq)
        self.microwave.config_phase(0.0)

    @kernel
    def gate_action(self, point, index):
        # Perform gate
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())
        delay(self.ramsey_delay_time)
        self.microwave.pulse(0.25 / self.microwave.rabi_freq())

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
            p0=[
                np.max(prob),
                self.microwave.DEFAULT_QUBIT_FREQ,
                1.0 / self.ramsey_delay_time,
            ],
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


class MicrowaveRamseyFreqCalibrationIter(DemoSystem, Experiment):
    """Ramsey Frequency Scan - Iterator"""

    def __init__(self, managers, *args, **kwargs):
        # Capture the managers before passing them to super
        self._managers = managers
        super(MicrowaveRamseyFreqCalibrationIter, self).__init__(
            managers, *args, **kwargs
        )

    def build(self):
        # Call super
        super(MicrowaveRamseyFreqCalibrationIter, self).build()

        # Arguments
        self.num_iterations = self.get_argument(
            "Iterations",
            NumberValue(2, min=1, step=1, ndecimals=0),
            tooltip="Number of Ramsey calibration iterations",
        )

        # Span
        self.span = self.get_argument(
            "Initial span",
            NumberValue(1 * kHz, unit="kHz", min=0.01 * kHz),
            tooltip="Initial value for CenterScan span",
        )
        self.span_sf = self.get_argument(
            "Span scale factor",
            NumberValue(0.1, min=0.01),
            tooltip="Span scaling factor for each iteration",
        )

        # Step
        self.step = self.get_argument(
            "Initial step",
            NumberValue(50 * Hz, unit="Hz", min=0.01 * Hz),
            tooltip="Initial value for CenterScan step",
        )
        self.step_sf = self.get_argument(
            "Step scale factor",
            NumberValue(0.1, min=0.01),
            tooltip="Step scaling factor for each iteration",
        )

        # Ramsey time
        self.ramsey_time = self.get_argument(
            "Initial Ramsey delay time",
            NumberValue(1.0 * ms, unit="ms", min=0.01 * ms),
            tooltip="Initial value for Ramsey delay time",
        )
        self.ramsey_time_sf = self.get_argument(
            "Ramsey delay time scale factor",
            NumberValue(10.0, min=0.01),
            tooltip="Ramsey delay time scaling factor for each iteration",
        )

    def run(self):
        # Get a sub-experiment runner
        sub_experiment = SubExperiment(self, self._managers)

        for i in range(self.num_iterations):
            # Get the latest microwave qubit frequency
            mw_qubit_frequency = self.microwave.fetch_qubit_freq()

            # Report values
            self.logger.info(
                f"Iteration {i + 1}, MW qubit freq = {freq_to_str(mw_qubit_frequency, precision=12)}"
            )
            self.logger.info(
                f"span={freq_to_str(self.span)}, "
                f"step={freq_to_str(self.step)}, "
                f"ramsey_time={time_to_str(self.ramsey_time)}"
            )

            # Assemble experiment arguments
            arguments = {
                MicrowaveRamseyFreqCalibration.MW_GATE_FREQ_LABEL: CenterScan(
                    mw_qubit_frequency, self.span, self.step
                ),
                MicrowaveRamseyFreqCalibration.RAMSEY_DELAY_TIME_LABEL: self.ramsey_time,
                MicrowaveRamseyFreqCalibration.UPDATE_DATASET_LABEL: True,
            }

            # Run the sub-experiment
            sub_experiment.run(
                MicrowaveRamseyFreqCalibration,
                "mw_ramsey_freq_calibration",
                arguments=arguments,
            )

            # Update values
            self.span *= self.span_sf
            self.step *= self.step_sf
            self.ramsey_time *= self.ramsey_time_sf
