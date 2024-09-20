from demo_system.system import *


class DaxInit(DemoSystem, EnvExperiment):
    """DAX initialization"""

    def run(self):
        # Initialize system
        self.dax_init()


if __name__ == '__main__':
    from artiq.frontend.artiq_run import run

    run()


class Idle(DemoSystem, EnvExperiment):
    """Idle"""

    def run(self):
        # Initialize system
        self.dax_init()
        # Turn off system
        self.idle()


if __name__ == '__main__':
    from artiq.frontend.artiq_run import run

    run()


class SafetyOff(DemoSystem, EnvExperiment):
    """Safety Off"""

    def run(self):
        # Initialize system
        self.dax_init()
        # Turn off system
        self.safety_off()


if __name__ == '__main__':
    from artiq.frontend.artiq_run import run

    run()
