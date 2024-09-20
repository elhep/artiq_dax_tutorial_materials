import dax.sim.test_case
from dax.experiment import *

from test.system import DemoTestSystem


class CwModuleTestCase(dax.sim.test_case.PeekTestCase):

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

    def test_switch(self):
        self.sys.trigger_ttl.set(True)
        self.expect(self.sys.trigger_ttl._sw, 'state', True)

        self.sys.trigger_ttl.set(False)
        self.expect(self.sys.trigger_ttl._sw, 'state', False)

    def test_pulse(self):
        with parallel:
            self.sys.trigger_ttl.pulse(1 * s)
            with sequential:
                delay(.01 * s)
                self.expect(self.sys.trigger_ttl._sw, 'state', True)
                delay(.98 * s)
                self.expect(self.sys.trigger_ttl._sw, 'state', True)
                delay(.02 * s)
                self.expect(self.sys.trigger_ttl._sw, 'state', False)
