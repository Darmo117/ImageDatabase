import abc

import PyQt5.QtCore as QtC


class WorkerThread(QtC.QThread):
    """Base class for worker threads."""
    progress_signal = QtC.pyqtSignal(float, object, int)

    STATUS_UNKNOWN = 0
    STATUS_SUCCESS = 1
    STATUS_FAILED = 2

    def __init__(self):
        super().__init__()
        self._error = None
        self._cancelled = False

    def cancel(self):
        """Interrupts this thread."""
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        """Whether this thread was cancelled."""
        return self._cancelled

    @abc.abstractmethod
    def run(self):
        pass

    @property
    def failed(self) -> bool:
        """Returns True if the operation failed."""
        return self._error is not None

    @property
    def error(self) -> str | None:
        """If the operation failed, returns the reason; otherwise returns None."""
        return self._error

    @error.setter
    def error(self, value: str):
        """Sets the error message."""
        self._error = value
