from artiq.experiment import *
from user import user_id
from common import Scope

class ParallelExcercise(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.ttl = self.get_device("ttl0")
        self.urukul = self.get_device("urukul0_cpld")
        self.urukul_channels = [self.get_device(f"urukul0_ch{i}") for  i in range(2)]
        self.scope = Scope(self, user_id)



    @kernel
    def run(self):
        ttl = self.ttl
        # Prepare oscilloscope
        self.scope.setup()
        # Reset our system after previous experiment
        self.core.reset()
    
        # Set SYSTEM time marker in future
        self.core.break_realtime()

        self.urukul.init()
        for ch in self.urukul_channels:
            ch.init()
            ch.sw.off()
            ch.set_att(0.0)
            ch.set(frequency=25*MHz)
            
        delay(10 * ms)
        '''
        TODO
        Drive ttl pulse for 200 ns and parallel switch on both urukul channels:
        Urukul channels objects:
        self.urukul_channels[0].sw.on()
        self.urukul_channels[1].sw.on() 
        self.urukul_channels[0].sw.off()
        self.urukul_channels[1].sw.off()

        Switch off channel 0 after 200 ns. Switch off channel 1 after 400 ns (200ns after channel 0)
        Drive another TTL pulse for 100 ns exactly 100 ns after the previous one.
        use 'with parallel' block and 'with sequential' block 
        '''
        with parallel:
            self.ttl.pulse(200 * ns)
        #    Your code in parallel block
        #    with sequential:
        #         Your code in sequential block (which is still in parallel block)
        #


        self.scope.store_waveform()
