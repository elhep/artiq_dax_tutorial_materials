import pytest

from test.demo_system_.util.test_experiment_base import ExperimentTestBase


from repository.dax.calibration.microwave.detection_efficiency import DetectionEfficiency
from repository.dax.calibration.microwave.gate_repeat import MicrowaveGateRepeatScan
from repository.dax.calibration.microwave.qubit_freq import MicrowaveQubitFreqGateScan
from repository.dax.calibration.microwave.qubit_time import MicrowaveQubitTimeGateScan
from repository.dax.calibration.microwave.ramsey_freq import MicrowaveRamseyFreqCalibration
from repository.dax.calibration.microwave.ramsey_phase import MicrowaveRamseyPhaseCalibration
from repository.dax.calibration.microwave.ramsey_time import MicrowaveRamseyTimeCalibration
from repository.dax.calibration.microwave.spin_echo_time import MicrowaveSpinEcho

n_samples = 1


@pytest.mark.repository
class InjectModulesTestCase(ExperimentTestBase):

    def test_DetectionEfficiency(self):
        self.run_experiment(DetectionEfficiency(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveGateRepeatScan(self):
        self.run_experiment(MicrowaveGateRepeatScan(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveQubitFreqGateScan(self):
        self.run_experiment(MicrowaveQubitFreqGateScan(self.sys), {'_gate_scan_num_samples': 1})

    def test_MicrowaveQubitTimeGateScan(self):
        self.run_experiment(MicrowaveQubitTimeGateScan(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveRamseyFreqCalibration(self):
        self.run_experiment(MicrowaveRamseyFreqCalibration(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveRamseyPhaseCalibration(self):
        self.run_experiment(MicrowaveRamseyPhaseCalibration(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveRamseyTimeCalibration(self):
        self.run_experiment(MicrowaveRamseyTimeCalibration(self.sys), {'_gate_scan_num_samples': n_samples})

    def test_MicrowaveSpinEcho(self):
        self.run_experiment(MicrowaveSpinEcho(self.sys), {'_gate_scan_num_samples': n_samples})
