import numpy as np

from dax.experiment import *

from demo_system.services.mw_operation import MicrowaveOperationService


# noinspection PyAbstractClass
class MicrowaveOperationSK1Service(MicrowaveOperationService):
    SERVICE_NAME = 'mw_operation_sk1'

    _SK1_PI_2 = np.arccos(-1 / 8) / (2 * np.pi)
    _SK1_PI = np.arccos(-1 / 4) / (2 * np.pi)
    _SK1_MPI_2 = np.arccos(1 / 8) / (2 * np.pi)

    def init(self) -> None:
        # Call super
        super(MicrowaveOperationSK1Service, self).init()

        # Pre-calculate machine units
        self._sk1_pi_2_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(self._SK1_PI_2))
        self._msk1_pi_2_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(-self._SK1_PI_2))
        self._sk1_pi_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(self._SK1_PI))
        self._msk1_pi_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(-self._SK1_PI))

        self._sk1_pi_2_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 + self._SK1_PI_2))
        self._msk1_pi_2_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 - self._SK1_PI_2))
        self._sk1_pi_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 + self._SK1_PI))
        self._msk1_pi_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 - self._SK1_PI))

        self._sk1_mpi_2_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(self._SK1_MPI_2))
        self._msk1_mpi_2_x: np.int32 = np.int32(self._microwave._dds.turns_to_pow(-self._SK1_MPI_2))
        self._sk1_mpi_2_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 + self._SK1_MPI_2))
        self._msk1_mpi_2_y: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.25 - self._SK1_MPI_2))

        self._sk1_pi_h: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.125 + self._SK1_PI))
        self._msk1_pi_h: np.int32 = np.int32(self._microwave._dds.turns_to_pow(0.125 - self._SK1_PI))

        self.update_kernel_invariants(
            '_sk1_pi_2_x', '_msk1_pi_2_x', '_sk1_pi_x', '_msk1_pi_x',
            '_sk1_pi_2_y', '_msk1_pi_2_y', '_sk1_pi_y', '_msk1_pi_y',
            '_sk1_mpi_2_x', '_msk1_mpi_2_x', '_sk1_mpi_2_y', '_msk1_mpi_2_y',
            '_sk1_pi_h', '_msk1_pi_h'
        )

    """Service functionality"""

    @kernel
    def x(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu(), 0)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_pi_x)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_pi_x)

    @kernel
    def y(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu(), self._POW_PI >> 1)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_pi_y)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_pi_y)

    @kernel
    def sqrt_x(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, 0)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_pi_2_x)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_pi_2_x)

    @kernel
    def sqrt_x_dag(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_mpi_2_x)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_mpi_2_x)

    @kernel
    def sqrt_y(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI >> 1)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_pi_2_y)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_pi_2_y)

    @kernel
    def sqrt_y_dag(self, qubit: TInt32 = -1):
        self._pulse_mu(self._duration_pi_mu() >> 1, self._POW_PI_3_4)
        self._pulse_mu(self._duration_pi_mu() << 1, self._sk1_mpi_2_y)
        self._pulse_mu(self._duration_pi_mu() << 1, self._msk1_mpi_2_y)

    @kernel
    def h(self, qubit: TInt32 = -1):
        self.sqrt_x_dag()
        self._pulse_mu(self._duration_pi_mu(), self._POW_PI >> 2)
        self._pulse_mu(self._duration_pi_mu(), self._sk1_pi_h)
        self._pulse_mu(self._duration_pi_mu(), self._msk1_pi_h)
        self.sqrt_x()
