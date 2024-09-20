import numpy as np
from scipy.stats import linregress

from dax.util.units import freq_to_str
from dax.util.sub_experiment import SubExperiment

from demo_system.system import *
from demo_system.templates.gate_scan import GateScan
from demo_system.util.functions import linear


class MicrowaveGateRepeatScan(GateScan, Experiment):
    """Microwave gate repeat scan"""

    MW_GATE_TIME_KEY = "mw_gate_time"

    MW_GATE_TIME_LABEL = "Microwave gate time"
    NUM_GATES_LABEL = "Number of gates"
    MW_GATE_FREQ_LABEL = "Microwave gate frequency"
    UPDATE_DATASET_LABEL = "Update dataset"

    def build_gate_scan(self):
        # Add scans
        self.add_scan(
            self.MW_GATE_TIME_KEY,
            self.MW_GATE_TIME_LABEL,
            Scannable(
                [
                    CenterScan(
                        self.microwave.fetch_pi_time(),
                        50 * us,
                        1 * us,
                    ),
                    RangeScan(0 * us, 200 * us, 200),
                    NoScan(100 * us),
                ],
                global_min=0 * us,
                ndecimals=3,
                unit="us",
            ),
        )

        # Add regular arguments
        self.num_gates = self.get_argument(
            self.NUM_GATES_LABEL,
            NumberValue(10, min=0, step=1, ndecimals=0),
            tooltip="Number of gates (i.e. pi rotations) to execute, pi/2 rotation will be appended",
        )
        self.mw_freq = self.get_argument(
            self.MW_GATE_FREQ_LABEL,
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
            self.UPDATE_DATASET_LABEL,
            BooleanValue(True),
            tooltip="Store calibrated values in system datasets",
        )
        self.update_kernel_invariants("num_gates", "mw_freq")

    def host_enter(self) -> None:
        # Call super
        super(MicrowaveGateRepeatScan, self).host_enter()

        # Clear the fit data (useful when this experiment is used as a sub-experiment)
        self.clear_fit()

    @kernel
    def gate_setup(self):
        # Set microwave frequency and reset phase
        self.microwave.config_freq(self.mw_freq)
        self.microwave.config_phase(0.0)

    @kernel
    def gate_action(self, point, index):
        # Perform repeated gates
        for _ in range(self.num_gates):
            self.microwave.pulse(point.mw_gate_time)
        self.microwave.pulse(point.mw_gate_time / 2.0)

    def host_exit(self) -> None:
        """Calibrate microwave Rabi frequency."""

        # Obtain x data
        scannables = self.get_scannables()
        time = np.asarray(scannables[self.MW_GATE_TIME_KEY])

        # Get probability
        prob = np.asarray(
            self.state.histogram.get_probabilities()[0]
        )  # active channel 0

        # Fit (linear regression)
        slope, intercept, _, _, _ = linregress(time, prob)
        if slope != 0:
            rabi_freq = 1 / (2 * ((0.5 - intercept) / slope))
        else:
            rabi_freq = self.microwave.fetch_rabi_freq()
        self.logger.info(
            f"Calculated microwave Rabi frequency: {freq_to_str(rabi_freq)}"
        )
        fit = linear(time, slope, intercept)
        self.plot_fit_single(fit)

        if self.update_dataset:
            # Update dataset
            self.microwave.store_rabi_freq(rabi_freq)


class MicrowaveGateRepeatScanIter(DemoSystem, Experiment):
    """Microwave gate repeat scan - Iterator"""

    def __init__(self, managers, *args, **kwargs):
        # Capture the managers before passing them to super
        self._managers = managers
        super(MicrowaveGateRepeatScanIter, self).__init__(managers, *args, **kwargs)

    def build(self):
        # Call super
        super(MicrowaveGateRepeatScanIter, self).build()

        # Arguments
        self.num_iterations = self.get_argument(
            "Iterations",
            NumberValue(2, min=1, step=1, ndecimals=0),
            tooltip="Number of gate repeat scan iterations",
        )

        # Span
        self.span = self.get_argument(
            "Initial span",
            NumberValue(5 * us, unit="us", min=1 * us),
            tooltip="Initial value for CenterScan span",
        )
        self.span_sf = self.get_argument(
            "Span scale factor",
            NumberValue(0.5, min=0.01),
            tooltip="Span scaling factor for each iteration",
        )

        # Step
        self.step = self.get_argument(
            "Initial step",
            NumberValue(0.2 * us, unit="us", min=0.1 * us, ndecimals=3),
            tooltip="Initial value for CenterScan step",
        )
        self.step_sf = self.get_argument(
            "Step scale factor",
            NumberValue(0.5, min=0.01),
            tooltip="Step scaling factor for each iteration",
        )

        # Number of gates
        self.num_gates = self.get_argument(
            "Initial number of gates",
            NumberValue(10, min=1, step=1, ndecimals=0),
            tooltip="Initial value for number of gates",
        )
        self.num_gates_sf = self.get_argument(
            "Number of gates scale factor",
            NumberValue(2.0, min=1.0),
            tooltip="Number of gates scaling factor for each iteration",
        )

    def run(self):
        # Get a sub-experiment runner
        sub_experiment = SubExperiment(self, self._managers)

        for i in range(self.num_iterations):
            # Report values
            self.logger.info(
                f"Iteration {i + 1}, "
                f"MW Rabi freq = {freq_to_str(self.microwave.fetch_rabi_freq(), precision=9)}"
            )
            self.logger.info(
                f"span={freq_to_str(self.span)}, "
                f"step={freq_to_str(self.step)}, "
                f"num_gates={self.num_gates}"
            )

            # Assemble experiment arguments
            arguments = {
                MicrowaveGateRepeatScan.MW_GATE_TIME_LABEL: CenterScan(
                    self.microwave.pi_time(), self.span, self.step
                ),
                MicrowaveGateRepeatScan.NUM_GATES_LABEL: self.num_gates,
                MicrowaveGateRepeatScan.MW_GATE_FREQ_LABEL: self.microwave.fetch_qubit_freq(),
                MicrowaveGateRepeatScan.UPDATE_DATASET_LABEL: True,
            }

            # Run the sub-experiment
            sub_experiment.run(
                MicrowaveGateRepeatScan, "mw_gate_repeat_scan", arguments=arguments
            )

            # Update values
            self.span *= self.span_sf
            self.step *= self.step_sf
            self.num_gates *= self.num_gates_sf
