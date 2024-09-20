import dax.sim.test_case

from test.system import DemoTestSystem

# from dax.experiment import *


class L370TestCase(dax.sim.test_case.PeekTestCase):
    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

    def test_initial(self):
        self.assert_laser_state(mode=self.sys.l370.MODES.COOL, state=True)

    def test_all_states(self):
        for mode in self.sys.l370.MODES.modes_list_int:
            for state in [True, False]:
                self.sys.l370.set_state(mode=mode, state=state)
                self.assert_laser_state(mode=mode, state=state)

    def test_config(self):
        for mode in self.sys.l370.MODES.modes_list_int:
            self.sys.l370.config_mode(mode=mode)
            self.assert_laser_state(mode=mode, state=True)

    def test_reset(self):
        for mode in self.sys.l370.MODES.modes_list_int:
            for state in [True, False]:
                self.sys.l370.set_state(mode=mode, state=state)
                self.sys.l370.reset()
                self.assert_laser_state(mode=self.sys.l370.MODES.COOL, state=True)

    def test_idle(self):
        for mode in self.sys.l370.MODES.modes_list_int:
            for state in [True, False]:
                self.sys.l370.set_state(mode=mode, state=state)
                self.sys.l370.reset()
                self.assert_laser_state(mode=self.sys.l370.MODES.COOL, state=True)

    def test_safety_off(self):
        for mode in self.sys.l370.MODES.modes_list_int:
            for state in [True, False]:
                self.sys.l370.set_state(mode=mode, state=state)
                self.sys.l370.safety_off()
                self.assert_laser_state(mode=self.sys.l370.MODES.OFF, state=False)

    freq_places = 0
    amp_places = 4

    def assert_laser_state(self, mode: int, state: bool):
        self.sys.logger.warning(f"Testing: {self.sys.l370.MODES.modes_list_str[mode]}")
        # 370
        self.expect(self.sys.l370._shutter._dds.sw, "state", state)
        self.expect(self.sys.l370._cool_sw._sw, "state", mode == self.sys.l370.MODES.COOL)
        self.expect(self.sys.l370._detect_prep_cool_dds._dds.sw, "state", mode == self.sys.l370.MODES.DETECT
                    or mode == self.sys.l370.MODES.Prep or mode == self.sys.l370.MODES.COOL)

        if mode == self.sys.l370.MODES.COOL:
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "freq",
                              self.sys.l370._cool_freq, places=self.freq_places)
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "amp",
                              self.sys.l370._cool_amp, places=self.amp_places)
        elif mode == self.sys.l370.MODES.Prep:
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "freq",
                              self.sys.l370._prep_freq, places=self.freq_places)
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "amp",
                              self.sys.l370._prep_amp, places=self.amp_places)
        elif mode == self.sys.l370.MODES.DETECT:
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "freq",
                              self.sys.l370._detect_freq, places=self.freq_places)
            self.expect_close(self.sys.l370._detect_prep_cool_dds._dds, "amp",
                              self.sys.l370._detect_amp, places=self.amp_places)
