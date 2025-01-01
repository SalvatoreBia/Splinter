import threading
import utils
from PyQt6.QtCore import pyqtSignal, QObject


class Worker(QObject, threading.Thread):
    def __init__(self):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.daemon = True


class SaveSplitWorker(Worker):
    finished = pyqtSignal(bool)

    def __init__(self, process, output_dir, options, folder_name):
        super().__init__()
        self.process = process
        self.output_dir = output_dir
        self.options = options
        self.folder_name = folder_name

    def run(self):
        print("SaveSplitWorker: In attesa del completamento del processo...")
        self.process.wait()
        if self.process.returncode == 0:
            print("SaveSplitWorker: Processo completato. Salvando i file...")
            utils.save(self.output_dir, self.options, self.folder_name)
        self.finished.emit(True)

class MonitorSplitWorker(Worker):
    def __init__(self, process):
        super().__init__()
        self.process = process
        self.action = None
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)

    def get_condition(self):
        return self.cond

    def set_action(self, action):
        with self.lock:
            self.action = action
            self.cond.notify()

    def run(self):
        with self.lock:
            while self.action is None:
                self.cond.wait()

            if self.action == 'abort':
                print("MonitorSplitWorker: Terminando il processo...")
                self.process.terminate()

