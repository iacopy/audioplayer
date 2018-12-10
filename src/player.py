#!/usr/bin/python

import sys
import wave

from PyQt5.QtCore import QBuffer, QIODevice
from PyQt5.QtMultimedia import (QAudio, QAudioFormat, QAudioOutput)
from PyQt5.QtWidgets import QMainWindow, QApplication


class MainWindow(QMainWindow):
    def __init__(self, wav_path):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle('MainWindow')

        self.wav_path = wav_path

        wav = wave.open(self.wav_path)
        params = wav.getparams()
        start = 0
        end = params.nframes
        frametoread = end - start
        self.buffer = QBuffer()
        wav.setpos(start)
        self.buffer.setData(wav.readframes(frametoread))
        wav.close()

        enc = 'audio/pcm'
        fmt = QAudioFormat()
        fmt.setChannelCount(params.nchannels)
        fmt.setSampleRate(params.framerate)
        fmt.setSampleSize(params.sampwidth * 8)
        fmt.setCodec(enc)
        fmt.setByteOrder(QAudioFormat.LittleEndian)
        fmt.setSampleType(QAudioFormat.SignedInt)

        self.output = QAudioOutput(fmt, self)
        self.output.setNotifyInterval(20)
        self.output.notify.connect(self.notified)

        self.play()

    def play(self):
        """
        Play from the beginning.
        """
        if self.buffer.isOpen():
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

    def notified(self):
        tus = self.output.elapsedUSecs()
        ts = tus / 1000000  #- self.t_paused
        self.statusBar().showMessage('{:.3f}'.format(ts))


# cli args
wav_path = sys.argv[1] if sys.argv[1:] else 'wav/nice-work.wav'

app = QApplication(sys.argv)
main = MainWindow(wav_path)
main.show()
sys.exit(app.exec_())

