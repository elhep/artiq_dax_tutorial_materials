import dax.sim.test_case

from test.system import DemoTestSystem


class DaxInitTestCase(dax.sim.test_case.PeekTestCase):

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

    def test_cpld(self):
        # CPLD
        self.assertGreater(len(self.sys.cpld.cpld), 0, msg='Expected at least one CPLD device')
        for cpld in self.sys.cpld.cpld:
            self.expect(cpld, 'init_att', True)

    def test_pmt(self):
        # PMT
        for ttl in self.sys.pmt._ttl:
            self.expect(ttl, 'direction', 0)

        # Laser
        # self.expect(env.laser.ca._dds.sw, 'state', 'x')
        # for signal in ['freq', 'amp']:
        #     self.expect(env.laser.ca._dds, signal, 'x')
        # for laser in env.laser.all_k_lasers:
        #     self.expect(laser._dds.sw, 'state', 0)
        #     self.expect_close(laser._dds, 'freq', laser._freq, delta=0.1)
        #     self.expect_close(laser._dds, 'amp', laser._amp, delta=0.1)
        #     self.expect_close(laser._dds.cpld, f'att_{laser._dds.chip_select - 4}', laser._dds_att, delta=0.1)

        # Ionizing shutter
        # self.expect(env.ionizing_shutter._ttl, 'state', 0)

        # Trap
        # for i in range(env.trap.dc.NUM_CHANNELS):
        #     self.expect(env.trap.dc._dac._zotino, f'v_out_{i}', 'x')

        # TOF
        # self.expect(env.tof._trigger, 'state', 0)
