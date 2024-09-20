import typing

from dax.experiment import *

from demo_system.modules.util.dds import DDS9910
from demo_system.modules.util.switch import Switch


class MODES370:
    COOL = 0
    Prep = 1
    DETECT = 2
    OFF = 3
    NONE = -1

    modes_list_int = [COOL, Prep, DETECT, OFF]
    modes_list_str = ["Cool", "Prep", "Detect", "OFF"]


class Laser370(DaxModule):

    _dds_dict: typing.Dict[str, DDS9910] = {}
    _dds_list: typing.List[DDS9910] = []
    kernel_invariants = {"_dds_list"}

    mode = MODES370.OFF

    MODES = MODES370

    _cool_freq = 100 * MHz
    _cool_amp = .5

    _prep_freq = 150 * MHz
    _prep_amp = .75

    _detect_freq = 200 * MHz
    _detect_amp = 1.0

    def build(self):
        super(Laser370, self).build()
        # Instantiate laser modules
        self._shutter = DDS9910(
            self,
            "shutter",
            dds_key="urukul0_ch1",
            default_freq=250 * MHz,
            default_att=10 * dB,
            default_amp=1.0,
            min_att=10.0,
            default_sw=True
        )
        self._detect_prep_cool_dds = DDS9910(
            self,
            "detect_prep_cool_dds",
            dds_key="urukul0_ch2",
            default_freq=self._cool_freq,
            default_att=10 * dB,
            default_amp=self._cool_amp,
            min_att=10.0,
            default_sw=True
        )
        self._cool_sw = Switch(
            self,
            "doppler_sw",
            sw_key="ttl2",
            default_state=True
        )

        self.update_kernel_invariants(
            "_shutter",
            "_detect_prep_cool_dds",
            "_cool_sw"
        )

        # All dds
        self._dds_dict: typing.Dict[str, DDS9910] = {
            "shutter": self._shutter,
            "detect_prep_cool_dds": self._detect_prep_cool_dds,
        }
        self._dds_list = list(self._dds_dict.values())

        # All sw
        self._sw_dict: typing.Dict[str, Switch] = {
            "cool": self._cool_sw,
        }
        self._sw_list = list(self._sw_dict.values())

    def init(self, *, force: bool = False) -> None:
        """Initialize this module.

        :param force: Force full initialization
        """
        if force:
            # Initialize devices
            self.init_kernel()

    def post_init(self):
        pass

    @kernel
    def init_kernel(self, debug=False):
        # Initialize submodules
        for dds in self._dds_list:
            dds.init_kernel()
        for sw in self._sw_list:
            sw.init_kernel()
        # Set to Idle state
        self.core.break_realtime()
        self.reset()


        self.core.wait_until_mu(now_mu())

    """Module Base Functions"""

    @kernel
    def safety_off(self):
        """Turn off all sw/dds safely"""
        for dds in self._dds_list:
            dds.safety_off()
        for sw in self._sw_list:
            sw.safety_off()
        self.mode = MODES370.OFF

    @kernel
    def reset(self, realtime: TBool = False):
        """Reset module to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        # Set system to idle cooling
        self.set_state(state=True, mode=MODES370.COOL, realtime=realtime)

        # Reset configuration
        for dds in self._dds_list:
            dds.reset_config(realtime=realtime)
            dds.reset_att(realtime=realtime)

    @host_only
    def update_latency(self):
        """Update all latencies"""
        for dds in self._dds_list:
            dds.update_latency()

    @host_only
    def clear_latency(self):
        """Clear all latencies"""
        for dds in self._dds_list:
            dds.clear_latency()

    """Module functionality"""

    @kernel
    def set_state(self, mode: TInt32, state: TBool, realtime: TBool = False):
        """
        Configure the 370 laser to a mode and set the state
        :param state: `True` to turn on, `False` to turn off
        :param mode: see self.MODE enumeration
        :param realtime: Compensate for programming latencies
        """
        # Configure mode
        self.config_mode(mode=mode, realtime=realtime)
        self.set_shutter(state=state, realtime=realtime)

    @kernel
    def config_mode(self, mode: TInt32, realtime: TBool = False):
        """
        Configure the 370 laser to a specified mode, moves cursor 10ns
        :param mode: see self.STATE enumeration
        :param realtime: Compensate for programming latencies
        """
        # Configure DDS Frequency
        if mode == MODES370.COOL:
            self._detect_prep_cool_dds.config_freq(self._cool_freq, realtime=realtime)
            self._detect_prep_cool_dds.config_amp(self._cool_amp, realtime=realtime)
        elif mode == MODES370.Prep:
            self._detect_prep_cool_dds.config_freq(self._prep_freq, realtime=realtime)
            self._detect_prep_cool_dds.config_amp(self._prep_amp, realtime=realtime)
        elif mode == MODES370.DETECT:
            self._detect_prep_cool_dds.config_freq(self._detect_freq, realtime=realtime)
            self._detect_prep_cool_dds.config_amp(self._detect_amp, realtime=realtime)
        delay(1*us)
        # Enable DDS
        self._detect_prep_cool_dds.set(mode != MODES370.OFF, realtime=realtime)
        # Enable Sidebands
        self._cool_sw.set(mode == MODES370.COOL, realtime=realtime)

        self.mode = mode

    @kernel
    def set_shutter(self, state: TBool, realtime: TBool = False):
        """
        Set the shutter state
        :param state: `True` to open, `False` to close
        :param realtime: Compensate for programming latencies
        """
        self._shutter.set(state, realtime=realtime)


class Laser355(DaxModule):
    _dds_dict: typing.Dict[str, DDS9910] = {}
    _sw_dict: typing.Dict[str, Switch] = {}
    _dds_list: typing.List[DDS9910] = []
    _sw_list: typing.List[Switch] = []
    kernel_invariants = {"_dds_list", "_sw_list"}

    def build(self):
        super(Laser355, self).build()
        # Instantiate laser modules
        self._shutter = DDS9910(
            self,
            "shutter",
            dds_key="urukul0_ch3",
            default_freq=205.75 * MHz,
            default_att=11 * dB,
            min_att=10.0,
        )

        self.update_kernel_invariants(
            "_shutter",
        )
        self._dds_dict: typing.Dict[str, DDS9910] = {
            "shutter": self._shutter,
        }

        self._dds_list = list(self._dds_dict.values())

    def init(self, *, force: bool = False) -> None:
        """Initialize this module.

        :param force: Force full initialization
        """
        if force:
            # Initialize devices
            self.init_kernel()

    def post_init(self) -> None:
        pass

    @kernel
    def init_kernel(self):
        for dds in self._dds_list:
            dds.init_kernel()

        self.core.break_realtime()
        self.reset()

    """Module Base Functions"""

    @kernel
    def safety_off(self):
        """Turn off all sw/dds safely"""
        for dds in self._dds_list:
            dds.safety_off()

    @kernel
    def reset(self, realtime: TBool = False):
        """Reset laser state to default state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        # Set output to default
        self.set_shutter(state=False, realtime=realtime)

        # Reset DDS Configs
        for dds in self._dds_list:
            dds.reset_config(realtime=realtime)
            dds.reset_att(realtime=realtime)

    @host_only
    def update_latency(self):
        """Update all latencies"""
        for dds in self._dds_list:
            dds.update_latency()

    @host_only
    def clear_latency(self):
        """Clear all latencies"""
        for dds in self._dds_list:
            dds.clear_latency()

    """Module functionality"""

    @kernel
    def set_shutter(self, state, realtime: TBool = False):
        """Set 355 shutter state
        :param state: Shutter state
        :param realtime: :const:`True` to compensate for programming latencies
        """
        self._shutter.set(state, realtime=realtime)
