import abc

import dax.sim.test_case

from test.system import DemoTestSystem
from dax.experiment import *


class BinaryStateControllerTestBase(dax.sim.test_case.PeekTestCase, abc.ABC):
    __test__ = False

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()
        self.initialize_test()

    @abc.abstractmethod
    def initialize_test(self):
        pass

    @abc.abstractmethod
    def assert_state(self, state: bool, initial: bool = False):
        pass

    def set_cb(self, state: bool):
        self._state = state

    def test_initial(self):
        self.assert_state(state=self._default_state, initial=True)
        self.assertEqual(self.dut._default_state, self._default_state)

    def test_all_states(self):
        self.dut.set_state(state=True)
        self.assert_state(state=True)
        self.dut.set_state(state=False)
        self.assert_state(state=False)
        self.dut.on()
        self.assert_state(state=True)
        self.dut.off()
        self.assert_state(state=False)

    def test_safety_off(self):
        self.dut.set_state(state=True)
        self.assert_state(state=True)
        self.dut.safety_off()
        self.assert_state(state=False)

    def test_reset(self):
        self.dut.set_state(state=not self._default_state)
        self.assert_state(state=not self._default_state)
        self.dut.reset()
        self.assert_state(state=self._default_state)

    # def test_pulse(self):
    #     duration = 1 * s
    #     self.dut.safety_off()
    #     with parallel:
    #         self.dut.pulse(duration=duration)
    #         with sequential:
    #             delay(1 * us)
    #             self.assert_state(state=True)
    #             delay(duration - (1 * us))
    #             self.assert_state(state=True)
    #             delay(1 * us)
    #             self.assert_state(state=False)

    # def test_default_pulse(self):
    #     duration = self.dut._default_pulse_duration_mu
    #     self.dut.safety_off()
    #     with parallel:
    #         self.dut.pulse()
    #         with sequential:
    #             delay(1 * us)
    #             self.assert_state(state=True)
    #             delay(duration)
    #             self.assert_state(state=False)
