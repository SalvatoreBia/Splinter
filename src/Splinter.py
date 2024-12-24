import sys
import os
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QPushButton, QLabel, QGridLayout, QGroupBox, QSizePolicy
)


class AudioSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Splitter")
        self.setFixedSize(700, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F8FF;
            }
            QLabel {
                color: #003366;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                font-size: 16px;
                padding: 10px;
                border: 2px solid #003366;
                border-radius: 10px;
                background-color: #6699CC;
                color: #FFFFFF;
                margin: 5px;
            }
            QPushButton:checked {
                background-color: #003366;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #B3CDE0;
                color: #90A4AE;
            }
            QGroupBox {
                border: 2px solid #003366;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                background-color: #F0F8FF;
                color: #003366;
            }
        """)

        self.input_file_path = None
        self.output_dir_path = None
        self.splitter_process = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Panel 1: Input File
        self.input_path_label = QLabel("No file selected")
        panel1 = self.create_file_chooser("Choose Input Audio File:", "Select Audio File", self.input_path_label)
        main_layout.addWidget(panel1)

        # Panel 2: Audio Tracks
        panel2 = self.create_audio_tracks_panel()
        main_layout.addWidget(panel2)

        # Panel 3: Output Directory
        self.output_path_label = QLabel("No directory selected")
        panel3 = self.create_file_chooser("Choose Output Directory:", "Select Directory", self.output_path_label, is_directory=True)
        main_layout.addWidget(panel3)

        # Bottom Buttons
        buttons_layout = QVBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setEnabled(False)
        self.start_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.clicked.connect(self.on_start)
        buttons_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.on_cancel)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

    def create_file_chooser(self, label_text, button_text, path_label, is_directory=False):
        """Creates a panel with a label, a path display, and a button to choose a file or folder."""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(path_label)

        button = QPushButton(button_text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(button)

        def choose_file():
            if is_directory:
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")
                if directory:
                    self.output_dir_path = directory
                    path_label.setText(directory)
            else:
                file, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
                if file:
                    self.input_file_path = file
                    path_label.setText(os.path.basename(file))
            self.update_start_button_state()

        button.clicked.connect(choose_file)
        return panel

    def create_audio_tracks_panel(self):
        """Creates the panel with checkable buttons for Drums, Bass, Guitar, Vocals, and Instrumental."""
        panel = QGroupBox("Select Audio Tracks")
        layout = QGridLayout(panel)

        tracks = {
            "Drums": (0, 0),
            "Bass": (0, 1),
            "Guitar": (1, 0),
            "Vocals": (1, 1),
            "Instrumental": (2, 0, 1, 2)
        }

        self.track_buttons = {}
        for track, pos in tracks.items():
            button = QPushButton(track)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.toggled.connect(self.update_start_button_state)
            self.track_buttons[track.lower()] = button

            if len(pos) == 2:
                layout.addWidget(button, pos[0], pos[1])
            else:
                layout.addWidget(button, *pos)

        return panel

    def update_start_button_state(self):
        """Enables or disables the Start button based on whether an input file, output folder, and at least one track are selected."""
        input_selected = (self.input_file_path is not None)
        output_selected = (self.output_dir_path is not None)
        track_selected = any(button.isChecked() for button in self.track_buttons.values())
        self.start_button.setEnabled(input_selected and output_selected and track_selected)

    def center(self):
        """Centers the window on the screen."""
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def on_start(self):
        """When user clicks 'Start'."""
        if not self.input_file_path or not self.output_dir_path:
            return  # sanity check

        # Which tracks did the user pick?
        selected_tracks = []
        if self.track_buttons["drums"].isChecked():
            selected_tracks.append('d')
        if self.track_buttons["bass"].isChecked():
            selected_tracks.append('b')
        if self.track_buttons["guitar"].isChecked():
            selected_tracks.append('g')
        if self.track_buttons["vocals"].isChecked():
            selected_tracks.append('v')
        if self.track_buttons["instrumental"].isChecked():
            selected_tracks.append('i')

        # Build the options string (e.g., "-dbgv")
        options = "-" + "".join(selected_tracks)

        input_file = self.input_file_path
        output_dir = self.output_dir_path

        # Kill any old process (just in case)
        self.on_cancel()

        # Construct the absolute path to the splitter.py script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        splitter_script = os.path.join(script_dir, "splitter.py")

        # Launch the subprocess
        print("Launching Demucs separation process...")
        try:
            self.splitter_process = subprocess.Popen(
                [sys.executable, splitter_script, options, input_file, output_dir]
            )
        except Exception as e:
            print(f"Error launching subprocess: {e}")
            return

        # Update UI
        self.start_button.setEnabled(False)
        self.start_button.setText("Splitting...")
        self.cancel_button.setEnabled(True)

        print(f"Selected tracks: {selected_tracks}")
        print(f"Input file: {input_file}")
        print(f"Output directory: {output_dir}")

    def on_cancel(self):
        """When user clicks 'Cancel'."""
        # If we have a running process, terminate it
        if self.splitter_process and (self.splitter_process.poll() is None):
            print("Terminating Demucs subprocess...")
            self.splitter_process.terminate()
            self.splitter_process.wait()
            self.splitter_process = None
            print("Process cancelled.")

        # Reset UI
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        self.cancel_button.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = AudioSplitterApp()
    window.center()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
