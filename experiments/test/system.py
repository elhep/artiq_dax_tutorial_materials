from demo_system.system import *


class DemoTestSystem(DemoSystem):
    def build(self, *, mon_pmt_enabled: bool = False) -> None:
        assert isinstance(mon_pmt_enabled, bool)
        # Inject system config before build()
        self.set_dataset_sys(self.MON_PMT_ENABLED_KEY, mon_pmt_enabled, data_store=False)
        self.DAX_INFLUX_DB_KEY = None
        # Call super() to build system
        super(DemoTestSystem, self).build()
