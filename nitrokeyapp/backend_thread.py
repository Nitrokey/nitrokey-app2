from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal


class BackendThread(QThread):
    hello = pyqtSignal()
    finishedSignal = pyqtSignal()

    job_q = Queue()

    def __del__(self):
        self.wait()

    def add_job(self, signal, func, *f_va, **f_kw):
        self.job_q.put((signal, func, f_va, f_kw))

    def stop_loop(self):
        self.add_job(None, None)

    def run(self):
        self.hello.emit()
        while True:
            # blocking job-wait-loop
            job = self.job_q.get()
            if job is None:
                continue
            signal, func, vargs, kwargs = job

            # func == None means stop/end thread asap!
            if func is None:
                break

            # eval `func`, emit signal with results
            res = func(*vargs, **kwargs)
            signal.emit(res or {})
