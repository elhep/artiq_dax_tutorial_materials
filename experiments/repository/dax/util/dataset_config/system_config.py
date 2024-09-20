from demo_system.system import *


class SystemConfig(DemoSystem, EnvExperiment):
    """System configuration"""

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


if __name__ == '__main__':
    from artiq.frontend.artiq_run import run

    run()
