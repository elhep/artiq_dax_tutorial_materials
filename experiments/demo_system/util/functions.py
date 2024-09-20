"""
Mathematical functions for post-analysis.

Convention: all frequencies are expressed in omega/2pi form.

This file was inherited from STAQ and was initially created by Jacob Whitlow.
"""

import numpy as np

""" General useful fitting functions """


def linear(x, a, b):
    return a * x + b


def sinusoidal(x, amp, freq, phase, offset):
    return amp * np.sin(2.0 * np.pi * freq * x + phase) + offset


def exp_decay(x, amp, decay_constant):
    return amp * np.exp((-1.0) * x / decay_constant)


def sinusoidal_decay(x, amp, freq, phase, offset, decay_constant):
    return amp * np.exp((-1.0) * x / decay_constant) * np.sin(2.0 * np.pi * freq * x + phase) + offset


def sinc_squared(x, amp, center, width):
    return amp * np.sinc((x - center) / width) ** 2


def gaussian(x, amp, center, sigma):
    return amp * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))


""" Experiment specific functions """


def rabi_oscillation(time, frequency, rabi_freq, resonance):
    """
    Rabi oscillation function
    assumed the qubit is initialized in |0> state

    :param time: Rabi pulse time in second
    :param frequency: applied pulse frequency in Hz unit
    :param rabi_freq: on-resonance rabi frequency in Hz unit (omega/2pi)
    :param resonance: intrinsic resonance frequency of two-level system in Hz unit
    :return: upper state population after rabi pulse
    """
    detuning = frequency - resonance
    rabi_eff = np.sqrt(rabi_freq ** 2 + detuning ** 2)
    return rabi_freq / rabi_eff * np.sin(np.pi * rabi_eff * time) ** 2


def rabi_oscillation_flattened(tf_point, rabi_freq, resonance):
    return rabi_oscillation(tf_point[0], tf_point[1], rabi_freq, resonance)


def rabi_oscillation_off_resonance(time, rabi_freq):
    """
    Off resonance rabi oscillation function

    :param time: Rabi pulse time in second
    :param rabi_freq: on-resonance rabi frequency in Hz unit (omega/2pi)
    :return: upper state population after rabi pulse
    """
    return rabi_oscillation(time, 0, rabi_freq, 0)


def rabi_oscillation_on_resonance(time, rabi_freq):
    """
    On resonance rabi oscillation function

    :param time: Rabi pulse time in second
    :param rabi_freq: on-resonance rabi frequency in Hz unit (omega/2pi)
    :return: upper state population after rabi pulse
    """
    return rabi_oscillation(time, 0, rabi_freq, 0)


def rabi_freq_to_pi_time(rabi_freq):
    """ calculate pi pulse time from rabi frequency """
    return 1 / 2 / rabi_freq


def ramsey_fringe(freq, delay_time, rabi_freq, resonance):
    """
    ramsey oscillation

    :param freq: applied pulse frequency in Hz unit
    :param delay_time: delay time between two half-pi pulse in seconds
    :param rabi_freq: on-resonance rabi frequency in Hz unit (omega/2pi)
    :param resonance: intrinsic resonance frequency of two-level system in Hz unit
    :return: upper state population after ramsey interferometry
    """

    detuning = freq - resonance
    rabi_freq_eff = np.sqrt(rabi_freq * rabi_freq + detuning * detuning)
    t = delay_time

    fringe = rabi_freq ** 2 / rabi_freq_eff ** 4 * np.sin(np.pi / 2 * rabi_freq_eff / rabi_freq) ** 2
    fringe *= (rabi_freq_eff * np.cos(np.pi * (1 / 4 - t * rabi_freq) * detuning / rabi_freq)
               + detuning * np.sin(np.pi * (1 / 4 - t * rabi_freq) * detuning / rabi_freq)
               * np.tan(rabi_freq_eff / rabi_freq * np.pi / 4)) ** 2

    return fringe


def simple_ramsey_fringe(freq, delay_time, resonance):
    """
     approximated ramsey oscillation near resonance.
     valid when detuning < on-resonance rabi freq

     :param freq: applied pulse frequency in Hz unit
     :param delay_time: delay time between two half-pi pulse in seconds
     :param resonance: intrinsic resonance frequency of two-level system in Hz unit
     :return: upper state population after ramsey interferometry
     """

    detuning = freq - resonance

    return np.cos(np.pi * delay_time * detuning) ** 2


def phase_oscillation(phase, amp, phase_offset, offset):
    return amp * np.sin(2.0 * np.pi * (phase - phase_offset)) + offset


""" useful functions """


def find_oscillation_freq(data, time_step):
    """
    find main oscillation peak, using FFT to find modulation peak
    :param data: data to be analyzed
    :param time_step: time step in seconds, data should have a constant time-interval between points
    :return: main oscillation frequency in angular freq/2pi
    """

    fft = np.fft.fft(data)
    fft_power = np.absolute(fft)[1:]  # exclude DC (f=0) components
    fft_freq = np.fft.fftfreq(len(data), time_step)[1:]
    peak_freq = abs(fft_freq[fft_power.argmax()])
    return peak_freq


def get_sample_interval(array):
    arr = np.array(array)
    return (arr.max() - arr.min()) / (arr.size - 1)
