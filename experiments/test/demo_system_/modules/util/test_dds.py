from numpy import int32, random
import dax.sim.test_case

from test.system import DemoTestSystem
from dax.experiment import *


class DDS9910TestCase(dax.sim.test_case.PeekTestCase):
    pass
    N_RANDOM_TESTS = 10
    PHASE_PLACES = 3
    FREQ_PLACES = 0
    AMP_PLACES = 3

    def setUp(self) -> None:
        self.sys = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        self.sys.dax_init()

        self.dut = self.sys.l370._shutter

    def test_defaults(self):
        self.expect_close(self.dut._dds, 'freq', self.dut._default_freq, places=self.FREQ_PLACES)
        self.expect_close(self.dut._dds, 'phase', self.dut._default_phase, places=self.PHASE_PLACES)
        self.expect_close(self.dut._dds, 'amp', self.dut._default_amp, places=self.AMP_PLACES)
        # self.expect_close(self.dut._dds.cpld, 'att_0', self.dut._default_att)

    def test_defaults_mu(self):
        self.assertEqual(self.dut._default_ftw, self.frequency_to_ftw(self.dut._default_freq))
        self.assertEqual(self.dut._default_pow, self.turns_to_pow(self.dut._default_pow))
        self.assertEqual(self.dut._default_asf, self.amplitude_to_asf(self.dut._default_amp))
        self.assertEqual(self.dut._max_asf, self.amplitude_to_asf(self.dut._max_amp))

    def test_config_frequency(self):
        for frequency in random.uniform(100 * MHz, 400 * MHz, self.N_RANDOM_TESTS):
            self.dut.config_freq(frequency=frequency)
            self.expect_close(self.dut._dds, 'freq', frequency, places=self.FREQ_PLACES)
            self.expect_close(self.dut._dds, 'phase', self.dut._default_phase, places=self.PHASE_PLACES)
            self.expect_close(self.dut._dds, 'amp', self.dut._default_amp, places=self.AMP_PLACES)

    def test_config_phase(self):
        for phase in random.uniform(0, 1, self.N_RANDOM_TESTS):
            self.dut.config_phase(phase=phase)
            self.expect_close(self.dut._dds, 'freq', self.dut._default_freq, places=self.FREQ_PLACES)
            self.expect_close(self.dut._dds, 'phase', phase, places=self.PHASE_PLACES)
            self.expect_close(self.dut._dds, 'amp', self.dut._default_amp, places=self.AMP_PLACES)

    def test_config_amp(self):
        amp_set = self.dut._default_amp
        for amp in random.uniform(0, 1, self.N_RANDOM_TESTS):
            self.dut.config_amp(amp=amp)
            if amp <= self.dut._max_amp:
                amp_set = amp
            self.expect_close(self.dut._dds, 'freq', self.dut._default_freq, places=self.FREQ_PLACES)
            self.expect_close(self.dut._dds, 'phase', self.dut._default_phase, places=self.PHASE_PLACES)
            self.expect_close(self.dut._dds, 'amp', amp_set, places=self.AMP_PLACES)

    def test_config(self):
        amp_set = self.dut._default_amp
        freq_set = self.dut._default_freq
        phase_set = self.dut._default_phase

        frequencies = random.uniform(100 * MHz, 400 * MHz, self.N_RANDOM_TESTS)
        phases = random.uniform(0, 1, self.N_RANDOM_TESTS)
        amps = random.uniform(0, 1, self.N_RANDOM_TESTS)
        for i in range(self.N_RANDOM_TESTS):
            self.dut.config(freq=frequencies[i], phase=phases[i], amp=amps[i])
            if amps[i] <= self.dut._max_amp:
                amp_set = amps[i]
                freq_set = frequencies[i]
                phase_set = phases[i]

            self.expect_close(self.dut._dds, 'freq', freq_set, places=self.FREQ_PLACES)
            self.expect_close(self.dut._dds, 'phase', phase_set, places=self.PHASE_PLACES)
            self.expect_close(self.dut._dds, 'amp', amp_set, places=self.AMP_PLACES)

        self.dut.reset_config()
        self.assertEqual(self.dut._default_ftw, self.frequency_to_ftw(self.dut._default_freq))
        self.assertEqual(self.dut._default_pow, self.turns_to_pow(self.dut._default_pow))

    # def test_att(self):
    #     att_set = self.dut._default_att
    #     self.expect(self.dut._dds.cpld, 'att_0', att_set)

    #     for att in random.uniform(0, 31.5 * dB, self.N_RANDOM_TESTS):
    #         self.dut.config_att(att=att)
    #         if att >= self.dut._min_att:
    #             att_set = att
    #         self.expect(self.dut._dds.cpld, 'att_0', att_set)

    # def test_config_latency(self):
    #     self.assertEqual(self.dut._config_latency_mu, 0)
    #     self.dut.update_config_latency()
    #     self.assertAlmostEqual(self.dut._config_latency_mu, 8)
    #     self.dut.clear_config_latency()
    #     self.assertAlmostEqual(self.dut._config_latency_mu, 0)

    def test_att_latency(self):
        self.assertEqual(self.dut._att_latency_mu, 0)
        self.dut.update_att_latency()
        self.assertAlmostEqual(self.dut._att_latency_mu, 0)

    # Copies from artiq.coredevice.ad9910
    @portable(flags={"fast-math"})
    def frequency_to_ftw(self, frequency):
        """Return the 32-bit frequency tuning word corresponding to the given
        frequency.
        """
        return int32(round(self.dut._dds.ftw_per_hz * frequency))

    @portable(flags={"fast-math"})
    def ftw_to_frequency(self, ftw):
        """Return the frequency corresponding to the given frequency tuning
        word.
        """
        return ftw / self.dut._dds.ftw_per_hz

    @portable(flags={"fast-math"})
    def turns_to_pow(self, turns):
        """Return the 16-bit phase offset word corresponding to the given phase
        in turns."""
        return int32(round(turns * 0x10000)) & int32(0xffff)

    @portable(flags={"fast-math"})
    def pow_to_turns(self, pow_):
        """Return the phase in turns corresponding to a given phase offset
        word."""
        return pow_ / 0x10000

    @portable(flags={"fast-math"})
    def amplitude_to_asf(self, amplitude):
        """Return 14-bit amplitude scale factor corresponding to given
        fractional amplitude."""
        code = int32(round(amplitude * 0x3fff))
        if code < 0 or code > 0x3fff:
            raise ValueError("Invalid AD9910 fractional amplitude!")
        return code

    @portable(flags={"fast-math"})
    def asf_to_amplitude(self, asf):
        """Return amplitude as a fraction of full scale corresponding to given
        amplitude scale factor."""
        return asf / float(0x3fff)
