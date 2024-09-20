from test.demo_system_.util.test_binary_state_controller_base import BinaryStateControllerTestBase


class DopplerTestCase(BinaryStateControllerTestBase):
    __test__ = True
    _default_state = True

    freq_places = 0
    amp_places = 4

    def initialize_test(self):
        self.dut = self.sys.cool_prep.cool

    def assert_state(self, state: bool, initial=False):
        if initial:
            mode = self.sys.l370.MODES.COOL
            state = True
        else:
            mode = self.sys.l370.MODES.COOL
        self.sys.logger.warning(f"Testing: {self.sys.l370.MODES.modes_list_str[mode]}")

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


class PumpTestCase(BinaryStateControllerTestBase):
    __test__ = True
    _default_state = False

    freq_places = 0
    amp_places = 4

    def initialize_test(self):
        self.dut = self.sys.cool_prep.prep

    def assert_state(self, state: bool, initial: bool = False):
        if initial:
            mode = self.sys.l370.MODES.COOL
            state = True
        else:
            mode = self.sys.l370.MODES.Prep
        self.sys.logger.warning(f"Testing: {self.sys.l370.MODES.modes_list_str[mode]}")

        self.assert_laser_state(mode=mode, state=state)

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
