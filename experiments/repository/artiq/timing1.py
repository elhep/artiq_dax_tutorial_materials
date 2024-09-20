from artiq.experiment import *
from user import user_id
from common import Scope

class Timing1Excercise(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.ttl = self.get_device("ttl0")
        self.setattr_argument(
            f"FirstPulseWidth", NumberValue(
                default = 250,
                ndecimals = 0,
                unit = "ns",
                type = "int",
                step = 1,
                min = 10,
                max = 400,
                scale=1
            )
        )
        self.setattr_argument(
            f"DelayToNextPulse", NumberValue(
                default = 250,
                ndecimals = 0,
                unit = "ns",
                type = "int",
                step = 1,
                min = 10,
                max = 400,
                scale=1
            )
        )
        self.setattr_argument(
            f"SecondPulseWidth", NumberValue(
                default = 250,
                ndecimals = 0,
                unit = "ns",
                type = "int",
                step = 1,
                min = 10,
                max = 400,
                scale=1
            )
        )
        self.scope = Scope(self, user_id)



    @kernel
    def run(self):
        ttl = self.ttl
        self.scope.setup()
        # Reset our system after previous experiment
        self.core.reset()

        # Set SYSTEM time marker in future
        self.core.break_realtime()

        # t will be our LOCAL time marker. For now it points the same point in timeline as SYSTEM: now marker
        t = now_mu()


        '''
        TODO
        Drive two pulses with self.ttl object. Remember about delay between. Time values are defined by arguments:
        self.FirstPulseWidth
        self.SecondPulseWidth
        self.DelayToNextPulse

        How to use dashboard arguments with delay() and at_mu()? Examples:
        
        delay(self.FirstPulseWidth * ns)
        at_mu(t + self.core.seconds_to_mu(self.FirstPulseWidth * ns))
        '''
        # TODO Your code should be here


        self.scope.store_waveform()

