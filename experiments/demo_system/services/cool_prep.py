from dax.experiment import *

from demo_system.modules.cw_laser import Laser370
from demo_system.modules.util.state_controller import BinaryStateController


class CoolInitService(DaxService):
    SERVICE_NAME = "cool_prep"

    def build(self):
        self.cool = Cooling(self)
        self.prep = Preparing(self)
        self.update_kernel_invariants("cool", "prep")

    @portable
    def modes(self):
        return self.doppler._370.MODES

    def init(self) -> None:
        pass

    def post_init(self) -> None:
        pass


class Cooling(DaxService, BinaryStateController):
    SERVICE_NAME = "doppler"

    def build(self, **kwargs):
        super(Cooling, self).build(set_cb=self._doppler_set, default_state=True)
        # Get the relevant modules
        self._370 = self.registry.find_module(Laser370)
        self.update_kernel_invariants("_370")

    def init(self) -> None:
        super(Cooling, self).init()

    def post_init(self) -> None:
        pass

    """Doppler Cooling functions"""

    @kernel
    def _doppler_set(self, state: TBool):
        self._370.set_state(mode=self._370.MODES.COOL, state=state, realtime=True)


class Preparing(DaxService, BinaryStateController):
    SERVICE_NAME = "initialization"

    def build(self, **kwargs):
        super(Preparing, self).build(set_cb=self._init_set, default_state=False)
        # Get the relevant modules
        self._370 = self.registry.find_module(Laser370)
        self.update_kernel_invariants("_370")

    def init(self) -> None:
        super(Preparing, self).init()

    def post_init(self) -> None:
        pass

    """Pumping functions"""

    @kernel
    def _init_set(self, state: TBool):
        self._370.set_state(mode=self._370.MODES.Prep, state=state, realtime=False)
