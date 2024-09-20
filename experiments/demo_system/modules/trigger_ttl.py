from dax.experiment import *

from demo_system.modules.util.switch import Switch
from demo_system.modules.util.state_controller import BinaryStateController


class TriggerTTLModule(Switch, BinaryStateController):

    def build(self):
        super(TriggerTTLModule, self).build(sw_key='ttl0')
        BinaryStateController.build(self, set_cb=self.set_cb, default_state=False)

    def init(self, *, force: bool = False) -> None:
        """Initialize this module.

        :param force: Force full initialization
        """
        super(TriggerTTLModule, self).init()
        # For some reason, BSC init is not being called with super
        BinaryStateController.init(self)

        self.set_default_pulse_duration(10 * us)

    @kernel
    def set_cb(self, state: TBool) -> None:
        self.set(state, realtime=True)
