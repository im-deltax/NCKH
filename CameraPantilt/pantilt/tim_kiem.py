



class BoNhoHuong:
    def __init__(self, rong_o_deg=15.0, so_diem=6, t_dung_s=1.5, goc_nghi=0.0,
                 pan_min=-70.0, pan_max=70.0, buoc_quet_deg=30.0, le_deg=5.0):
        self.rong = float(rong_o_deg)
        self.so_diem = int(so_diem)
        self.t_dung = float(t_dung_s)
        self.goc_nghi = float(goc_nghi)
        self.pan_min = float(pan_min)
        self.pan_max = float(pan_max)
        self.buoc = float(buoc_quet_deg)
        self.le = float(le_deg)
        self.o = {}                                                           
        self.thu_tu = []
        self.i = 0
        self.t_doi = None

    def ghi_nhan(self, theta, t):
        k = int(round(float(theta) / self.rong))
        n, _ = self.o.get(k, (0, 0.0))
        self.o[k] = (n + 1, float(t))

    def _kep(self, a):
        lo = self.pan_min + self.le
        hi = self.pan_max - self.le
        return min(max(float(a), lo), hi)

    def _pha_uu_tien(self):

        g = [self._kep(self.goc_nghi)]
        ds = sorted(self.o.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))
        for k, _ in ds:
            a = self._kep(k * self.rong)
            if all(abs(a - b) > self.rong * 0.5 for b in g):
                g.append(a)
            if len(g) >= self.so_diem:
                break
        return g

    def _pha_phu_kin(self, da_co):

        g = []
        lo = self.pan_min + self.le
        hi = self.pan_max - self.le
        n = int((hi - lo) / self.buoc) + 1
        for i in range(n):
            a = lo + i * self.buoc
            if all(abs(a - b) > self.buoc * 0.25 for b in da_co) and \
               all(abs(a - b) > self.buoc * 0.25 for b in g):
                g.append(a)
        if g and abs(hi - g[-1]) > self.buoc * 0.5 and \
           all(abs(hi - b) > self.buoc * 0.25 for b in da_co):
            g.append(hi)
        return g

    def _xep_hang(self):
        uu_tien = self._pha_uu_tien()
        return uu_tien + self._pha_phu_kin(uu_tien)

    def bat_dau_quet(self, t):
        self.thu_tu = self._xep_hang()
        self.i = 0
        self.t_doi = float(t)

    def goc_quet(self, t):
        t = float(t)
        if not self.thu_tu or self.t_doi is None:
            self.bat_dau_quet(t)
        if not self.thu_tu:
            return self.goc_nghi
        if t - self.t_doi >= self.t_dung:
            self.i += 1
            self.t_doi = t
            if self.i >= len(self.thu_tu):
                self.thu_tu = self._xep_hang()
                self.i = 0
        return self.thu_tu[self.i]

    def so_huong(self):
        return len(self.thu_tu)

    def so_lan_thay(self):
        return sum(n for n, _ in self.o.values())
