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
        # Prepare oscilloscope
        self.scope.setup()
        # Reset our system after previous experiment
        self.core.reset()

        # Set SYSTEM time pointer in future
        self.core.break_realtime()

        # t will be our LOCAL time pointer. For now it points the same point in timeline as SYSTEM pointer
        t = now_mu()

        # Let's drive single pulse. With delay() we change system pointer relative: 
        # software does not care about the exact point in timeline but we know that next event will take place exactly "FirstPulseWidth" microseconds after ttl.set_o(True) command
        self.ttl.on()
        delay(self.FirstPulseWidth * ns)
        self.ttl.off()

        # Because of delay() function, SYSTEM pointer is DelayValue further. Let's drive another pulse using at_mu:
        at_mu(t + # start with local pointer
              self.core.seconds_to_mu(self.FirstPulseWidth * ns) + # add FirstPulseWidth to "catch" system pointer
              self.core.seconds_to_mu(self.DelayToNextPulse * ns))  # add Delay value

        self.ttl.pulse(self.SecondPulseWidth * ns)
        # Pulse method consists delay() function inside. SYSTEM pointer is now at falling edge of the second pulse.


        self.scope.store_waveform()

