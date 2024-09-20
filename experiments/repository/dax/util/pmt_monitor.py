import dax.clients.pmt_monitor

from demo_system.system import DemoSystem


class PmtMonitor(dax.clients.pmt_monitor.PmtMonitor(DemoSystem)):
    """PMT monitor"""

    DEFAULT_BUFFER_SIZE = 2
    DEFAULT_SLIDING_WINDOW_SIZE = 60


class MultiPmtMonitor(dax.clients.pmt_monitor.MultiPmtMonitor(DemoSystem)):
    """Multi PMT monitor"""

    DEFAULT_BUFFER_SIZE = 3
    DEFAULT_SLIDING_WINDOW_SIZE = 60
    DEFAULT_APPLET_UPDATE_DELAY = 0.2
