"""
Utility functions.
"""
# Standard Library
import re
import wave

# 3rd party
from PyQt5.QtMultimedia import QAudioFormat
from PyQt5.QtMultimedia import QAudioOutput


def get_audio_output(params):
    """
    Create and return a QAudioOutput from wav params.
    """
    enc = 'audio/pcm'
    fmt = QAudioFormat()
    fmt.setChannelCount(params.nchannels)
    fmt.setSampleRate(params.framerate)
    fmt.setSampleSize(params.sampwidth * 8)
    fmt.setCodec(enc)
    fmt.setByteOrder(QAudioFormat.LittleEndian)
    fmt.setSampleType(QAudioFormat.SignedInt)
    return QAudioOutput(fmt)


def read_wav_info(wav_path):
    """
    Read a wav file and return audio parameters
    """
    with wave.open(wav_path) as wav:
        return wav.getparams()


def parse_command(command):
    """
    >>> parse_command('l1')
    ('l', 1.0)
    """
    res = re.findall(r'([lr])(-?)(.+)', command)[0]
    left_right, sign, amount = res
    amount = float(amount)
    if sign == '-':
        amount = amount * -1
    return left_right, amount
