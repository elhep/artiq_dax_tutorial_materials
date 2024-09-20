import dax.sim.test_case

from test.system import DemoTestSystem
# from dax.experiment import *


class MicrowaveTestCase(dax.sim.test_case.PeekTestCase):

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

    # def test_initial(self):
    #     self.assert_laser_state(doppler=False, detect=False, eit=False)

    def test_defaults(self):
        pass
