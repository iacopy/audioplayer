#!/usr/bin/python
"""
Play audio regions of a wav file.
"""

# Standard Library
import random
import sys
import time
import wave

# 3rd party
from PyQt5 import QtWidgets
from PyQt5.QtCore import QBuffer
from PyQt5.QtCore import QIODevice
from PyQt5.QtMultimedia import QAudio
from PyQt5.QtMultimedia import QAudioFormat
from PyQt5.QtMultimedia import QAudioOutput
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow


REG_SECONDS = 2


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


class MainWindow(QMainWindow):
    def __init__(self, wav_path):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle('MainWindow')

        self._setLayout()

        self.wav_path = wav_path
        self.params = read_wav_info(wav_path)
        self.reg_nframes = int(self.params.framerate * REG_SECONDS)
        self.duration = self.params.nframes / self.params.framerate

        self.output = get_audio_output(self.params)
        self.output.stateChanged.connect(self.state_checkpoint)
        self.output.setNotifyInterval(20)

        self.output.notify.connect(self.notified)
        self.play_button.clicked.connect(self.play_pause)
        self.random_button.clicked.connect(self.set_random_region)

        self.loop_enabled = False

        self.buffer = QBuffer()
        self.set_random_region()

    def _setLayout(self):
        widget = QtWidgets.QWidget()

        grid = QtWidgets.QGridLayout(widget)
        self.progressBar = QtWidgets.QProgressBar(widget)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.play_button = QtWidgets.QPushButton('Play | Stop', widget)
        self.random_button = QtWidgets.QPushButton('Random', widget)

        grid.addWidget(self.progressBar, 0, 0, 1, 3)
        grid.addWidget(self.play_button, 1, 1)
        grid.addWidget(self.random_button, 1, 2)

        widget.setLayout(grid)
        self.setCentralWidget(widget)

    def play(self):
        """
        Play from the beginning.
        """
        if self.buffer.isOpen():
            state = self.output.state()
            if state != QAudio.StoppedState:
                self.output.stop()
            if sys.platform == 'darwin':
                self.buffer.close()
                self.buffer.open(QIODevice.ReadOnly)
            else:
                # I found this way does not works on OS X
                self.buffer.seek(0)
        else:
            # Load from file
            self.buffer.open(QIODevice.ReadOnly)
        self.output.start(self.buffer)

    def play_pause(self):
        """
        Play or pause based on audio output state.
        """
        state = self.output.state()
        if state == QAudio.ActiveState:  # playing
            # pause playback
            self.output.suspend()
        elif state == QAudio.SuspendedState:  # paused
            # resume playback
            self.output.resume()
        elif state == QAudio.StoppedState or state == QAudio.IdleState:
            self.play()

    def stop(self):
        """
        Stop playback.
        """
        state = self.output.state()
        if state != QAudio.StoppedState:
            self.output.stop()
            if sys.platform == 'darwin':
                self.buffer.close()

    def state_checkpoint(self):
        """
        React to AudioOutput state change.
        Loop if enabled.
        """
        # Loop implementation
        if self.output.state() == QAudio.IdleState and self.loop_enabled:
            self.play()

    def notified(self):
        ts = self.output.processedUSecs() /1000000 + self.t_start
        self.statusBar().showMessage('{:.3f}'.format(ts))
        self.progressBar.setValue(ts * 100 / self.duration)

    def set_region(self, position):
        """
        Put the playback start position to `position`.
        """
        wav = wave.open(self.wav_path)
        wav.setpos(position)
        self.buffer.seek(0)
        self.buffer.writeData(wav.readframes(self.reg_nframes))
        wav.close()

        self.t_start = position / self.params.framerate
        self.progressBar.setValue(self.t_start * 100 / self.duration)

    def set_random_region(self):
        """
        Choose a random position and set playback start from there.
        """
        position = random.randrange(self.params.nframes - self.reg_nframes)
        end = position + self.reg_nframes
        print('Random region: {:.2f}-{:.2f}'.format(
            position / self.params.framerate, end / self.params.framerate)
        )
        self.set_region(position)


# cli args
wav_path = sys.argv[1] if sys.argv[1:] else 'wav/nice-work.wav'

app = QApplication(sys.argv)
main = MainWindow(wav_path)
main.show()
sys.exit(app.exec_())
