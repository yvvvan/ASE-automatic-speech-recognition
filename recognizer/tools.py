import math
import numpy as np
from praatio import tgio
import numpy as np


def sec_to_samples(x, sampling_rate):
    return int(x * sampling_rate)


def next_pow2(x):
    return math.ceil(math.log(x, 2))


def dft_window_size(x, sampling_rate):
    x_len = sec_to_samples(x, sampling_rate)
    p = next_pow2(x_len)
    return 2 ** p


def get_num_frames(signal_length_samples, window_size_samples, hop_size_samples):
    """
    this function is used to calculate the number of total frames in a signal
    :param signal_length_samples: the length of the signal in samples
    :param window_size_samples:   the length of the window in samples
    :param hop_size_samples:      the length of the hop size (not overlapped area) in samples
    :return: how many frames in total
    """
    return math.ceil((signal_length_samples - (window_size_samples - hop_size_samples)) / hop_size_samples)


def hz_to_mel(x):
    """
    this function is used to convert frequency from Hz to Mel
    :param x: the frequency in Hz or an array of frequencies in Hz
    :return: mel value
    """
    return 2595*np.log(1+x/700)


def mel_to_hz(x):
    return 700*(np.exp(x/2595)-1)

def sec_to_frame(x, sampling_rate, hop_size_samples):
    """
    Converts time in seconds to frame index.

    :param x:  time in seconds
    :param sampling_rate:  sampling frequency in hz
    :param hop_size_samples:    hop length in samples
    :return: frame index
    """
    return int(np.floor(sec_to_samples(x, sampling_rate) / hop_size_samples))


def divide_interval(num, start, end):
    """
    Divides the number of states equally to the number of frames in the interval.

    :param num:  number of states.
    :param start: start frame index
    :param end: end frame index
    :return starts: start indexes
    :return end: end indexes
    """
    interval_size = end - start
    # gets remainder
    remainder = interval_size % num
    # init sate count per state with min value
    count = [int((interval_size - remainder)/num)] * num
    # the remainder is assigned to the first n states
    count[:remainder] = [x + 1 for x in count[:remainder]]
    # init starts with first start value
    starts = [start]
    ends = []
    # iterate over the states and sets start and end values
    for c in count[:-1]:
        ends.append(starts[-1] + c)
        starts.append(ends[-1])

    # set last end value
    ends.append(starts[-1] + count[-1])

    return starts, ends


def praat_file_to_target(praat_file, sampling_rate, window_size_samples, hop_size_samples, hmm):
    """
    Reads in praat file and calculates the word-based target matrix.

    :param praat_file: *.TextGrid file.
    :param sampling_rate: sampling frequency in hz
    :param window_size_samples: window length in samples
    :param hop_size_samples: hop length in samples
    :return: target matrix for DNN training
    """
    # gets list of intervals, start, end, and word/phone
    intervals, min_time, max_time = praat_to_interval(praat_file)

    # gets dimensions of target
    max_sample = sec_to_samples(max_time, sampling_rate)
    num_frames = get_num_frames(max_sample, window_size_samples, hop_size_samples)
    num_states = hmm.get_num_states()

    # init target with zeros
    target = np.zeros((num_frames, num_states))

    # parse intervals
    for interval in intervals:
        # get state index, start and end frame
        states = hmm.input_to_state(interval.label)
        start_frame = sec_to_frame(interval.start, sampling_rate, hop_size_samples)
        end_frame = sec_to_frame(interval.end, sampling_rate, hop_size_samples)

        # divide the interval equally to all states
        starts, ends = divide_interval(len(states), start_frame, end_frame)

        # assign one-hot-encoding to all segments of the interval
        for state, start, end in zip(states, starts, ends):
            # set state from start to end to 1
            target[start:end, state] = 1

    # find all columns with only zeros...
    zero_column_idxs = np.argwhere(np.amax(target, axis=1) == 0)
    # ...and set all as silent state
    target[zero_column_idxs, hmm.input_to_state('sil')] = 1

    return target


def praat_to_interval(praat_file):
    """
    Reads in one praat file and returns interval description.

    :param praat_file: *.TextGrid file path

    :return itervals: returns list of intervals,
                        containing start and end time and the corresponding word/phone.
    :return min_time: min timestamp of audio (should be 0)
    :return max_time: min timestamp of audio (should be audio file length)
    """
    # read in praat file (expects one *.TextGrid file path)
    tg = tgio.openTextgrid(praat_file)

    # read return values
    itervals = tg.tierDict['words'].entryList
    min_time = tg.minTimestamp
    max_time = tg.maxTimestamp

    # we will read in word-based
    return itervals, min_time, max_time


