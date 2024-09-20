import unittest
from unittest.mock import MagicMock
import random

import artiq.coredevice.spi2
import artiq.coredevice.ttl

import dax.sim.coredevice.core

from demo_system.coredevice.mems import MemsSystem


class MemsSystemTestCase(unittest.TestCase):
    SEED = None
    NUM_SAMPLES = 50
    PRECISION = 3  # Number of digits after the dot that have to be equal

    def setUp(self) -> None:
        # Random number generator
        self.rng = random.Random(self.SEED)

        # Mock devices and device manager
        hv_spi = MagicMock(spec=artiq.coredevice.spi2.SPIMaster)
        hv_spi.ref_period_mu = 1
        dac_spi = MagicMock(spec=artiq.coredevice.spi2.SPIMaster)
        dac_spi.ref_period_mu = 1
        device_manager = {
            'core': dax.sim.coredevice.core.BaseCore(),
            'hv_spi': hv_spi,
            'dac_spi': dac_spi,
            'hv_clr': MagicMock(spec=artiq.coredevice.ttl.TTLOut),
            'dac_rst': MagicMock(spec=artiq.coredevice.ttl.TTLOut),
            'ldac': MagicMock(spec=artiq.coredevice.ttl.TTLOut),
        }

        # Instantiated driver to test
        self.driver = MemsSystem(device_manager, sw_spi='hv_spi', dac_spi='dac_spi',
                                 sw_clr='hv_clr', dac_rst='dac_rst', ldac='ldac')

    def test_dac_vout_conversion(self):
        for _ in range(self.NUM_SAMPLES):
            v_out = self.rng.uniform(-10, 10)
            self.assertAlmostEqual(v_out, self.driver.dac_fsr_to_vout(self.driver.dac_vout_to_fsr(v_out)),
                                   places=self.PRECISION, msg='Output voltage conversion did not matched initial value')


if __name__ == '__main__':
    unittest.main()
