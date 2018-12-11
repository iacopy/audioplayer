#!/usr/bin/python

# Standard Library
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


class MainWindow(QMainWindow):
    def __init__(self, wav_path):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle('MainWindow')

        self._setLayout()

        self.wav_path = wav_path

        wav = wave.open(self.wav_path)
        params = wav.getparams()
        self.duration = params.nframes / params.framerate

        start = 0
        end = params.nframes
        frametoread = end - start
        wav.setpos(start)
        self.data = wav.readframes(frametoread)
        wav.close()
        self._resetBuffer()

        enc = 'audio/pcm'
        fmt = QAudioFormat()
        fmt.setChannelCount(params.nchannels)
        fmt.setSampleRate(params.framerate)
        fmt.setSampleSize(params.sampwidth * 8)
        fmt.setCodec(enc)
        fmt.setByteOrder(QAudioFormat.LittleEndian)
        fmt.setSampleType(QAudioFormat.SignedInt)

        self.output = QAudioOutput(fmt, self)
        self.output.stateChanged.connect(self.state_checkpoint)
        self.output.setNotifyInterval(20)
        self.output.notify.connect(self.notified)
        self.play_button.clicked.connect(self.play_pause)

        self.loop_enabled = False

    def _setLayout(self):
        widget = QtWidgets.QWidget()

        grid = QtWidgets.QGridLayout(widget)
        self.progressBar = QtWidgets.QProgressBar(widget)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.play_button = QtWidgets.QPushButton('Play | Stop', widget)

        grid.addWidget(self.progressBar, 0, 0, 1, 3)
        grid.addWidget(self.play_button, 1, 1)

        widget.setLayout(grid)
        self.setCentralWidget(widget)

    def _resetBuffer(self):
        self.buffer = QBuffer()
        self.buffer.setData(self.data)

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
                self._resetBuffer()
                self.buffer.open(QIODevice.ReadOnly)
            else:
                # I found this way does not works on OS X
                self.buffer.seek(0)
        else:
            # Load from file
            self.buffer.open(QIODevice.ReadOnly)
        self.output.start(self.buffer)
        self.t_paused = 0
        self.t0_paused = time.time()

    def play_pause(self):
        """
        Play or pause based on audio output state.
        """
        state = self.output.state()
        if state == QAudio.ActiveState:  # playing
            # pause playback
            self.output.suspend()
            self.t0_paused = time.time()
        elif state == QAudio.SuspendedState:  # paused
            # resume playback
            self.output.resume()
            self.t_paused += time.time() - self.t0_paused
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
        tus = self.output.elapsedUSecs()
        ts = tus / 1000000 - self.t_paused
        self.statusBar().showMessage('{:.3f}'.format(ts))
        self.progressBar.setValue(ts * 100 / self.duration)


# cli args
wav_path = sys.argv[1] if sys.argv[1:] else 'wav/nice-work.wav'

app = QApplication(sys.argv)
main = MainWindow(wav_path)
main.show()
sys.exit(app.exec_())
