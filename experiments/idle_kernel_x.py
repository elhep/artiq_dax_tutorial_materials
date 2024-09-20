from artiq.experiment import *
import numpy as np
from time import sleep


class Test(EnvExperiment):
    kernel_invariants = {'freqs', 'steps_no', 'urukul_channels'}
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

        self.steps_no = 20
        steps = np.linspace(0, 1., self.steps_no)
        self.freqs = [
            [(o * 1 + s) * MHz for s in steps]
            for o in range(5)
        ]

    @kernel
    def loop_procedure(self):
        for i in range(100):
            t = (100)
            with parallel:
                self.ttl0.pulse(t*us)
                self.urukul0_ch0.sw.pulse(t*us)
            self.urukul0_ch1.sw.pulse(t*us)

        # delay(100*ms)

        # for i in range(self.steps_no):
        #     delay(100*ms)
        #     with parallel:
        #         self.ttl0.pulse(100*us)
        #         for o in range(5):
        #             self.phaser0.channel[0].oscillator[o].set_frequency(self.freqs[o][i])
        #             self.phaser0.channel[0].oscillator[o].set_amplitude_phase(.2)
        #             self.phaser0.channel[1].oscillator[o].set_frequency(-self.freqs[o][i])
        #             self.phaser0.channel[1].oscillator[o].set_amplitude_phase(.2)
        #             delay(1*ms)


    @kernel
    def run(self):
        self.core.break_realtime()
        
        while True:
            self.loop_procedure()
