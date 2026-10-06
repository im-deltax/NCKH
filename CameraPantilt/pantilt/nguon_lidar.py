

import json
import math
import threading
import time
import urllib.request


def goc_pan_tu_lidar(bearing_deg, range_m, d_m, lech_deg, dao_dau):



    psi = math.radians(float(bearing_deg))
    r = max(float(range_m), 0.01)
    x = r * math.sin(psi)
    y = r * math.cos(psi)
    th = math.degrees(math.atan2(x, y + float(d_m)))
    if dao_dau:
        th = -th
    return th + float(lech_deg)


class NguonLidar:
    def __init__(self, url, d_m=0.10, lech_deg=0.0, dao_dau=False,
                 het_han_s=1.0, toc_do_min=0.05, bo_loc=None):
        self.url = url
        self.bo_loc = bo_loc
        self.d_m = d_m
        self.lech_deg = lech_deg
        self.dao_dau = dao_dau
        self.het_han_s = het_han_s
        self.toc_do_min = toc_do_min

        self._lock = threading.Lock()
        self._vet_tho = None                                             
        self._vet = None                                                
        self._t_goi = 0.0                                      
        self._t_vet_tho = 0.0                                           
        self._t_vet = 0.0                                             
        self.song = False
        self.loi = None
        self.so_goi = 0
        self.dung = False

    def bat_dau(self):
        threading.Thread(target=self._chay, daemon=True).start()

    def _chay(self):
        while not self.dung:
            try:
                with urllib.request.urlopen(self.url, timeout=10) as r:
                    self.song = True
                    self.loi = None
                    for raw in r:
                        if self.dung:
                            return
                        line = raw.decode("utf-8", "ignore").strip()
                        if not line.startswith("data:"):
                            continue                                  
                        try:
                            goi = json.loads(line[5:])
                        except Exception:
                            continue
                        self._xu_ly(goi)
            except Exception as e:
                self.song = False
                self.loi = str(e)
                time.sleep(1.0)                                          

    def _xu_ly(self, goi):

        t_now = time.perf_counter()
        tat_ca = list(goi.get("tracks", []))

        def dang_duoc_quan_sat(v):
            co_co_quan_sat = any(k in v for k in
                                ("matched", "occluded", "raw_recovered"))
            if not co_co_quan_sat:
                return bool(v.get("active"))
            return bool(v.get("matched") or v.get("occluded")
                        or v.get("raw_recovered"))

        ds_quan_sat = [v for v in tat_ca if dang_duoc_quan_sat(v)]

        def diem(v):
            return (float(v.get("speed", 0.0))
                    / max(float(v.get("range", 0.01)), 0.01))

        with self._lock:
            vet_cu = (self._vet_tho
                      if self._vet_tho is not None
                      and t_now - self._t_vet_tho <= self.het_han_s
                      else None)
        chon_tho = None
        if vet_cu is not None:
            ma_cu = vet_cu.get("id")
            chon_tho = next((v for v in ds_quan_sat
                             if v.get("id") == ma_cu), None)

        if chon_tho is None and vet_cu is None:
            ung_vien_moi = [
                v for v in ds_quan_sat
                if bool(v.get("active"))
                and float(v.get("speed", 0.0)) >= self.toc_do_min
            ]
            chon_tho = max(ung_vien_moi, key=diem) if ung_vien_moi else None

        duoc_phep = False
        if chon_tho is not None:
            duoc_phep = (self.bo_loc(chon_tho)
                         if self.bo_loc is not None else True)

        with self._lock:
            self._t_goi = t_now
            self.so_goi += 1
            if chon_tho is not None:
                self._vet_tho = chon_tho
                self._t_vet_tho = t_now
                if duoc_phep:
                    self._vet = chon_tho
                    self._t_vet = t_now
                else:
                    self._vet = None
                    self._t_vet = 0.0

    def goc_muc_tieu(self, t_now):

        with self._lock:
            vet = self._vet
            t_goi = self._t_vet
        if vet is None or t_now - t_goi > self.het_han_s:
            return None
        return goc_pan_tu_lidar(vet.get("bearing", 0.0), vet.get("range", 1.0),
                                self.d_m, self.lech_deg, self.dao_dau)

    def vet_hien_tai(self, t_now):

        with self._lock:
            vet = self._vet
            t_goi = self._t_vet
        if vet is None or t_now - t_goi > self.het_han_s:
            return None
        return vet

    def vet_tho_hien_tai(self, t_now):
        with self._lock:
            vet = self._vet_tho
            t_goi = self._t_vet_tho
        if vet is None or t_now - t_goi > self.het_han_s:
            return None
        return vet

    def cu_ly_ngang(self, t_now):

        vet = self.vet_hien_tai(t_now)
        if vet is None:
            return None
        psi = math.radians(float(vet.get("bearing", 0.0)))
        r = max(float(vet.get("range", 0.0)), 0.01)
        return math.hypot(r * math.sin(psi), r * math.cos(psi) + self.d_m)

    def mo_ta(self, t_now):
        with self._lock:
            vet_tho = self._vet_tho
            vet = self._vet
            t_goi = self._t_vet_tho
        if not self.song:
            return "LIDAR mat ket noi"
        if vet_tho is None or t_now - t_goi > self.het_han_s:
            return "LIDAR trong"
        if vet is None:
            return (f"LIDAR co vat {vet_tho.get('range', 0.0):.2f} m "
                    f"- dang cho IFF")
        return (f"LIDAR {vet.get('bearing', 0.0):+.0f} do "
                f"{vet.get('range', 0.0):.2f} m "
                f"{vet.get('speed', 0.0):.2f} m/s")