def viterbi( logLike, logPi, logA ):
    """
    Viterbi-Algorithm for HMM
    :param logLike:  log(likelihood) of the observations  b(o_t)
    :param logPi:    log(initial state)
    :param logA:     log(transition matrix)
    :return:
    stateSequence:   most likely state sequence [i_1, i_2, ..., i_T]
    pStar: p*(o|λ), max. probability of the most likely state sequence
    """
    # T: number of observations, N: number of states
    T, N = logLike.shape

    # phi[t, i] = max. probability of the most likely path ending in state i at time t
    phi = np.zeros((T, N))
    # psi[t, i] = the best previous state(argmax) at time t-1 [i_t-1] that bring us to this state i at time t
    psi = np.zeros((T, N), dtype=int)

    phi[0, :] = logPi + logLike[0, :]  # initial probability at time t=0   # multiply in log domain = add
    psi[0, :] = -1                     # no previous state at time t=0

    for t in range(1, T):   # time
        for j in range(N):  # state(nodes)
            phi[t, j] = np.max(phi[t - 1, :] + logA[:, j]) + logLike[t, j]
            psi[t, j] = np.argmax(phi[t - 1, :] + logA[:, j])

    # p*: the max. probability of the most likely path ending in state i at final time T
    # in coding, because T is length of the time array, so T-1 is the last time
    pStar = np.max(phi[T - 1, :])
    # i*: the state sequence that gives the p*
    stateSequence = np.zeros(T, dtype=int)
    # so last state is the state with the highest probability
    stateSequence[T - 1] = np.argmax(phi[T - 1, :])
    # so data saved in psi[t,j] shows the previous state of j, j is the last state we found in the last line
    for t in range(T - 2, -1, -1):  # backtracking
        # the state at time t = the saved *previous state* at time t+1 = the data saved in psi[t+1,j]
        stateSequence[t] = psi[t + 1, stateSequence[t + 1]]
    return stateSequence, pStar


def limLog(x):
    """
    Log of x.

    :param x: numpy array.
    :return: log of x.
    """
    MINLOG = 1e-100
    return np.log(np.maximum(x, MINLOG))


def _needlemann_wunsch(reference, transcript):
    """
    Dynamic programming algorithm to align true transcription with output sequence in order to find the smallest distance.

    :param reference: Reference sequence (true transcription).
    :param transcript: output of viterbi

    :return ref_align: Alignment for reference.
    :return trans_align: Alignment for transcript.
    """
    gap_score = -1
    sim_func = lambda x, y: 0 if x == y else -1

    n_ref = len(reference)
    n_trans = len(transcript)
    d_mat = np.zeros(shape=[n_trans + 1, n_ref + 1, ])
    # Initialize the dynamic programming calculation using base conditions
    for idr in range(n_ref + 1):
        d_mat[0, idr] = gap_score * idr
    for idt in range(n_trans + 1):
        d_mat[idt, 0] = gap_score * idt

    # Calculate all D[i,j]
    for i in range(1, n_trans + 1):
        for j in range(1, n_ref + 1):
            match = d_mat[i - 1, j - 1] + sim_func(reference[j - 1], transcript[i - 1])
            gaps = d_mat[i, j - 1] + gap_score
            gapt = d_mat[i - 1, j] + gap_score
            d_mat[i, j] = np.max([match, gaps, gapt])

    # Do the Traceback to create the alignment
    i = n_trans
    j = n_ref
    ref_align = []
    trans_align = []
    while (i > 0) and (j > 0):
        if d_mat[i, j] - sim_func(reference[j - 1], transcript[i - 1]) == d_mat[i - 1, j - 1]:
            ref_align.insert(0, reference[j - 1])
            trans_align.insert(0, transcript[i - 1])
            i = i - 1
            j = j - 1
        elif d_mat[i, j] - gap_score == d_mat[i, j - 1]:
            ref_align.insert(0, reference[j - 1])
            trans_align.insert(0, None)
            j = j - 1
        elif d_mat[i, j] - gap_score == d_mat[i - 1, j]:
            ref_align.insert(0, None)
            trans_align.insert(0, transcript[i - 1])
            i = i - 1
        else:
            raise ('should not happen')

    while j > 0:
        ref_align.insert(0, reference[j - 1])
        trans_align.insert(0, None)
        j = j - 1

    while i > 0:
        ref_align.insert(0, None)
        trans_align.insert(0, transcript[i - 1])
        i = i - 1

    return (ref_align, trans_align)


def needlemann_wunsch(reference, transcript):
    """
    Counts number of errors.

    :param reference: Reference sequence (true transcription).
    :param transcript: output of viterbi

    :return N: Total number of words.
    :return D: Number of deleted words.
    :return I: Number of inserted words.
    :return S: Number of substituted words.
    """
    insertions = 0
    deletions = 0
    substitutions = 0
    ref_align, trans_align = _needlemann_wunsch(reference, transcript)
    for idr in range(len(ref_align)):
        if ref_align[idr] is None:
            insertions += 1
        elif trans_align[idr] is None:
            deletions += 1
        elif ref_align[idr] != trans_align[idr]:
            substitutions += 1

    return len(reference), deletions, insertions, substitutions

