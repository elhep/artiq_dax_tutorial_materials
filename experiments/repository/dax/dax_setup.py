from demo_system.system import *
from dax.util.sub_experiment import SubExperiment


class DaxInit(DemoSystem, EnvExperiment):
    """_DAX initialization"""

    def build(self) -> None:
        try:
            # Build system
            super(DaxInit, self).build()
        except KeyError:
            # Could not find key and system config might not be available, fallback on defaults
            self.logger.info('No current configuration exists yet, run this utility once to set a configuration')

    def run(self):
        # Initialize system
        self.dax_init()


class SystemConfig(DemoSystem, EnvExperiment):
    """_System configuration"""

    def build(self) -> None:
        try:
            # Build system
            super(SystemConfig, self).build()
        except KeyError:
            # Could not find key and system config might not be available, fallback on defaults
            self.logger.info('No current configuration exists yet, run this utility once to set a configuration')
            mon_pmt_enabled = False
        else:
            # Obtain current system config (read-only), can raise a archive overwrite warning which can be ignored
            mon_pmt_enabled = self.get_dataset_sys(self.MON_PMT_ENABLED_KEY)

            # Add arguments
        self.mon_pmt_enabled = self.get_argument('Monitoring PMT enabled', BooleanValue(mon_pmt_enabled),
                                                 tooltip='Use Monitoring PMT as a main PMT')

    def prepare(self):
        # Check arguments
        assert isinstance(self.mon_pmt_enabled, bool)

    def run(self):
        # Write system datasets
        self.set_dataset_sys(self.MON_PMT_ENABLED_KEY, self.mon_pmt_enabled)


class DaxSetup(DemoSystem, Experiment):
    """DAX Setup"""

    def __init__(self, managers, *args, **kwargs):
        # Capture the managers before passing them to super
        self._managers = managers
        super(DaxSetup, self).__init__(managers, *args, **kwargs)

    def build(self) -> None:
        try:
            # Build system
            super(DaxSetup, self).build()
        except KeyError:
            # Could not find key and system config might not be available, fallback on defaults
            self.logger.info('No current configuration exists yet, run this utility once to set a configuration')

    def run(self):
        sub_experiment = SubExperiment(self, self._managers)
        sub_experiment.run(SystemConfig, "config")
        sub_experiment.run(DaxInit, "init")
