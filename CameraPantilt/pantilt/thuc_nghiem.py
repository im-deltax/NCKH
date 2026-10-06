

import csv
import random
import threading
import time


def _bai1():
    ds = ["BAN"] * 10 + ["THU"] * 10
    random.Random(2026).shuffle(ds)
    return [(f"{x}", f"Bam {'b' if x == 'BAN' else 't'} de the o che do {x}, "
             f"cho the xac nhan. SPACE, dua vat vao vung, di chuyen khoang "
             f"5 giay, dua vat ra ngoai, cho ve CHO roi SPACE.") for x in ds]


def _bai2():
    ds = []
    for cu_ly in (30,):
        for goc in (-60, -45, -30, -15, 0, 15, 30, 45, 60):
            ds.append((f"goc={goc};cu_ly={cu_ly};lan=1",
                       f"SPACE, day xe NAM NGANG tu ngoai vao diem goc {goc:+d} do "
                       f"THEO LIDAR (duong la ben PHAI, giong man hinh LiDAR), "
                       f"mat than xe cach LiDAR {cu_ly} cm, "
                       f"rut tay ra, de yen 5 giay, SPACE, roi dua xe ra ngoai "
                       f"va cho ve CHO."))
    return ds


def _bai3():
    mo_ta = {
        "dung_yen": "de vat DUNG YEN",
        "cham": "di chuyen vat CHAM va DEU qua lai (khoang 5 cm/s)",
        "nhanh": "di chuyen vat NHANH, DOI HUONG lien tuc",
    }
    ds = []
    for kieu in ("dung_yen", "cham", "nhanh"):
        for lan in (1, 2, 3):
            ds.append((f"kieu={kieu};lan={lan}",
                       (f"Dua xe vao vung, cho pan-tilt BAM roi bam SPACE va "
                        f"{mo_ta[kieu]}. Chuong trinh tu chay 3 luot x 20 giay "
                        f"lien tiep, khong can bam them.") if lan == 1 else
                       f"Tu dong, tiep tuc {mo_ta[kieu]}."))
    return ds


def _bai4():
    return [("phong_trong", "Dat san vat dung yen co gan dai giay mong trong vung "
             "TRUOC khi bat LiDAR. Thinh thoang THOI tu NGOAI vung 70 cm cho giay "
             "rung, khong de dau hay tay lot vao vung. SPACE bat dau, chuong trinh "
             "dem nguoc va TU KET THUC sau 60 phut.")]


def _bai5():
    ds = []
    for v in (3, 10, 30):
        for lan in (1, 2, 3):
            ds.append((f"v={v};lan={lan}",
                       (f"Dat vat CHINH DIEN cach LiDAR 80 cm (ngoai vung). Bam "
                        f"SPACE. Moi khi nghe BIP DOI thi day vat THANG ve phia "
                        f"LiDAR, DEU khoang {v} cm/s, toi moc 30 cm thi dung. Het "
                        f"gio keo vat ve lai 80 cm; luot sau tu bat dau khi he ve "
                        f"CHO.") if lan == 1 else
                       f"Tu dong. Cho BIP DOI roi day DEU khoang {v} cm/s tu "
                       f"80 cm toi 30 cm."))
    ds.append(("THU_mat_mang;lan=1",
               "TAT Wi-Fi laptop, xe ngoai vung, bam SPACE. Nghe BIP DOI thi day "
               "xe vao khoang 40 cm chinh dien, rut tay, de yen 15 giay. Het gio "
               "keo xe ra va BAT lai Wi-Fi."))
    return ds


def _bai6():
    vao = ("Moi khi nghe BIP DOI thi day xe vao vung (khoang 40 cm chinh dien), "
           "rut tay, de yen. Het gio keo xe ra ngoai vung.")
    return [
        ("THU_co_mang;lan=1", "Rut the IFF (he coi la THU). Xe de ngoai vung. "
         "Bam SPACE. " + vao),
        ("THU_co_mang;lan=2", "Tu dong. " + vao),
        ("THU_mat_mang;lan=1", "TAT Wi-Fi laptop, cho xe ngoai vung, bam SPACE. "
         + vao + " Xong thi BAT lai Wi-Fi."),
    ]


