import math


def sec_to_samples(x, sampling_rate):
    return x * sampling_rate


def next_pow2(x):
    return math.ceil(math.log(x, 2))


def dft_window_size(x, sampling_rate):
    x_len = sec_to_samples(x, sampling_rate)
    p = next_pow2(x_len)
    return 2 ** p


def get_num_frames(signal_length_samples, window_size_samples, hop_size_samples):
    return math.ceil((signal_length_samples-(window_size_samples-hop_size_samples))/hop_size_samples)