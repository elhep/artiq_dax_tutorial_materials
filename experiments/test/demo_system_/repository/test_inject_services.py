import pytest

from test.demo_system_.util.test_experiment_base import ExperimentTestBase

from repository.dax.util.inject_services.inject_cooling import InjectCooling
from repository.dax.util.inject_services.inject_detection import InjectDetection
from repository.dax.util.inject_services.inject_ions import InjectNIons


@pytest.mark.repository
class InjectModulesTestCase(ExperimentTestBase):

    def test_inject_cooling(self):
        self.run_experiment(InjectCooling(self.sys))

    def test_inject_detection(self):
        self.run_experiment(InjectDetection(self.sys))

    def test_inject_ions(self):
        self.run_experiment(InjectNIons(self.sys))
