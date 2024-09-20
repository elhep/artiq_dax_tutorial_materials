import dax.sim.test_case

from test.system import DemoTestSystem
# from dax.experiment import *


class SwitchTestCase(dax.sim.test_case.PeekTestCase):

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

        self.dut = self.sys.l370._cool_sw

    # def test_initial(self):
    #     self.assert_laser_state(doppler=False, detect=False, eit=False)
    def test_init(self):
        self.expect(self.dut._sw, 'state', self.dut._default_state)

    def test_reset(self):
        self.expect(self.dut._sw, 'state', self.dut._default_state)
        self.dut.set(not self.dut._default_state)
        self.expect(self.dut._sw, 'state', not self.dut._default_state)
        self.dut.reset()
        self.expect(self.dut._sw, 'state', self.dut._default_state)

    def test_set(self):
        self.dut.set(True)
        self.expect(self.dut._sw, 'state', True)
        self.dut.set(False)
        self.expect(self.dut._sw, 'state', False)
        self.dut.set(True)
        self.expect(self.dut._sw, 'state', True)

    def test_safety_off(self):
        self.dut.set(True)
        self.expect(self.dut._sw, 'state', True)
        self.dut.safety_off()
        self.expect(self.dut._sw, 'state', False)