def _phu_a():
    return [(f"rut_iff;lan={i}",
             "Bam t. SPACE, RUT cap USB tram IFF, dua vat vao vung 10 giay, "
             "dua ra, CAM lai cap, cho dong '[IFF] Da noi lai', SPACE.")
            for i in (1, 2)]


def _phu_b():
    return [(f"hai_vat;lan={i}",
             "Bam b (the o che do BAN). SPACE, dua DONG THOI hai vat vao vung, "
             "di chuyen 10 giay, dua ra, SPACE.") for i in (1, 2, 3)]


THOI_LUONG = {
    "bai3": 20.0,
    "bai4": 3600.0,
    "bai5": {"v=3": 25.0, "v=10": 13.0, "v=30": 10.0, "THU_mat_mang": 15.0},
    "bai6": 15.0,
}
CHO_VE_CHO = {"bai5", "bai6"}


def _bip(tan_so=1200, ms=250):
    try:
        import winsound
        threading.Thread(target=winsound.Beep, args=(tan_so, ms),
                         daemon=True).start()
    except Exception:
        print("\a", end="", flush=True)


KICH_BAN = {
    "bai1": ("Phan loai ban thu va do tre toan chuoi", _bai1),
    "bai2": ("Do chinh xac ban giao LiDAR sang camera", _bai2),
    "bai3": ("Do chinh xac bam theo kieu chuyen dong", _bai3),
    "bai4": ("Bao dong gia va do on dinh khi chay dai", _bai4),
    "bai5": ("Bo sot theo toc do di chuyen, gop canh bao Telegram", _bai5),
    "bai6": ("Canh bao Telegram, co va mat mang", _bai6),
    "phu_a": ("Mat tram IFF giua chung", _phu_a),
    "phu_b": ("Hai muc tieu cung luc", _phu_b),
}


