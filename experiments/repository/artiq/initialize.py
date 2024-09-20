import time

from artiq.experiment import *
from common import Scope
from user import user_id


class Initialize(EnvExperiment):

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

        self.scope = Scope(self, user_id)   

    @kernel
    def init(self):
        self.core.reset()

        self.urukul0_cpld.init()
        for urukul_ch in self.urukul_channels:
            urukul_ch.init()
            urukul_ch.sw.off()
            urukul_ch.set_att(31.5)

    @kernel
    def run_rt(self):
        self.init()

        # First setup Urukuls
        self.urukul0_ch0.set(frequency=10 * MHz)
        self.urukul0_ch0.set_att(10.0)
        self.urukul0_ch0.sw.on()

        self.urukul0_ch1.set(frequency=20 * MHz)
        self.urukul0_ch1.set_att(10.0)
        self.urukul0_ch1.sw.on()

        delay(1 * ms)

        # Starting TTL sequence will trigger the scope
        for _ in range(100):
            self.ttl0.pulse(100 * ns)
            delay(100 * ns)

    def run(self):        
        total_time = 0
        num_executions = 1

        for _ in range(num_executions):
            start_time = time.time()
            
            # Profile scope.setup()
            setup_start = time.time()
            self.scope.setup()
            setup_end = time.time()
            setup_time = setup_end - setup_start
            
            # Profile run_rt()
            run_rt_start = time.time()
            self.run_rt()
            run_rt_end = time.time()
            run_rt_time = run_rt_end - run_rt_start
            
            # Profile scope.store_waveform()
            store_start = time.time()
            self.scope.store_waveform()
            store_end = time.time()
            store_time = store_end - store_start
            
            end_time = time.time()
            loop_time = end_time - start_time
            total_time += loop_time

            print(f"Execution {_ + 1}:")
            print(f"  scope.setup() time: {setup_time:.6f} seconds")
            print(f"  run_rt() time: {run_rt_time:.6f} seconds")
            print(f"  scope.store_waveform() time: {store_time:.6f} seconds")
            print(f"  Total loop time: {loop_time:.6f} seconds")

        average_time = total_time / num_executions
        print(f"Average execution time: {average_time:.6f} seconds")
