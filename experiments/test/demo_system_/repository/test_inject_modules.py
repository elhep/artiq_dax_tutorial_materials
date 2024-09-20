import pytest

from test.demo_system_.util.test_experiment_base import ExperimentTestBase

from repository.dax.util.inject_modules.inject_ablation import InjectAblation
from repository.dax.util.inject_modules.inject_cw_laser import InjectCWLaser
from repository.dax.util.inject_modules.inject_microwave import InjectMicrowave


@pytest.mark.repository
class InjectModulesTestCase(ExperimentTestBase):
    def test_inject_ablation(self):
        self.run_experiment(InjectAblation(self.sys), {'ablation_time': 0.1})

    def test_inject_cw_laser(self):
        for mode in self.sys.l370.MODES.modes_list_str:
            self.run_experiment(InjectCWLaser(self.sys), {'l370_mode': mode})

    def test_inject_microwave(self):
        self.run_experiment(InjectMicrowave(self.sys))
