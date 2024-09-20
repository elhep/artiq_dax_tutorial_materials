import io
import numpy as np

from artiq.experiment import *
from PIL import Image


class Scope:

    def __init__(self, experiment: EnvExperiment, user_id, scope="scope"):
        self.experiment = experiment
        self.user_id = user_id
        self.scope = experiment.get_device(scope)

    def setup(self, reset=False, sleep_time=3.0):
        self.scope.setup(
            channel_configs=[
                {
                    "channel": 1,
                    "vertical_scale": 2.5,
                    "vertical_position": 3,
                    "termination_fifty_ohms": False,
                    "label": "DIO SMA 0",
                    "ac_coupling": False
                },
                {
                    "channel": 2,
                    "vertical_scale": 1,
                    "vertical_position": 1.0,
                    "termination_fifty_ohms": True,
                    "label": "Urukul 0",
                    "ac_coupling": True
                },
                {
                    "channel": 3,
                    "vertical_scale": 1,
                    "vertical_position": -1.0,
                    "termination_fifty_ohms": True,
                    "label": "Urukul 1",
                    "ac_coupling": True
                },
                {
                    "channel": 4,
                    "vertical_scale": 0.5,
                    "vertical_position": -3.0,
                    "termination_fifty_ohms": True,
                    "label": "Phaser RF 0",
                    "ac_coupling": True
                }
            ],
            horizontal_scale=100*ns,
            horizontal_position=400*ns,
            trigger_config={
                "channel": 1,
                "level": 2.5,
                "slope": "RISE",
                "mode": "NORMAL"
            },
            queue=True,
            reset=reset
        )
        self.scope.run_queue(sleep_time=sleep_time)

    def store_waveform(self):
        im = Image.open(io.BytesIO(self.scope.get_screen_png()))
        im = np.array(im)
        im = np.rot90(im, 1, (0, 1))
        im = np.flip(im, 1)
        im = np.flip(im, 0)
        self.experiment.set_dataset(
            f"scope_{self.user_id}", im, broadcast=True)
