




import queue
import threading
import time

import serial

BAN = "BAN"                                                     
THU = "THU"                                                               
CHO = "CHO"                                                           


class TramIFF:
    def __init__(self, port, baud=115200, cho_khoi_dong=1.5,
                 so_lan_hoi=3, han_cho_s=1.5, han_nho_s=20.0,
                 tre_roi_vung_s=1.0, ke_thua_s=1.5):
        self.port = port
        self.baud = baud
        self.cho_khoi_dong = float(cho_khoi_dong)
        self.so_lan_hoi = max(1, min(9, int(so_lan_hoi)))
        self.han_cho_s = float(han_cho_s)
        self.han_nho_s = float(han_nho_s)
        self.tre_roi_vung_s = float(tre_roi_vung_s)
        self.ke_thua_s = float(ke_thua_s)
        self._t_bat_dau_vang = None

        self._lock = threading.Lock()
        self._bang = {}                                         
        self._hang = queue.Queue()
        self.dung = False
        self.ser = None
        self.song = False
        self.loi = None
        self.so_lan_da_hoi = 0
        self._cuoi = None                                         
        self._t_noi_lai = 0.0
        self._lidar_co_vat = False
        self._dang_hoi = False
        self._yeu_cau_l0 = threading.Event()

        try:
            self._mo_cong()
        except Exception as e:
            self._mat_ket_noi(e)

    def bat_dau(self):
        threading.Thread(target=self._chay, daemon=True).start()

    def dat_lidar(self, co_vat):

        co_vat = bool(co_vat)
        t = time.perf_counter()
        with self._lock:
            if co_vat:
                self._t_bat_dau_vang = None
                if not self._lidar_co_vat:
                    self._lidar_co_vat = True
                return
            if not self._lidar_co_vat:
                return
            if self._t_bat_dau_vang is None:
                self._t_bat_dau_vang = t
                return
            if t - self._t_bat_dau_vang < self.tre_roi_vung_s:
                return
            self._lidar_co_vat = False
            self._t_bat_dau_vang = None
            self._bang.clear()
            self._cuoi = None
            self._dang_hoi = False
            while True:
                try:
                    self._hang.get_nowait()
                except queue.Empty:
                    break
            self._yeu_cau_l0.set()

    def phan_xet(self, ma):

        t = time.perf_counter()
        with self._lock:
            e = self._bang.get(ma)
            if e is None:
                gan = [v for v in self._bang.values()
                       if v["xong"] and v.get("ly_do") != "SERIAL"
                       and t - v["t_cham"] <= self.ke_thua_s]
                if gan:
                    moi = dict(max(gan, key=lambda v: v["t_cham"]))
                    moi.update(t_cham=t, ke_thua=True)
                    self._bang[ma] = moi
                    return BAN if moi["ban"] else THU
                self._bang[ma] = {"xong": False, "ban": False, "t_hoi": t,
                                  "t_cham": t, "ly_do": "", "ms": 0,
                                  "so_lan": 0, "status": 0}
                self._dang_hoi = True
                self._hang.put(ma)
                self._don_dep(t)
                return CHO
            e["t_cham"] = t
            if e["xong"]:
                if (e.get("ly_do") == "SERIAL" and self.song
                        and t - e["t_hoi"] > 1.0):
                    e.update({"xong": False, "ban": False, "t_hoi": t,
                              "ly_do": "", "ms": 0, "so_lan": 0,
                              "status": 0})
                    self._dang_hoi = True
                    self._hang.put(ma)
                    return CHO
                return BAN if e["ban"] else THU
            if t - e["t_hoi"] > self.han_cho_s:
                return THU
            return CHO

    def chi_tiet(self, ma):
        with self._lock:
            e = self._bang.get(ma)
            return dict(e) if e else None

    def mo_ta(self):
        if not self.song:
            return f"IFF dang noi lai {self.port}"
        with self._lock:
            e = self._cuoi
            dang_hoi = self._dang_hoi
        if dang_hoi:
            return "IFF dang hoi"
        if e is None:
            return "IFF san sang"
        ket = "BAN" if e["ban"] else "THU"
        return f"IFF {ket} {e['ly_do']} {e['ms']} ms"

    def _don_dep(self, t):
        if len(self._bang) < 64:
            return
        cu = [k for k, v in self._bang.items()
              if t - v["t_cham"] > self.han_nho_s]
        for k in cu:
            self._bang.pop(k, None)

    def _chay(self):
        while not self.dung:
            if self._yeu_cau_l0.is_set():
                self._gui_lidar_het()
                continue
            try:
                ma = self._hang.get(timeout=0.05)
            except queue.Empty:
                if not self.song:
                    self._thu_noi_lai()
                continue
            if self.dung:
                return
            try:
                kq = self._hoi_mot_lan()
            except Exception as e:
                self._mat_ket_noi(e)
                if self._thu_noi_lai(bat_buoc=True):
                    try:
                        kq = self._hoi_mot_lan()
                    except Exception as e2:
                        self._mat_ket_noi(e2)
                        kq = {"ban": False, "ly_do": "SERIAL", "ms": 0,
                              "so_lan": 0, "status": 0}
                else:
                    kq = {"ban": False, "ly_do": "SERIAL", "ms": 0,
                          "so_lan": 0, "status": 0}
            if self._yeu_cau_l0.is_set():
                continue
            with self._lock:
                e = self._bang.get(ma)
                if e is not None:
                    e.update(kq)
                    e["xong"] = True
                    self._cuoi = dict(e)
                self._dang_hoi = any(not v["xong"]
                                     for v in self._bang.values())

    def _gui_lidar_het(self):
        self._yeu_cau_l0.clear()
        if not self.song or self.ser is None:
            return
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"L0\n")
            han = time.perf_counter() + 0.5
            while time.perf_counter() < han:
                dong = self.ser.readline().decode("utf-8", "ignore").strip()
                if dong.startswith("OK,lidar=0"):
                    return
        except Exception as e:
            self._mat_ket_noi(e)

    def _dong_cong(self):
        ser, self.ser = self.ser, None
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass

    def _mat_ket_noi(self, e):
        self.song = False
        self.loi = str(e)
        self._dong_cong()

    def _mo_cong(self):
        self._dong_cong()
        ser = serial.Serial(self.port, self.baud, timeout=0.2,
                            write_timeout=1.0)
        self.ser = ser
        time.sleep(self.cho_khoi_dong)
        ser.reset_input_buffer()

        ser.write(b"A0\n")
        han = time.perf_counter() + 1.0
        while time.perf_counter() < han:
            dong = ser.readline().decode("utf-8", "ignore").strip()
            if dong.startswith("OK,tu_hoi=0"):
                ser.write(b"L0\n")
                han_l0 = time.perf_counter() + 0.5
                while time.perf_counter() < han_l0:
                    d0 = ser.readline().decode("utf-8", "ignore").strip()
                    if d0.startswith("OK,lidar=0"):
                        self.song = True
                        self.loi = None
                        return
                raise TimeoutError(f"{self.port} khong tra loi lenh L0")
        raise TimeoutError(f"{self.port} khong tra loi lenh A0")

    def _thu_noi_lai(self, bat_buoc=False):
        t = time.perf_counter()
        if not bat_buoc and t - self._t_noi_lai < 2.0:
            return False
        self._t_noi_lai = t
        try:
            self._mo_cong()
            print(f"[IFF] Da noi lai tram tai {self.port}.", flush=True)
            return True
        except Exception as e:
            self._mat_ket_noi(e)
            return False

    def _hoi_mot_lan(self):
        self.ser.reset_input_buffer()
        self.ser.write(f"Q{self.so_lan_hoi}\n".encode())
        self.so_lan_da_hoi += 1

        han = time.perf_counter() + max(0.8, self.han_cho_s)
        while time.perf_counter() < han:
            dong = self.ser.readline().decode("utf-8", "ignore").strip()
            if not dong:
                continue
            if not dong.startswith("R,"):
                continue
            phan = dong.split(",")
            if len(phan) < 6:
                continue
            self.song = True
            self.loi = None
            return {"ban": phan[1] == "1",
                    "ms": int(phan[2]) if phan[2].isdigit() else 0,
                    "ly_do": phan[3],
                    "so_lan": int(phan[4]) if phan[4].isdigit() else 0,
                    "status": int(phan[5]) if phan[5].isdigit() else 0}
        return {"ban": False, "ly_do": "QUA_HAN", "ms": 0,
                "so_lan": 0, "status": 0}

    def dong(self):
        self.dung = True
        time.sleep(0.25)
        self._dong_cong()
