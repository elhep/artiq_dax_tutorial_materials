import dax.sim.test_case

# from demo_system.modules.ablation import AblationModule

from test.system import DemoTestSystem


class TrapTestCase(dax.sim.test_case.PeekTestCase):
    def setUp(self):
        # Construct system environment
        self.env = self.construct_env(DemoTestSystem, device_db="experiments/device_db_sim.py")
        # Initialize
        self.env.dax_init()

    def test_ablation(self):
        # Ensure that the ablation pulse is triggered
        self.assertEqual(self.env.ablation.ablation_state(), False)
        with self.env.ablation:
            self.assertEqual(self.env.ablation.ablation_state(), False)
            self.env.ablation.on()
            self.assertEqual(self.env.ablation.ablation_state(), True)
            self.env.ablation.off()
            self.assertEqual(self.env.ablation.ablation_state(), False)
        self.assertEqual(self.env.ablation.ablation_state(), False)

    def test_ablation_out_of_context(self):
        self.assertEqual(self.env.ablation.ablation_state(), False)
        self.env.ablation.on()
        self.assertEqual(self.env.ablation.ablation_state(), False)

    def test_ablation_toggle_in_context(self):
        # Ensure that the ablation pulse is triggered
        self.assertEqual(self.env.ablation.ablation_state(), False)
        with self.env.ablation:
            self.env.ablation.on()
            self.assertEqual(self.env.ablation.ablation_state(), True)
            self.env.ablation.off()
            self.assertEqual(self.env.ablation.ablation_state(), False)
            self.env.ablation.on()
            self.assertEqual(self.env.ablation.ablation_state(), True)
        self.assertEqual(self.env.ablation.ablation_state(), False)
