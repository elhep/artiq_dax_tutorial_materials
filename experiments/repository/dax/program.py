import dax.clients.program
from dax.program import *

from demo_system.system import *
from demo_system.services.cool_prep import CoolInitService


class ProgramClient(dax.clients.program.ProgramClient(DemoSystem)):
    """Program client"""
    PROGRAMS_DIR_PATH = "program"
    

    def setup(self):
        pass


if __name__ == '__main__':
    from artiq.frontend.artiq_run import run

    run()
