import dax.sim.test_case

from test.system import DemoTestSystem


class PMTModuleTestCase(dax.sim.test_case.PeekTestCase):

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

    def test_detect(self):
        self.sys.pmt.detect_all(1)
        self.sys.pmt.detect_channels([1], 1)
        self.sys.pmt.detect(1, 1)

    def test_active(self):
        self.assertEqual(self.sys.pmt.active_channels(), [])
        self.sys.pmt.set_active_channels([1])
        self.assertEqual(self.sys.pmt.active_channels(), [1])
        self.sys.pmt.detect_active(1)

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            self.sys.pmt.detect_channels([], 1)
        with self.assertRaises(AssertionError):
            self.sys.pmt.set_active_channels([-1])
        with self.assertRaises(AssertionError):
            self.sys.pmt.set_active_channels([-1] * (self.sys.pmt.NUM_CHANNELS + 1))
        with self.assertRaises(AssertionError):
            self.sys.pmt.set_active_channels([1, 1])
