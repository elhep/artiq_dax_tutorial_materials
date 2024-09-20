from artiq.experiment import *

from demo_system.system import DemoSystem


class InjectCooling(DemoSystem, EnvExperiment):
    """Inject Cooling"""

    _service_states = ["On", "Off", "Default", "Pulse"]

    def build(self):
        # Get Devices
        super(InjectCooling, self).build()

        # Doppler
        self.doppler_state = self.get_argument(
            "State",
            processor=EnumerationValue(self._service_states, "Default"),
            group="Doppler",
            tooltip="Set Service state",
        )

        self.doppler_pulse_duration = self.get_argument(
            "Pulse Duration",
            processor=NumberValue(0 * us, "us", min=0 * us),
            group="Doppler",
            tooltip="Set pulse mode pulse duration",
        )

        self.doppler_update_defaults = self.get_argument(
            "Update Defaults",
            processor=BooleanValue(True),
            group="Doppler",
            tooltip="Reset DDS to Dataset settings",
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
            "doppler_state",
            "doppler_pulse_duration",
            "doppler_update_defaults",
            "pre_delay",
            "post_delay",
        )

    def prepare(self):
        self.dax_init()
        pass

    @kernel
    def run(self):
        # Reset the core
        self.core.reset()

        # Pre-delay
        delay(self.pre_delay)

        self.inject_cooling()

        # Post-wait time
        delay(self.post_delay)
        self.core.wait_until_mu(now_mu())

    @kernel
    def inject_cooling(self):
        self.inject_doppler()

    @kernel
    def inject_doppler(self):
        self.core.break_realtime()
        self.core.break_realtime()

        if self.doppler_state == "On":
            self.cool_prep.cool.on()
        elif self.doppler_state == "Off":
            self.cool_prep.cool.off()
        elif self.doppler_state == "Pulse":
            self.cool_prep.cool.pulse(self.doppler_pulse_duration)
        elif self.doppler_state == "Default":
            self.cool_prep.cool.reset()
        else:
            self.cool_prep.cool.safety_off()
            self.logger.error("Invalid state provided")
        self.core.break_realtime()
