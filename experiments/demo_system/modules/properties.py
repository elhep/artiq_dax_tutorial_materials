import numpy as np

from dax.experiment import *


class PropertiesModule(DaxModule):
    """Meta-module for storing system properties.

    This module contains optional attributes that are only available when the value has been stored before.
    If the corresponding key has a value, it will be assigned to a kernel invariant attribute with the name of the key.
    If the key is not available, the attribute will not be set.
    Attributes should be accessed directly, and a compile/attribute error is raised if the attribute is not available.
    """

    # System dataset keys
    NUM_IONS_KEY = 'num_ions'

    @host_only
    def init(self) -> None:
        """Initialize this meta-module."""
        self._num_ions = self.get_dataset_sys(self.NUM_IONS_KEY, 0)
        self.update_kernel_invariants('_num_ions')

    @host_only
    def post_init(self) -> None:
        pass

    """Module functionality"""

    @property
    def num_ions(self) -> np.int32:
        return np.int32(self._num_ions)

    @host_only
    def set_num_ions(self, num_ions: int) -> None:
        """Update the number of ions (no re-initialization required)."""
        assert isinstance(num_ions, (int, np.int32))
        assert num_ions >= 0

        # Store value locally and in the system dataset
        self._num_ions = num_ions
        self.set_dataset_sys(self.NUM_IONS_KEY, int(self._num_ions))
