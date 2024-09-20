from artiq.experiment import *

from demo_system.system import DemoSystem


class InjectNIons(DemoSystem, EnvExperiment):
    """Inject N Ions"""

    _group = 'N Ions'

    def build(self):
        # Get Devices
        super(InjectNIons, self).build()

        # Inject Ions
        self.n_ions = self.get_argument('N Ions',
                                        processor=NumberValue(1),
                                        group=self._group,
                                        tooltip='Set Number of Ions')

        # Timing arguments
        self.pre_delay = self.get_argument('Pre-delay time',
                                           processor=NumberValue(10 * ms, 'ms', step=1 * ms, min=0 * ms),
                                           group='Delays',
                                           tooltip='Wait time before configuring the device')
        self.post_delay = self.get_argument('Post-delay time',
                                            processor=NumberValue(0 * s, 's', step=1 * s, min=0 * s),
                                            group='Delays',
                                            tooltip='Wait time after the device is configured')

        self.update_kernel_invariants('n_ions', 'pre_delay', 'post_delay')

    def prepare(self):
        self.dax_init()
        pass

    def run(self):
        self.ion_load._update_num_ions(int(self.n_ions))
