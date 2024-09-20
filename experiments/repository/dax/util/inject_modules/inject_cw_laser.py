from artiq.experiment import *

from demo_system.system import DemoSystem

class InjectCWLaser(DemoSystem, EnvExperiment):
    """Inject CW"""

    def build(self):
        # Get Devices
        super(InjectCWLaser, self).build()
        # CW Set
        self.update_defaults = self.get_argument(
            "Update Config",
            processor=BooleanValue(True),
            group="CW",
            tooltip="Update DDS Configuration",
        )

        self.realtime = self.get_argument(
            "Realtime",
            processor=BooleanValue(True),
            group="CW",
            tooltip="Perform SW latency corrections",
        )
        self.l370_mode = self.get_argument(
            "370 Mode",
            processor=EnumerationValue(self.l370.MODES.modes_list_str, "Cool"),
            group="CW",
            tooltip="370 Mode",
        )

        self.l370_set = self.get_argument(
            "370 Set",
            processor=BooleanValue(False),
            group="CW",
            tooltip="Sets the 370 for the given mode",
        )

        self.ionize_set = self.get_argument(
            "Ionize Set",
            processor=BooleanValue(False),
            group="CW",
            tooltip="Sets the Ionization Laser",
        )

        self.idle_ = self.get_argument(
            "Idle",
            processor=BooleanValue(False),
            group="CW",
            tooltip="Sets all to the Idle state",
        )

        self.off = self.get_argument(
            "Off",
            processor=BooleanValue(False),
            group="CW",
            tooltip="Sets all to the Off state",
        )

        # Timing arguments
        self.pre_delay = self.get_argument(
            "Pre-delay time",
            processor=NumberValue(10 * ms, "ms", step=1 * ms, min=0 * ms),
            group="Delays",
            tooltip="Wait time before configuring the device",
        )
        self.post_delay = self.get_argument(
            "Post-delay time",
            processor=NumberValue(0 * s, "s", step=1 * s, min=0 * s),
            group="Delays",
            tooltip="Wait time after the device is configured",
        )

        self.update_kernel_invariants(
            "l370_mode",
            "l370_set",
            "ionize_set",
            "idle",
            "pre_delay",
            "post_delay",
        )

        
    def prepare(self):
        self.l370_mode = self.l370.MODES.modes_list_str.index(self.l370_mode)
        pass

    @host_only
    def run(self):
        self.dax_init()

        self.run_kernel()
        self.post_run()

    @kernel
    def run_kernel(self):
        # Reset the core
        self.core.reset()

        self.trigger_ttl.pulse(10 * ns)

        # Pre-delay
        delay(self.pre_delay)

        self.inject_cw_laser()

        # Post-wait time
        delay(self.post_delay)
        self.scope.store_waveform()
        self.core.wait_until_mu(now_mu())

    @kernel
    def inject_cw_laser(self):
        self.core.break_realtime()
        if self.update_defaults:
            self.l355.reset()
            self.l370.reset()
        self.l370.safety_off()
        self.core.break_realtime()
        self.l370.set_state(
            mode=self.l370_mode, state=self.l370_set, realtime=self.realtime
        )
        delay(10 * us)

        self.l355.set_shutter(self.ionize_set)

        delay(10 * us)
        if self.idle_:
            self.l355.reset()
            self.l370.reset()

        if self.off:
            self.l355.safety_off()
            self.l370.safety_off()