class ThucNghiem:

    def __init__(self, ten_bai):
        if ten_bai not in KICH_BAN:
            raise SystemExit(f"[x] Khong co kich ban {ten_bai}. "
                             f"Chon mot trong: {', '.join(KICH_BAN)}")
        self.ten_bai = ten_bai
        self.tieu_de, tao = KICH_BAN[ten_bai]
        self.ds = tao()
        self.chi_so = 0                                            
        self.luot = 0                                                  
        self.nhan = ""
        self.dang_do = False
        self.t_bat_dau = 0.0
        self.su_kien = []                                       
        self._khoa = threading.Lock()
        self._t_nhac = 0.0
        self._tl = THOI_LUONG.get(ten_bai)
        self.thoi_luong = None if isinstance(self._tl, dict) else self._tl
        self._cho_ve_cho = ten_bai in CHO_VE_CHO
        self._t_cho_tu = None                                    
        self._giay_con_cuoi = None
        self._tu_bat_dau_luc = None                                           

    def gioi_thieu(self):
        print("\n" + "=" * 64, flush=True)
        print(f"  THUC NGHIEM {self.ten_bai.upper()}: {self.tieu_de}", flush=True)
        print(f"  So luot: {len(self.ds)}. SPACE = bat dau/ket thuc luot, "
              f"x = bo luot vua roi, q = thoat.", flush=True)
        print("=" * 64, flush=True)
        self._in_luot_ke()

    def _in_luot_ke(self):
        if self.chi_so >= len(self.ds):
            print("\n[TN] DA XONG TAT CA LUOT. Bam q de thoat va ghi log.",
                  flush=True)
            return
        nhan, huong_dan = self.ds[self.chi_so]
        print(f"\n[TN] Luot ke tiep {self.chi_so + 1}/{len(self.ds)}: {nhan}",
              flush=True)
        print(f"     {huong_dan}", flush=True)

    def phim_cach(self):
        with self._khoa:
            t = time.time()
            if not self.dang_do:
                if self.chi_so >= len(self.ds):
                    print("[TN] Het luot. Bam q de thoat.", flush=True)
                    return
                self.nhan = self.ds[self.chi_so][0]
                self.luot = self.chi_so + 1
                self.dang_do = True
                self.t_bat_dau = t
                self.su_kien.append((t, "bat_dau", self.luot, self.nhan))
                self._giay_con_cuoi = None
                if isinstance(self._tl, dict):
                    self.thoi_luong = self._tl.get(self._nhom(self.nhan))
                print(f"[TN] >>> BAT DAU luot {self.luot}: {self.nhan}",
                      flush=True)
                if self.thoi_luong:
                    if self._cho_ve_cho:
                        _bip(1500, 150)
                        threading.Timer(0.3, _bip, (1500, 150)).start()
                    print(f"[TN] Dem nguoc {self.thoi_luong:.0f} s, het gio "
                          f"luot tu ket thuc (SPACE de ket thuc som).",
                          flush=True)
                    _bip(1200, 150)
            else:
                self.dang_do = False
                self.su_kien.append((t, "ket_thuc", self.luot, self.nhan))
                print(f"[TN] <<< KET THUC luot {self.luot} "
                      f"({t - self.t_bat_dau:.1f} s)", flush=True)
                self.chi_so += 1
                self.luot = 0
                self.nhan = ""
                self._in_luot_ke()

    def phim_x(self):
        self._tu_bat_dau_luc = None                                     
        with self._khoa:
            t = time.time()
            if self.dang_do:
                so = self.luot
                self.dang_do = False
                self.luot = 0
                self.nhan = ""
            elif self.chi_so > 0:
                self.chi_so -= 1
                so = self.chi_so + 1
            else:
                return
            nhan = self.ds[so - 1][0]
            self.su_kien.append((t, "bo", so, nhan))
            print(f"[TN] Da BO luot {so} ({nhan}). Do lai luot nay.", flush=True)
            self._in_luot_ke()

    @staticmethod
    def _nhom(nhan):
        return ";".join(p for p in str(nhan).split(";")
                        if not p.startswith("lan="))

    def nhac(self, trang_thai=None):

        if not self._tl:
            return
        if not self.dang_do:
            if self._cho_ve_cho:
                if trang_thai == "CHO":
                    if self._t_cho_tu is None:
                        self._t_cho_tu = time.time()
                else:
                    self._t_cho_tu = None
            if self._tu_bat_dau_luc and time.time() >= self._tu_bat_dau_luc:
                if (self._cho_ve_cho and (self._t_cho_tu is None
                                          or time.time() - self._t_cho_tu < 2.0)):
                    return                                               
                self._tu_bat_dau_luc = None
                self.phim_cach()
            return
        if not self.thoi_luong:
            return
        con = self.thoi_luong - (time.time() - self.t_bat_dau)
        if con <= 0:
            print("\n[TN] HET GIO.", flush=True)
            _bip(900, 500)
            nhom = self._nhom(self.nhan)
            self.phim_cach()                                 
            if (self.chi_so < len(self.ds)
                    and self._nhom(self.ds[self.chi_so][0]) == nhom):
                self._tu_bat_dau_luc = time.time() + 2.0
                self._t_cho_tu = None
                if self._cho_ve_cho:
                    print("[TN] Keo vat ra ngoai vung. Khi he ve CHO, luot sau "
                          "tu bat dau bang BIP DOI.", flush=True)
                else:
                    print("[TN] Luot ke tiep CUNG KIEU tu bat dau sau 2 s, "
                          "giu nguyen cach lam.", flush=True)
            elif self.chi_so < len(self.ds):
                if self._cho_ve_cho:
                    print("[TN] XONG NHOM. Keo vat ra ngoai vung, lam theo huong "
                          "dan luot ke tiep roi bam SPACE.", flush=True)
                else:
                    print("[TN] XONG NHOM. Chuan bi kieu moi, cho camera BAM "
                          "roi bam SPACE.", flush=True)
            return
        giay = int(con) + 1
        if giay == self._giay_con_cuoi:
            return
        self._giay_con_cuoi = giay
        if self.thoi_luong <= 120:
            print(f"\r[TN] Con {giay:3d} s   ", end="", flush=True)
            if giay <= 3:
                _bip(1500, 120)
        elif giay % 300 == 0 or giay <= 10:
            print(f"[TN] Con {giay // 60} phut {giay % 60:02d} giay", flush=True)

    def cot_log(self):
        return self.luot, self.nhan, int(self.dang_do)

    def ghi(self, duong_dan):
        with open(duong_dan, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["epoch_s", "loai", "luot", "nhan"])
            for e in self.su_kien:
                w.writerow([f"{e[0]:.6f}", e[1], e[2], e[3]])
