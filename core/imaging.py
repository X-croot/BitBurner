import os
import time
import threading
from typing import Optional, Callable

WRITE_CHUNK = 8 * 1024 * 1024

class ImageWriter:
    def __init__(self):
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_progress: Optional[Callable[[float,int,int,float,int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_finished: Optional[Callable[[], None]] = None
        self.on_canceled: Optional[Callable[[], None]] = None

    def start(self, image_path: str, device_path: str):
        self._cancel.clear()
        self._thread = threading.Thread(target=self._run, args=(image_path, device_path), daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel.set()

    def _emit(self, cb, *args):
        try:
            if cb:
                cb(*args)
        except Exception:
            pass

    def _run(self, image_path: str, device_path: str):
        try:
            if not os.path.exists(image_path):
                self._emit(self.on_error, "Source file not found.")
                return
            total = os.path.getsize(image_path)
            done = 0
            t_prev = time.time()
            prev_done = 0
            try:
                ftest = open(device_path, "rb+")
                ftest.close()
            except PermissionError:
                self._emit(self.on_error, "Access denied. Try running as administrator/root.")
                return
            except FileNotFoundError:
                self._emit(self.on_error, "Target device not found.")
                return
            except Exception as e:
                self._emit(self.on_error, f"Cannot open target: {e}")
                return
            with open(image_path, "rb", buffering=0) as fin, open(device_path, "rb+", buffering=0) as fout:
                try:
                    fout.seek(0)
                except Exception:
                    pass
                while not self._cancel.is_set():
                    buf = fin.read(WRITE_CHUNK)
                    if not buf:
                        break
                    w = fout.write(buf)
                    if w != len(buf):
                        self._emit(self.on_error, "Partial write encountered.")
                        return
                    done += w
                    now = time.time()
                    if now - t_prev >= 0.12:
                        span = max(now - t_prev, 1e-6)
                        bps = (done - prev_done) / span
                        eta = int((total - done)/bps) if bps > 1 else -1
                        ratio = min(done/total, 0.99)
                        self._emit(self.on_progress, ratio, done, total, bps, eta)
                        t_prev = now
                        prev_done = done
                try:
                    fout.flush()
                    os.fsync(fout.fileno())
                except Exception:
                    pass
            if self._cancel.is_set():
                self._emit(self.on_canceled)
                return
            self._emit(self.on_progress, 1.0, total, total, 0.0, 0)
            self._emit(self.on_finished)
        except Exception as e:
            self._emit(self.on_error, f"Error: {e}")
