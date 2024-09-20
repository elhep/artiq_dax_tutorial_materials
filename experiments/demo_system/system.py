from dax.experiment import *

from dax.modules.rpc_benchmark import RpcBenchmarkModule
from dax.modules.rtio_benchmark import RtioLoopBenchmarkModule
from dax.modules.cpld_init import CpldInitModule

from demo_system.modules.properties import PropertiesModule
from demo_system.modules.cw_laser import Laser355, Laser370
from demo_system.modules.pmt import PmtModule
from demo_system.modules.ablation import AblationModule
from demo_system.modules.trigger_ttl import TriggerTTLModule
from demo_system.modules.microwave import MicrowaveModule
from demo_system.modules.scope import ScopeModule

from demo_system.services.ion_load import IonLoadService
from demo_system.services.detection import DetectionService
from demo_system.services.cool_prep import CoolInitService
from demo_system.services.state import StateService

from demo_system.services.mw_operation import MicrowaveOperationService
from demo_system.services.mw_operation_sk1 import MicrowaveOperationSK1Service

class DemoSystem(DaxSystem):
    SYS_ID = "demo_system"  # Unique system identifier for archiving data
    SYS_VER = 1  # Tag for archiving data, increment with major hardware changes

    # system datasets
    MON_PMT_ENABLED_KEY: str = "monitoring_pmt_enabled"
    DAX_INFLUX_DB_KEY: str = None

    user_id = "-1"

    def build(self) -> None:
        # Call super, obtains core devices
        super(DemoSystem, self).build()

        # Add standard modules
        self.rpc_bench = RpcBenchmarkModule(self, "rpc_bench")
        self.rtio_bench = RtioLoopBenchmarkModule(
            self,
            "rtio_bench",
            ttl_out="ttl3",
            ttl_in="ttl7",
            init_kernel=False,
        )
        self.cpld = CpldInitModule(self, "cpld_init", init_kernel=False)
        self.update_kernel_invariants("rpc_bench", "rtio_bench", "cpld")

        # Add meta-modules
        self.properties = PropertiesModule(self, "properties")

        # Get system configuration (read-only)
        mon_pmt_enabled: bool = self.get_dataset_sys(self.MON_PMT_ENABLED_KEY)
        assert isinstance(
            mon_pmt_enabled, bool
        ), "Monitoring PMT enabled flag must be of type bool"

        # Add modules
        self.l355 = Laser355(self, "l355")
        self.l370 = Laser370(self, "l370")
        self.pmt = PmtModule(self, "pmt")
        self.ablation = AblationModule(self, "ablation")
        self.trigger_ttl = TriggerTTLModule(self, "trigger_ttl")
        self.microwave = MicrowaveModule(self, "microwave")
        self.scope = ScopeModule(self, "scope", user_id = self.user_id)
        self.update_kernel_invariants("l355", "l370", "pmt", "ablation", "trigger_ttl", "microwave", "scope")

        # Add other devices
        self.scheduler = self.get_device("scheduler")
        self.update_kernel_invariants("scheduler")

        # Add services
        self.detection = DetectionService(self)
        self.cool_prep = CoolInitService(self)
        self.state = StateService(self)
        self.ion_load = IonLoadService(self)
        self.update_kernel_invariants(
            "ion_load", "detection", "cool_prep", "state"
        )

        # Add operation interfaces
        self.mw_operation = MicrowaveOperationService(self)
        self.mw_operation_sk1 = MicrowaveOperationSK1Service(self)
        self.update_kernel_invariants("mw_operation", "mw_operation_sk1")

    @kernel
    def init(self):
        """Joint kernel to initialize various modules.

        By manually initializing modules in a single kernel, the number of compiler runs
        can be reduced with faster initialization as a result.
        """
        # Call initialization kernel functions (they include calls to reset() and wait_until_mu()
        self.cpld.init_kernel()
        self.rtio_bench.init_kernel()
        self.l355.init_kernel()
        self.l370.init_kernel()
        self.pmt.init_kernel()
        self.trigger_ttl.init_kernel()

        # self.idle()

    @kernel
    def idle(self):
        # Set system to idle (between experiments) state
        self.core.break_realtime()
        self.l370.reset()
        self.core.break_realtime()
        self.l355.reset()

    @kernel
    def safety_off(self):
        # Safely turn off system
        self.core.break_realtime()
        self.l370.safety_off()
        self.core.break_realtime()
        self.l355.safety_off()


    def post_init(self) -> None:
        # Log message for user convenience
        self.logger.info(f"Start experiment with RID: {self.scheduler.rid}")

    def post_run(self) -> None:
        self.scope.store_waveform()