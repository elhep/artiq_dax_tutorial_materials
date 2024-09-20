from artiq.experiment import *

from demo_system.system import DemoSystem


class InjectMicrowave(DemoSystem, EnvExperiment):
    """Inject Microwave"""

    kernel_invariants = {
        'pre_delay',
        'post_delay'
    }

    def build(self):
        # Get Devices
        super(InjectMicrowave, self).build()

        # Mirror Set
        self.frequency = self.get_argument('Microwave Frequency',
                                           processor=NumberValue(200 * MHz, unit="MHz", min=100 * MHz, max=400 * MHz),
                                           group='Microwave',
                                           tooltip='Sets the Microwave Frequency')

        self.pulse_duration = self.get_argument('Pulse Duration',
                                                processor=NumberValue(1 * s, 'us', min=0.0),
                                                group='Microwave',
                                                tooltip='Sets the Microwave Frequency')
        # Timing arguments
        self.pre_delay = self.get_argument('Pre-delay time',
                                           processor=NumberValue(10 * ms, 'ms', step=1 * ms, min=0 * ms),
                                           group='Delays',
                                           tooltip='Wait time before configuring the device')
        self.post_delay = self.get_argument('Post-delay time',
                                            processor=NumberValue(0 * s, 's', step=1 * s, min=0 * s),
                                            group='Delays',
                                            tooltip='Wait time after the device is configured')

    def prepare(self):
        self.dax_init()
        pass

    @kernel
    def run(self):
        # Reset the core
        self.core.reset()

        # Pre-delay
        delay(self.pre_delay)

        self.inject_microwave()

        # Post-wait time
        delay(self.post_delay)
        self.core.wait_until_mu(now_mu())

    @kernel
    def inject_microwave(self):
        self.microwave.pulse(self.pulse_duration)
        pass
