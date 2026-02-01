from sys import argv as sys_argv, exit as sys_exit
from random import randint
from threading import Thread

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSpinBox, QCheckBox
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QIcon

from pynput import keyboard
from pynput.mouse import Button, Controller as MouseController


# --- Qt signal bridge ---
class HotkeySignals(QObject):
    start = Signal()
    stop = Signal()


class AutoClicker(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Clicker')
        self.setFixedSize(320, 280)

        # --- State ---
        self.mouse = MouseController()
        self.is_running = False

        # --- Signals ---
        self.signals = HotkeySignals()
        self.signals.start.connect(self.start_clicking)
        self.signals.stop.connect(self.stop_clicking)

        # --- Timers ---
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.click)

        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(self.stop_clicking)

        # --- UI ---
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Click interval (50-10000 ms):'))
        self.interval_box = QSpinBox()
        self.interval_box.setRange(50, 10_000)
        self.interval_box.setValue(100)
        layout.addWidget(self.interval_box)

        # --- Anti-detect ---
        self.anti_detect_checkbox = QCheckBox('Antidetect (interval +- 5-75%)')
        layout.addWidget(self.anti_detect_checkbox)

        diff_layout = QVBoxLayout()
        self.diff_box = QSpinBox()
        self.diff_box.setRange(5, 75)
        self.diff_box.setValue(10)
        self.diff_box.setEnabled(False)
        diff_layout.addWidget(self.diff_box)
        layout.addLayout(diff_layout)

        self.anti_detect_checkbox.stateChanged.connect(
            lambda state: self.diff_box.setEnabled(state)
        )

        layout.addWidget(QLabel('Timer (0-3600 sec, 0 = off):'))
        self.duration_box = QSpinBox()
        self.duration_box.setRange(0, 3600)
        self.duration_box.setValue(0)
        layout.addWidget(self.duration_box)

        self.status_label = QLabel('Status: Stopped')
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel('F8 — Start\nF9 — Stop'))

        # --- Global hotkeys ---
        Thread(target=self.start_hotkeys, daemon=True).start()

    # --- Global hotkeys thread ---
    def start_hotkeys(self):
        def on_press(key):
            if key == keyboard.Key.f8:
                self.signals.start.emit()
            elif key == keyboard.Key.f9:
                self.signals.stop.emit()

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    # --- Logic ---
    def start_clicking(self):
        if self.is_running:
            return

        self.is_running = True
        self.status_label.setText('Status: Clicking')

        duration = self.duration_box.value()
        if duration > 0:
            self.stop_timer.start(duration * 1000)

        self.schedule_next_click()

    def stop_clicking(self):
        if not self.is_running:
            return

        self.is_running = False
        self.click_timer.stop()
        self.stop_timer.stop()
        self.status_label.setText('Status: Stopped')

    def schedule_next_click(self):
        if not self.is_running:
            return

        base_interval = self.interval_box.value()

        if self.anti_detect_checkbox.isChecked():
            diff_percent = self.diff_box.value()
            diff_ms = int(base_interval * diff_percent / 100)
            interval = randint(base_interval - diff_ms, base_interval + diff_ms)
        else:
            interval = base_interval

        self.click_timer.start(interval)

    def click(self):
        self.mouse.press(Button.left)
        self.mouse.release(Button.left)

        self.schedule_next_click()


if __name__ == "__main__":
    app = QApplication(sys_argv)
    app.setWindowIcon(QIcon('icon.png'))
    window = AutoClicker()
    window.setFixedSize(300, 250)
    window.show()
    sys_exit(app.exec())
