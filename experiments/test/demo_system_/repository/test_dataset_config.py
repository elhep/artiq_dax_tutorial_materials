import pytest

from test.demo_system_.util.test_experiment_base import ExperimentTestBase

from repository.dax.util.dataset_config.system_config import SystemConfig


@pytest.mark.repository
class InjectModulesTestCase(ExperimentTestBase):

    def test_SystemConfig(self):
        self.run_experiment(SystemConfig(self.sys))
