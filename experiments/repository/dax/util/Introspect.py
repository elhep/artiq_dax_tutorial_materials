import dax.clients.introspect

from demo_system.system import DemoSystem


class Introspect(dax.clients.introspect.Introspect(DemoSystem)):
    """Introspect"""
    pass
