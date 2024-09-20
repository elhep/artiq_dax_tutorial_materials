from artiq.experiment import *
import numpy as np


class PhaserDemoExcercise(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")

        self.setattr_device("ttl0")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch0")
        self.setattr_device("urukul0_ch1")
        self.urukul_channels = [
            self.urukul0_ch0,
            self.urukul0_ch1
        ]
        self.setattr_device("phaser0")

        self.center_f = 97 * MHz

        freq_slopes = [
            np.linspace(2.8 * MHz, 1 * MHz, 100),
            np.linspace(2.9 * MHz, 2 * MHz, 100),
            np.full(100, 3 * MHz),
            np.linspace(3.1 * MHz, 4 * MHz, 100),
            np.linspace(3.2 * MHz, 5 * MHz, 100),
        ]

        amp_slopes = [
            np.linspace(0.375, 0.01, 100) * 0.9,
            np.linspace(0.10, 0.25, 100) * 0.9,
            np.linspace(0.05, 0.48, 100) * 0.9,
            np.linspace(0.10, 0.25, 100) * 0.9,
            np.linspace(0.375, 0.01, 100) * 0.9,
        ]

        # Make sure that summed amps never exceed 1.0 (full scale)
        assert all(sum(amps) <= 1.0 for amps in zip(*amp_slopes))

        self.ftw = [np.concatenate([slope, slope[::-1]]) for slope in freq_slopes]
        self.amps = [np.concatenate([slope, slope[::-1]]) for slope in amp_slopes]
        self.length = len(self.ftw[0])

    @kernel
    def init(self):
        self.core.reset()
        self.core.break_realtime()

        self.phaser0.init()
        
        self.ttl0.off()

    @kernel
    def run(self):
        self.init()

        phaser = self.phaser0
        
        phaser.channel[0].set_att(0 * dB)
        phaser.channel[0].set_duc_frequency(self.center_f)
        phaser.channel[0].set_duc_phase(0.25)
        phaser.channel[0].set_duc_cfg()

        delay(0.1 * ms)
        phaser.duc_stb()
        delay(0.1 * ms)
        
        while True:
            for i in range(self.length):
                for osc in range(5):
                    phaser.channel[0].oscillator[osc].set_frequency(self.ftw[osc][i])
                    phaser.channel[0].oscillator[osc].set_amplitude_phase(
                        self.amps[osc][i], phase=0.25)
                    delay(5 * ms)
        # for osc in range(5):
        #     phaser.channel[0].oscillator[osc].set_frequency(self.ftw[osc])
        #     phaser.channel[0].oscillator[osc].set_amplitude_phase(
        #         self.asf[osc], phase=0.25)
        #     delay(0.1 * ms)

        
