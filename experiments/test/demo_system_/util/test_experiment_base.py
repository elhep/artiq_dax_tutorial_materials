import dax.sim.test_case

from test.system import DemoTestSystem
from dax.experiment import *

from demo_system.system import *


class ExperimentTestBase(dax.sim.test_case.PeekTestCase):

    N_IONS: int = 1
    experiments: list[EnvExperiment]

    def setUp(self):
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        # self.sys.dax_init()
        self.sys.ion_load._update_num_ions(self.N_IONS)

    def run_experiment(self, experiment: EnvExperiment, args: dict = {}):
        for key, value in args.items():
            setattr(experiment, key, value)
        experiment.prepare()
        experiment.run()
