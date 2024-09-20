import pytest

from test.demo_system_.util.test_experiment_base import ExperimentTestBase

from repository.dax.util.dax.dax_init import DaxInit, Idle, SafetyOff


@pytest.mark.repository
class DaxInitTestCase(ExperimentTestBase):
    __test__ = True

    def test_dax_init(self):
        self.run_experiment(DaxInit(self.sys))

    def test_idle(self):
        self.run_experiment(Idle(self.sys))

    def test_safety_off(self):
        self.run_experiment(SafetyOff(self.sys))
