"""
This program demonstrates how to create a superposition state and store measurements using the data context.
"""

import numpy as np

from dax.program import *
from user import user_id

class PlusState(DaxProgram, Experiment):
    user_id = user_id

    @kernel
    def run(self):
        self.core.reset()

        with self.data_context:
            for _ in range(10):
                self.core.break_realtime()

                self.q.prep_0_all()
                delay(1 * us)
                self.q.h(0)
                delay(1 * us)
                self.q.m_z_all()

                self.q.store_measurements_all()

    def analyze(self):
        data = np.asarray(self.data_context.get_raw())
        self.logger.info(f'Collected data:\n{data}')