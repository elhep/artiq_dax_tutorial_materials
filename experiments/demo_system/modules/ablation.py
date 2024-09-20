from dax.experiment import *
from dax.modules.safety_context import SafetyContext
import inspect
import artiq.coredevice.ttl


class AblationModule(SafetyContext):
    """Ablation Module, turns on ablation laser on entering ablation context."""

    _ablation_on: bool = None

    def build(self) -> None:
        # Call super
        super(AblationModule, self).build(
            enter_cb=self._enter_cb, exit_cb=self._exit_cb
        )

        # Get the controller
        self._ablation_sw = self.get_device(
            "ttl1", artiq.coredevice.ttl.TTLOut
        )

    def init(self) -> None:
        self._ablation_on = False
        self.init_kernel()

    @kernel
    def init_kernel(self):
        # Switch ablation laser off in the unlikely event it was on
        self.off()

    def post_init(self) -> None:
        pass

    """Module functionality"""

    @portable
    def _enter_cb(self):
        pass

    @portable
    def _exit_cb(self):
        # Always turn off at the end of the safety context
        self.off()

    @kernel
    def on(self):
        # Only turn on in safety conext
        if self.in_context():
            # Break Realtime to avoid RTIO Underflow
            self.core.break_realtime()
            self._ablation_sw.on()
            self._ablation_on = True
        else:
            self.logger.warning("Attempted to turn on Ablation outside of context")

    @kernel
    def off(self):
        # Break Realtime to avoid RTIO Underflow
        self.core.break_realtime()
        self._ablation_sw.off()
        self._ablation_on = False

    def _get_parent(self, trace=0):
        """Get the method calling the current function
        :param trace: Return `n`th parent of the function
        """
        """
        The chosen constants in inspect.stack()[i][j] can be a bit confusing. Let me explain:
        i: This is the index in the stack. The constant is set to 3 because:
        - 0: `inspect.stack()`
        - 1: `_get_parent()`
        - 2: the function which calls `_get_parent()`
        - 3: The name of the calling function
        j: inspect.stack returns a tuple
        (frame, fname, lineno, function, code_context, index)
        """
        self.logger.debug(inspect.stack()[3])
        return inspect.stack()[3 + trace][3]

    @portable
    def ablation_state(self) -> TBool:
        return self._ablation_on
