from dax.experiment import *
from demo_system.modules.util.state_controller import BinaryStateController


class BinaryStateControllerService(BinaryStateController, DaxService):
    """Context class for a service which controlls binary states"""
    pass
