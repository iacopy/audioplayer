#!/usr/bin/python
"""
Play audio regions of a wav file.
"""

# Standard Library
import random
import sys
import wave
from datetime import timedelta

# 3rd party
from PyQt5 import QtWidgets
from PyQt5.QtCore import QBuffer
from PyQt5.QtCore import QIODevice
from PyQt5.QtMultimedia import QAudio
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow

# My stuff
import utils

REG_SECONDS = 2


class MainWindow(QMainWindow):
    def __init__(self, wav_path):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle('MainWindow')

        self._setLayout()
        self.status_bar = self.statusBar()

        self.wav_path = wav_path
        self.params = utils.read_wav_info(wav_path)
        self.duration = self.params.nframes / self.params.framerate

        self.output = utils.get_audio_output(self.params)
        self.output.stateChanged.connect(self.state_checkpoint)
        self.output.setNotifyInterval(20)

        self.output.notify.connect(self.notified)

        self.loop_button.clicked.connect(self.switch_loop)
        self.play_button.clicked.connect(self.play_pause)
        self.random_button.clicked.connect(self.set_random_region)
        self.export_button.clicked.connect(self.export_region)

        self.command_edit.returnPressed.connect(self.command_entered)

        self.loop_enabled = False

        self.buffer = QBuffer()

        self.region = None
        self.set_region((0, REG_SECONDS * self.params.framerate))
        # self.set_random_region()

    def _setLayout(self):
        widget = QtWidgets.QWidget()

        grid = QtWidgets.QGridLayout(widget)
        self.progressBar = QtWidgets.QProgressBar(widget)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.loop_button = QtWidgets.QPushButton('Loop', widget)
        self.loop_button.setCheckable(True)
        self.play_button = QtWidgets.QPushButton('Play | Stop', widget)
        self.random_button = QtWidgets.QPushButton('Random', widget)
        self.command_edit = QtWidgets.QLineEdit('')
        self.export_button = QtWidgets.QPushButton('Export', widget)

        grid.addWidget(self.progressBar, 0, 0, 1, 3)
        grid.addWidget(self.loop_button, 1, 0)
        grid.addWidget(self.play_button, 1, 1)
        grid.addWidget(self.random_button, 1, 2)
        grid.addWidget(self.command_edit, 2, 1)
        grid.addWidget(self.export_button, 2, 2)

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

    def switch_loop(self):
        self.loop_enabled = not self.loop_enabled

    def state_checkpoint(self):
        """
        React to AudioOutput state change.
        Loop if enabled.
        """
        # Loop implementation
        state = self.output.state()
        if state == QAudio.ActiveState:
            print(state, '== Active')
        elif state == QAudio.SuspendedState:
            print(state, '== Suspended')
        elif state == QAudio.IdleState:
            print(state, '== Idle')
            if self.loop_enabled:
                self.play()
            else:
                self.stop()
        elif state == QAudio.StoppedState:
            print(state, '== Stopped')

    def notified(self):
        start_time = self.region[0] / self.params.framerate
        playing_time = self.output.processedUSecs() / 1000000 + start_time
        self.progressBar.setValue(playing_time * 100 / self.duration)
        self.status_bar.showMessage(str(timedelta(seconds=playing_time))[:-3])

    def set_region(self, region):
        """
        Put the playback start position to `position`.
        """
        # avoid segfault if changing region during playback
        self.stop()

        position, end = region
        position = max(0, min(position, end))  # don't start before 0
        end = min(self.params.nframes, end)  # don't set end after days!
        self.region = position, end
        print('set_region -> {:,}-{:,}'.format(*self.region))
        print('region times: {}-{} (duration={})'.format(*self.region_timedeltas()))
        frame_to_read = end - position

        wav = wave.open(self.wav_path)
        wav.setpos(position)
        # we need to reinit buffer since the region could be shorter than before
        self.buffer = QBuffer()
        self.buffer.writeData(wav.readframes(frame_to_read))
        wav.close()

        start_time = position / self.params.framerate
        self.progressBar.setValue(start_time * 100 / self.duration)
        self.status_bar.showMessage(str(timedelta(seconds=start_time))[:-3])

    @property
    def reg_nframes(self):
        return self.region[1] - self.region[0]

    def set_random_region(self):
        """
        Choose a random position and set playback start from there.
        """
        try:
            position = random.randrange(self.params.nframes - self.reg_nframes)
        except ValueError:
            print('Cannot move position randomly. Please shorten the region.')
            position = 0

        end = position + self.reg_nframes
        print('Random region: {:.2f}-{:.2f}'.format(
            position / self.params.framerate, end / self.params.framerate)
        )
        self.set_region((position, end))

    def region_timedeltas(self):
        """Return start, end and duration timedeltas"""
        start, end = self.region
        start_timedelta = timedelta(seconds=start / self.params.framerate)
        end_timedelta = timedelta(seconds=end / self.params.framerate)
        return start_timedelta, end_timedelta, (end_timedelta - start_timedelta)

    def command_entered(self):
        """
        Change region boundaries with Blender-like syntax.

        Examples:
        "l-0.5" ==> move start position 0.5 s before
        "r1"    ==> move stop position 1 seconds after
        """
        command = self.command_edit.text()
        try:
            lr, delta = utils.parse_command(command)
        except (IndexError, ValueError) as err:
            print(err)
            return

        start, end = self.region
        if lr == 'l':
            start = int(start + delta * self.params.framerate)
            print('New start: {}'.format(timedelta(seconds=(start / self.params.framerate))))
        elif lr == 'r':
            end = int(end + delta * self.params.framerate)
            print('New end: {}'.format(timedelta(seconds=(end / self.params.framerate))))

        self.set_region((start, end))
        self.command_edit.setText('')

        # feature: restart immediately after command is entered
        self.play()

    def export_region(self):
        """
        Export the current region.
        """
        start, stop = self.region
        wav_filepath = self.wav_path[:-4] + '[{}-{}].wav'.format(start, stop)
        with wave.open(wav_filepath, 'wb') as wave_write:
            wave_write.setparams(self.params)
            wave_write.writeframes(self.buffer.data())
        print(wav_filepath, 'created')


# cli args
WAV_PATH = sys.argv[1] if sys.argv[1:] else 'wav/nice-work.wav'

app = QApplication(sys.argv)
main = MainWindow(WAV_PATH)
main.show()
sys.exit(app.exec_())
