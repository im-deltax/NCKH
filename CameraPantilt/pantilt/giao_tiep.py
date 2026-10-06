import threading
import time

import serial


class KetNoiServo:
    GIAO_THUC = "A{p:.2f},{t:.2f}\n"

    def __init__(self, port, baud=115200, cho_khoi_dong=2.0):
        self.ser = serial.Serial(port, baud, timeout=0.05, write_timeout=0.5)
        time.sleep(cho_khoi_dong)                                      
        self.ser.reset_input_buffer()
        self.lock = threading.Lock()
        self.so_lenh = 0

    def _gui(self, s, cho_phan_hoi=True, timeout=0.3):
        with self.lock:
            n = self.ser.in_waiting
            if n:
                self.ser.read(n)
            self.ser.write(s.encode())
            if not cho_phan_hoi:
                return None
            t0 = time.perf_counter()
            while time.perf_counter() - t0 < timeout:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line.startswith(("OK", "ST", "ER")):
                    return line
            return None

    def bat(self):    return self._gui("E\n")
    def nha(self):    return self._gui("D\n")
    def ve_giua(self): return self._gui("H\n")

    def dat_goc(self, pan_deg, tilt_deg, cho_phan_hoi=False):
        self.so_lenh += 1
        return self._gui(self.GIAO_THUC.format(p=pan_deg, t=tilt_deg),
                         cho_phan_hoi=cho_phan_hoi)

    def trang_thai(self):
        r = self._gui("S\n")
        if r and r.startswith("ST"):
            d = {}
            for tok in r[3:].split():
                k, _, v = tok.partition("=")
                d[k] = float(v)
            return d
        return None

    def dat_gioi_han(self, pmin, pmax, tmin, tmax):
        return self._gui(f"C{pmin},{pmax},{tmin},{tmax}\n")

    def buoc_nhay(self, n_deg):
        return self._gui(f"Z{n_deg}\n", timeout=1.0)

    def den(self, bat):
        return self._gui(f"L{1 if bat else 0}\n")

    def dong(self):
        try:
            self.nha()
        finally:
            self.ser.close()
