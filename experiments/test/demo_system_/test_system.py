import dax.sim.test_case
import dax.base.system

from test.system import DemoTestSystem


class SystemTestCase(dax.sim.test_case.PeekTestCase):
    MON_PMT_ENABLED: bool = False

    def test_kernel_invariants(self):
        # Construct system environment
        env = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py",
                                 build_kwargs={'mon_pmt_enabled': self.MON_PMT_ENABLED})
        env.dax_init()

        # Test modules
        for m in env.registry.get_module_list():
            self._test_kernel_invariants(m)
        # Test services
        for s in env.registry.get_service_list():
            self._test_kernel_invariants(s)

    def _test_kernel_invariants(self, component: dax.base.system.DaxHasSystem):
        # Test kernel invariants of this component
        for k in component.kernel_invariants:
            self.assertTrue(hasattr(component, k), 'Name "{:s}" of "{:s}" was marked kernel invariant, but this '
                                                   'attribute does not exist'.format(k, component.get_system_key()))


class SystemTestCaseMonPmtEnabled(SystemTestCase):
    MON_PMT_ENABLED = True
