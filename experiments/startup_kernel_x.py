from artiq.experiment import *
from time import sleep


class Test(EnvExperiment):
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

    @kernel
    def init(self):
        self.core.reset()

        self.urukul0_cpld.init()
        for urukul_ch in self.urukul_channels:
            urukul_ch.init()
            urukul_ch.sw.off()
            urukul_ch.set_att(31.5)

    @kernel
    def set_phaser_frequencies(self, phaser, duc, osc):
        self.core.break_realtime()
        phaser.init()
        delay(1*ms)
        phaser.channel[0].set_duc_frequency(duc)
        phaser.channel[0].set_duc_cfg()
        phaser.channel[0].set_att(6*dB)
        phaser.channel[1].set_duc_frequency(-duc)
        phaser.channel[1].set_duc_cfg()
        phaser.channel[1].set_att(6*dB)
        phaser.duc_stb()
        delay(1*ms)
        for i in range(len(osc)):
            phaser.channel[0].oscillator[i].set_frequency(osc[i])
            phaser.channel[0].oscillator[i].set_amplitude_phase(.2)
            phaser.channel[1].oscillator[i].set_frequency(-osc[i])
            phaser.channel[1].oscillator[i].set_amplitude_phase(.2)
            delay(1*ms)

    @kernel
    def run(self):
        self.init()

        # First setup Urukuls
        self.urukul0_ch0.set(frequency=10*MHz)
        self.urukul0_ch0.set_att(10.0)
        # self.urukul0_ch0.sw.on()

        self.urukul0_ch1.set(frequency=20*MHz)
        self.urukul0_ch1.set_att(10.0)
        # self.urukul0_ch1.sw.on()

        # Now setup Phaser
        duc = (1)*10*MHz
        osc = [i*1*MHz for i in range(5)]
        self.set_phaser_frequencies(self.phaser0, duc, osc)
