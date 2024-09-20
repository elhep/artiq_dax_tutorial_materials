from artiq.experiment import *
from user import user_id
from common import Scope

class Timing2Excercise(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.ttl = self.get_device("ttl0")
        # self.setattr_device("scope")
        self.setattr_argument(
            f"Delay", NumberValue(
                default = 100,
                ndecimals = 0,
                unit = "ns",
                type = "int",
                step = 1,
                min = 100,
                max = 1000,
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

        for i in range(10000):
            # Simple code: for self.Delay value < 390 ns system timer counter will catch our program
            self.ttl.on()
            delay(self.Delay * ns)
            self.ttl.off()
            delay(self.Delay * ns)

        self.scope.store_waveform()

