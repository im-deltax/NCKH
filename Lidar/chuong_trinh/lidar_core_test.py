







import math
import warnings
from collections import deque

import numpy as np

try:
    from scipy.optimize import linear_sum_assignment
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

try:
    from scipy.spatial import cKDTree
    HAVE_KDTREE = True
except Exception:
    cKDTree = None
    HAVE_KDTREE = False


STATIC, SUSPECT, DYNAMIC = 'STATIC', 'SUSPECT', 'DYNAMIC'


class Config:
    def __init__(self):
        self.vat_nho_bat = True
        self.vat_nho_max_diem = 6
        self.vat_nho_min_mau = 5
        self.vat_nho_net_mm = 35.0
        self.vat_nho_residual_mm = 6.0
        self.min_range_mm = 120.0
        self.max_range_mm = 500.0
        self.ban_kinh_chuan_mm = 500.0
        self.fov_center_deg = 180.0
        self.fov_half_deg = 90.0
        self.angle_sign = 1.0                                             

        self.n_bins = 180

        self.bg_window_s = 60.0                               
        self.bg_percentile = 85.0                                                       
        self.bg_min_samples = 12
        self.bg_ti_le_that = 0.35                                                
        self.bg_warmup_s = 3.0                                                  
        self.fg_margin_mm = 50.0
        self.le_tran_ratio = 0.20

        self.diff_mm = 10.0
        self.diff_sigma_k = 3.0                                   
        self.fg_sigma_k = 5.0                                        
        self.diff_scales = (1, 4, 16)
        self.diff_min_run = 5
        self.nhap_nhay_mm = 60.0
        self.nhap_nhay_lan = 2                                              
        self.nhap_nhay_diem = 30                                             
        self.nhap_nhay_vang = 0.0
        self.nhap_nhay_vang_toi_da = 0.97                                                                                             
        self.nhap_nhay_yen_mm = 120.0                                      
        self.evidence_min_bins = 3
        self.strong_ev_bins = 5

        self.gap_bins = 3                                                       
        self.merge_range_mm = 50.0                                                  
        self.min_object_bins = 3
        self.min_object_points = 3
        self.min_object_width_ratio = 0.05
        self.min_diem = 4
        self.mat_do_diem = 1.2
        self.ti_le_tia_doi = 0.42

        self.gate_base_mm = 145.0
        self.gate_vel_gain = 1.4                                                  
        self.cuu_vot_min_mm = 120.0
        self.cuu_vot_he_so = 2.5
        self.lost_timeout_s = 0.6
        self.lost_timeout_dyn_s = 10.0
        self.so_vong_xac_nhan_ra = 2
        self.toc_do_ra_toi_thieu_mm_s = 40.0
        self.sigma_r_mm = 0.73                                   
        self.sigma_r_exp = 1.03                                                        
        self.dung_sigma_r_moi = True
        self.sigma_r_tia_moi_mm = 0.50
        self.sigma_a_mm_s2 = 1600.0
        self.max_speed_mm_s = 3000.0
        self.range_sq_noise = 1.0                                           

        self.buoc_neo_mm = 60.0
        self.g3_radial_mm = 100.0                           
        self.g4_anchor_mm = 150.0                      
        self.nis_nguong = 9.21

        self.che_le_goc_deg = 3.0                              
        self.che_sau_mm = 40.0                                                 
        self.che_toi_da_vong = 40                                           
        self.gop_phong_R = False
        self.gop_dong_bang_nhom = True
        self.gop_hud_predict_s = 0.80
        self.gop_hud_speed_min_mm_s = 80.0
        self.ghep_dung_nis = True
        self.ghep_nis_nguong = 100.0
        self.ghep_nis_he_so_che = 2.5
        self.ghep_nis_trong_so_mm = 10.0
        self.ghep_nis_chi_khi_mo_ho = True
        self.ghep_huong_phat = 250.0
        self.ghep_huong_toc_min = 100.0
        self.che_he_so_cong = 2.2

        self.k_confirm = 2                                               
        self.k_confirm_yeu = 4
        self.fast_confirm = 0.0
        self.fast_confirm_cos = 0.5                                            
        self.latch_dynamic = 1.0                                                   
        self.pham_vi_toi_thieu_mm = 120.0
        self.pham_vi_so_vong = 30                           
        self.cham_min_mau = 8
        self.cham_span_mm = 45.0
        self.cham_net_ratio = 0.80
        self.cham_straight_min = 0.70
        self.cham_linearity_min = 0.95
        self.cham_monotonic_min = 0.85
        self.cham_confirm_frames = 1
        self.hud_min_cutoff_hz = 0.8
        self.hud_beta = 0.004
        self.hud_derivative_cutoff_hz = 1.0
        self.ghep_he_so_rong = 0.0
        self.ghep_he_so_rong_sau_che = 0.5
        self.ghep_phat_rong_toi_da = 150.0                                          
        self.rong_so_vong = 20                                       
        self.rong_id_so_vong = 80
        self.rong_id_sigma_san_mm = 12.0
        self.rong_id_sigma_ty_le = 0.12
        self.rong_id_nguong_ngoai_lai_sigma = 3.0
        self.ghep_rong_nll_mm = 28.0
        self.ghep_rong_nll_toi_da_mm = 220.0
        self.ghep_rong_tach_sigma = 1.5
        self.gop_xuyen_tam_min_mm = 45.0
        self.gop_xuyen_tam_sai_so_mm = 65.0
        self.gop_rong_khop_z2 = 2.25
        self.gop_rong_cach_z2 = 2.0
        self.gop_rong_tong_ratio = 0.78

        self.lop_cu_ly_bat = 1.0
        self.lop_cu_ly_cach_vet_toi_thieu_mm = 25.0
        self.lop_cu_ly_diem_toi_thieu = 2
        self.lop_cu_ly_cong_san_mm = 22.0
        self.lop_cu_ly_cong_theo_rong = 0.45
        self.lop_cu_ly_cong_toi_da_mm = 65.0
        self.lop_cu_ly_le_goc_o = 1
        self.lop_cu_ly_bao_ve_vong = 40

        self.diem_id_so_vong = 80
        self.diem_id_sigma_san = 0.08
        self.diem_id_nguong_ngoai_lai_sigma = 3.0

        self.cuong_do_id_bat = 1.0
        self.cuong_do_r_min_mm = 280.0
        self.cuong_do_r_max_mm = 550.0
        self.cuong_do_mau_toi_thieu = 3
        self.cuong_do_id_so_vong = 80
        self.cuong_do_id_khoa_sau = 32
        self.cuong_do_sigma_log_san = 0.18
        self.cuong_do_sigma_do_log = 0.20
        self.cuong_do_nguong_ngoai_lai_sigma = 3.0
        self.ghep_cuong_do_nll_mm = 45.0
        self.ghep_cuong_do_nll_toi_da_mm = 220.0
        self.ghep_cuong_do_tach_sigma = 1.5
        self.cuong_do_reid_mat_toi_da_s = 2.5
        self.cuong_do_reid_gate_mm = 350.0
        self.cuong_do_reid_z_toi_da = 2.5
        self.cuong_do_reid_margin_mm = 35.0
        self.cuong_do_gallery_s = 30.0
        self.cuong_do_gallery_z_toi_da = 2.0
        self.cuong_do_gallery_margin = 0.45

        self.bac_cau_vung_mu = 1.0
        self.ghep_toi_thieu = 0.08
        self.ngung_ve_sau_s = 1.5
        self.goc_ve_max = 35.0
        self.blind_ratio = 0.4                                                             
        self.bg_shift_ratio = 0.4                                              
        self.pose_guard_max_range_mm = 6000.0
        self.pose_guard_max_points = 200
        self.pose_guard_confirm_frames = 3
        self.pose_guard_rot_deg = 2.0
        self.pose_guard_trans_mm = 30.0
        self.pose_guard_score_ratio = 0.65
        self.pose_guard_score_max_mm = 100.0
        self.pose_guard_inlier_mm = 60.0
        self.pose_guard_inlier_ratio = 0.45
        self.pose_guard_min_sectors = 6

    def scale_theo_ban_kinh(self, moi_mm):


        k = float(moi_mm) / self.ban_kinh_chuan_mm
        self.max_range_mm = float(moi_mm)
        self.min_range_mm = max(120.0, 0.28 * float(moi_mm))
        self.g3_radial_mm *= k
        self.g4_anchor_mm *= k
        self.gate_base_mm *= k
        self.cluster_merge_mm = getattr(self, 'cluster_merge_mm', 130.0) * k
        return k

    def as_dict(self):
        return dict(self.__dict__)

    def update(self, d):
        for k, v in d.items():
            if k in self.__dict__ and isinstance(v, (int, float)) \
                    and not isinstance(self.__dict__[k], tuple):
                setattr(self, k, float(v))


def preprocess(points, cfg):

    out = []
    for a, d in points:
        if d < cfg.min_range_mm or d > cfg.max_range_mm:
            continue
        rel = ((a * cfg.angle_sign - cfg.fov_center_deg + 180.0) % 360.0) - 180.0
        if abs(rel) > cfg.fov_half_deg:
            continue
        rad = math.radians(rel)
        out.append((rel, d, d * math.sin(rad), d * math.cos(rad)))
    out.sort(key=lambda p: p[0])
    return out


class BinGrid:


    def __init__(self, cfg):
        self.cfg = cfg
        self.nb = int(cfg.n_bins)
        self.span = 2.0 * cfg.fov_half_deg

    def build(self, pts):
        r = np.full(self.nb, np.nan)
        if not pts:
            return r
        half = self.cfg.fov_half_deg
        for rel, d, _, _ in pts:
            b = int((rel + half) / self.span * self.nb)
            if b < 0 or b >= self.nb:
                continue
            if math.isnan(r[b]) or d < r[b]:
                r[b] = d

        MAX_KHE = 3
        b = 1
        while b < self.nb - 1:
            if not math.isnan(r[b]):
                b += 1
                continue
            e = b
            while e < self.nb - 1 and math.isnan(r[e]):
                e += 1
            rong = e - b
            trai, phai = r[b - 1], r[e]
            if (rong <= MAX_KHE and not math.isnan(trai) and not math.isnan(phai)
                    and abs(trai - phai) < 60.0):
                for k in range(rong):
                    u = (k + 1.0) / (rong + 1.0)
                    r[b + k] = trai + (phai - trai) * u
            b = e + 1
        return r

    def bin_angle(self, b):
        half = self.cfg.fov_half_deg
        return (b + 0.5) / self.nb * self.span - half


class Background:



    MOC_TRONG = 1.0e5                                        

    def __init__(self, cfg, nb):
        self.cfg = cfg
        self.nb = nb
        self.cap = max(16, int(cfg.bg_window_s * 10))
        self.buf = np.full((nb, self.cap), np.nan)
        self.idx = 0
        self.count = 0
        self.bg = np.full(nb, np.nan)
        self.fill = np.zeros(nb)
        self.sigma = np.full(nb, np.nan)
        self.t0 = None
        self.t_last_calc = -1e9
        self.co_truoc = np.zeros(nb, dtype=bool)                                 

    def push(self, t, r, exclude_mask=None):




        if self.t0 is None:
            self.t0 = t
        row = r.copy()
        with np.errstate(all='ignore'):
            row[np.isnan(row)] = self.MOC_TRONG
        if exclude_mask is not None:
            row[exclude_mask] = np.nan
        self.buf[:, self.idx] = row
        co = ~np.isnan(r)
        self.co_truoc = co.copy()
        self.co_truoc[1:] |= co[:-1]
        self.co_truoc[:-1] |= co[1:]
        self.idx = (self.idx + 1) % self.cap
        self.count = min(self.count + 1, self.cap)

    def maybe_recompute(self, t, every=0.5):
        if t - self.t_last_calc < every:
            return
        self.t_last_calc = t
        with np.errstate(all='ignore'):
            that = self.buf[:, :self.count] < self.MOC_TRONG * 0.5
        valid = np.sum(that, axis=1)
        co_ghi = np.sum(~np.isnan(self.buf[:, :self.count]), axis=1)
        self.fill = valid / max(self.count, 1)
        with np.errstate(all='ignore'):
            buf = self.buf[:, :self.count]
            chi_that = np.where(that, buf, np.nan)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                bg_that = np.nanpercentile(chi_that, self.cfg.bg_percentile,
                                           axis=1)
            ti_le_that = valid / np.maximum(co_ghi, 1)
            bg = np.where(ti_le_that >= self.cfg.bg_ti_le_that,
                          bg_that, self.MOC_TRONG)
            buf = np.where(buf >= self.MOC_TRONG * 0.5, np.nan, buf)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                p95 = np.nanpercentile(buf, 95.0, axis=1)
                p75 = np.nanpercentile(buf, 75.0, axis=1)
            sig = (p95 - p75) / 0.971
        bg[co_ghi < self.cfg.bg_min_samples] = np.nan
        sig[valid < self.cfg.bg_min_samples] = np.nan

        with np.errstate(all='ignore'):
            cu = self.bg
            giu = (~np.isnan(cu)) & (~np.isnan(bg))
            bg[giu] = np.maximum(bg[giu], cu[giu])
            chi_co_cu = np.isnan(bg) & (~np.isnan(cu))
            bg[chi_co_cu] = cu[chi_co_cu]
        self.bg = bg
        self.sigma = np.clip(sig, 2.0, 45.0)

    def ready(self, t):
        return self.t0 is not None and (t - self.t0) >= self.cfg.bg_warmup_s

    def le_tien_canh(self):


        

        cfg = self.cfg
        s = np.where(np.isnan(self.sigma), cfg.fg_margin_mm,
                     cfg.fg_sigma_k * self.sigma)
        tran = max(cfg.fg_margin_mm, cfg.le_tran_ratio * cfg.max_range_mm)
        return np.clip(s, cfg.fg_margin_mm, tran)

    def foreground(self, r):
        cfg = self.cfg
        with np.errstate(all='ignore'):
            trong = self.bg >= self.MOC_TRONG * 0.5                         
            fg_that = (~np.isnan(r)) & (~np.isnan(self.bg)) & (~trong) & \
                      ((self.bg - r) > self.le_tien_canh())
            bien = max(0.15 * cfg.max_range_mm, 25.0)
            gan_han = r < (cfg.max_range_mm - bien)
            fg_trong = (~np.isnan(r)) & trong & gan_han & self.co_truoc
            fg = fg_that | fg_trong
        with np.errstate(all='ignore'):
            chua_co_nen = (~np.isnan(r)) & np.isnan(self.bg) & (self.fill < 0.25)
        return fg | chua_co_nen


def _runs_at_least(mask, n, mu=None):


    if n <= 1:
        return mask.copy()
    lan = mask if mu is None else (mask | mu)
    out = np.zeros_like(mask)
    i, N = 0, len(mask)
    n_mep = max(2, (n + 1) // 2)
    while i < N:
        if lan[i]:
            j = i
            while j < N and lan[j]:
                j += 1
            cham_mep = (i == 0) or (j == N)
            if mu is not None and not np.any(mask[i:j]):
                i = j
                continue
            if (j - i) >= (n_mep if cham_mep else n):
                out[i:j] = mask[i:j] if mu is None else (mask[i:j] | mu[i:j])
            i = j
        else:
            i += 1
    return out


class NeoOGoc:






    def __init__(self, cfg, nb):
        self.cfg = cfg
        self.nb = nb
        self.neo = np.full(nb, np.nan)
        self.r_truoc = np.full(nb, np.nan)
        self.vang = np.zeros(nb, dtype=int)                                          

    def reset(self):
        self.neo[:] = np.nan
        self.r_truoc[:] = np.nan
        self.vang[:] = 0

    def cap_nhat(self, r, buoc_mm):
        with np.errstate(all='ignore'):
            co = ~np.isnan(r)
            bac = co & (~np.isnan(self.r_truoc)) & (np.abs(r - self.r_truoc) > buoc_mm)
            moi = co & np.isnan(self.neo)
            self.neo[bac | moi] = r[bac | moi]
            self.vang[co] = 0
            self.vang[~co] += 1
            mat_han = self.vang > 8
            self.neo[mat_han] = np.nan
            troi = self.neo - r
            troi[~co] = 0.0
            troi[np.isnan(troi)] = 0.0
        moi = r.copy()
        with np.errstate(all='ignore'):
            thieu = np.isnan(moi) & (~np.isnan(self.r_truoc)) & (self.vang <= 8)
        moi[thieu] = self.r_truoc[thieu]
        self.r_truoc = moi
        return troi


class MotionEvidence:




    def __init__(self, cfg, nb):
        self.cfg = cfg
        self.nb = nb
        self.hist_r = deque(maxlen=max(cfg.diff_scales) + 1)
        self.diem_nn = np.zeros(nb, dtype=float)
        self.mask_nn = np.zeros(nb, dtype=bool)

    def push(self, r):
        self.hist_r.appendleft(r.copy())

    def reset(self):
        self.hist_r.clear()
        self.diem_nn[:] = 0.0
        self.mask_nn[:] = False

    def _nhap_nhay_tuc_thoi(self):



        n = len(self.hist_r)
        if n < 6 or self.cfg.nhap_nhay_lan <= 0:
            return np.zeros(self.nb, dtype=bool)
        M = np.array(self.hist_r, dtype=float)
        co = ~np.isnan(M)

        doi_co = np.abs(np.diff(co.astype(np.int8), axis=0)).sum(axis=0)

        du = co.sum(axis=0) >= 4
        lo = np.min(np.where(co, M, np.inf), axis=0)
        hi = np.max(np.where(co, M, -np.inf), axis=0)
        bien_do = np.where(du, np.where(du, hi, 0.0) - np.where(du, lo, 0.0), 0.0)
        giua = np.where(du, 0.5 * (np.where(du, lo, 0.0) + np.where(du, hi, 0.0)),
                        np.inf)
        gan = co & (M < giua[None, :])
        doi_muc = np.abs(np.diff(gan.astype(np.int8), axis=0)).sum(axis=0)

        nua = max(n // 2, 2)
        du_dau = co[:nua].any(axis=0)
        du_cuoi = co[nua:].any(axis=0)
        m_dau = np.zeros(self.nb)
        m_cuoi = np.zeros(self.nb)
        if du_dau.any():
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m_dau = np.nanmedian(np.where(co[:nua], M[:nua], np.nan), axis=0)
        if du_cuoi.any():
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m_cuoi = np.nanmedian(np.where(co[nua:], M[nua:], np.nan), axis=0)
        lech = np.where(du_dau & du_cuoi, np.abs(m_dau - m_cuoi), np.inf)
        dung_yen = np.isfinite(lech) & (lech < self.cfg.nhap_nhay_yen_mm)

        co_ca_hai = du_dau & du_cuoi
        lo_dau = np.min(np.where(co[:nua], M[:nua], np.inf), axis=0)
        lo_cuoi = np.min(np.where(co[nua:], M[nua:], np.inf), axis=0)
        hi_dau = np.max(np.where(co[:nua], M[:nua], -np.inf), axis=0)
        hi_cuoi = np.max(np.where(co[nua:], M[nua:], -np.inf), axis=0)
        lo_dau = np.where(co_ca_hai, lo_dau, 0.0)
        lo_cuoi = np.where(co_ca_hai, lo_cuoi, 0.0)
        hi_dau = np.where(co_ca_hai, hi_dau, 0.0)
        hi_cuoi = np.where(co_ca_hai, hi_cuoi, 0.0)
        yen = self.cfg.nhap_nhay_yen_mm
        hai_muc_yen = (co_ca_hai
                       & (np.abs(lo_dau - lo_cuoi) < yen)
                       & (np.abs(hi_dau - hi_cuoi) < yen))
        dung_yen = dung_yen | hai_muc_yen

        vang = 1.0 - co.mean(axis=0)
        hay_vang = ((vang >= self.cfg.nhap_nhay_vang)
                    & (vang <= self.cfg.nhap_nhay_vang_toi_da))

        k = self.cfg.nhap_nhay_lan
        return dung_yen & hay_vang & ((doi_co >= k)
                                      | (du & (bien_do > self.cfg.nhap_nhay_mm)
                                         & (doi_muc >= k)))

    def cap_nhat_nhap_nhay(self):



        tuc = self._nhap_nhay_tuc_thoi()
        tran = 2.0 * max(self.cfg.nhap_nhay_diem, 1)
        self.diem_nn = np.clip(np.where(tuc, self.diem_nn + 1.0,
                                        self.diem_nn - 1.0), 0.0, tran)
        self.mask_nn = self.diem_nn >= self.cfg.nhap_nhay_diem
        return self.mask_nn

    def evidence(self, bg, mu=None):

        cfg = self.cfg
        tong = np.zeros(self.nb, dtype=bool)
        theo_thang = {}
        theo_thang_tho = {}
        if len(self.hist_r) < 2:
            return tong, theo_thang, theo_thang_tho

        r0 = self.hist_r[0]
        fg0 = bg.foreground(r0)
        ben = ~self.cap_nhat_nhap_nhay()
        for k in cfg.diff_scales:
            if k >= len(self.hist_r):
                continue
            rk = self.hist_r[k]
            fgk = bg.foreground(rk)

            with np.errstate(all='ignore'):
                nguong = np.maximum(cfg.diff_mm,
                                    cfg.diff_sigma_k * 1.414 * np.where(
                                        np.isnan(bg.sigma), cfg.diff_mm / 4.0, bg.sigma))
                chung = fg0 & fgk & (~np.isnan(r0)) & (~np.isnan(rk)) & ben
                doi_cu_ly = chung & (np.abs(r0 - rk) > nguong)
            doi_mat_na = (fg0 ^ fgk) & ben

            m = _runs_at_least(doi_cu_ly | doi_mat_na, cfg.diff_min_run, mu)
            theo_thang[k] = m
            tong |= m

            with np.errstate(all='ignore'):
                hop_le = (~np.isnan(r0)) & (~np.isnan(rk)) & ben
                tho = hop_le & (np.abs(r0 - rk) > 1.6 * nguong)
            theo_thang_tho[k] = _runs_at_least(tho, cfg.diff_min_run, mu)
        return tong, theo_thang, theo_thang_tho


def gom_vat_the(fg, r, grid, cfg, mu=None, pts=None, dtheta_deg=None):

    nb = len(fg)
    objs = []
    i = 0
    while i < nb:
        if not fg[i]:
            i += 1
            continue
        j = i
        ho = 0
        cuoi = i
        r_truoc = r[i] if not math.isnan(r[i]) else None
        while j < nb:
            if fg[j] and not math.isnan(r[j]):
                if r_truoc is not None:
                    nguong_cu_ly = 90.0 + 0.06 * min(r_truoc, r[j])
                    if abs(r[j] - r_truoc) > nguong_cu_ly:
                        break                                          
                cuoi = j
                r_truoc = r[j]
                ho = 0
            elif mu is not None and mu[j]:
                pass
            else:
                ho += 1
                if ho > cfg.gap_bins:
                    break
            j += 1
        bins = [b for b in range(i, cuoi + 1) if fg[b] and not math.isnan(r[b])]
        i = cuoi + 1
        if len(bins) < cfg.min_object_bins:
            continue

        xs, ys, ds = [], [], []
        for b in bins:
            a = math.radians(grid.bin_angle(b))
            d = r[b]
            xs.append(d * math.sin(a))
            ys.append(d * math.cos(a))
            ds.append(d)
        n_diem = 0
        if pts:
            half = cfg.fov_half_deg
            span = 2.0 * half
            px, py, pd = [], [], []
            for rel, dd, x, y in pts:
                bb = int((rel + half) / span * nb)
                if bins[0] <= bb <= bins[-1]:
                    px.append(x); py.append(y); pd.append(dd)
            n_diem = len(px)
            if n_diem >= max(3, len(bins) // 2):
                xs, ys, ds = px, py, pd
        xs, ys, ds = np.array(xs), np.array(ys), np.array(ds)
        w = 1.0 / np.maximum(ds - ds.min() + 20.0, 1.0) ** 2
        cx = float((xs * w).sum() / w.sum())
        cy = float((ys * w).sum() / w.sum())
        objs.append({
            'bins': (bins[0], bins[-1]),
            'n': len(bins),
            'n_diem': n_diem,
            'cx': cx, 'cy': cy,
            'r': float(math.hypot(cx, cy)),
            'r_min': float(ds.min()),
            'theta': math.atan2(cy, cx),
            'width': float(math.hypot(xs.max() - xs.min(), ys.max() - ys.min())),
        })
    rong_min = cfg.min_object_width_ratio * cfg.max_range_mm

    def du_rong(o):
        b0, b1 = o['bins']
        mep = (b0 <= 0) or (b1 >= nb - 1)
        return o['width'] >= (0.5 * rong_min if mep else rong_min)

    if dtheta_deg and dtheta_deg > 1e-6:
        mat_do_toi_da = (grid.span / float(grid.nb)) / float(dtheta_deg)
        mat_do_can = max(0.35, min(cfg.mat_do_diem,
                                   cfg.ti_le_tia_doi * mat_do_toi_da))
    else:
        mat_do_can = cfg.mat_do_diem

    def du_day(o):







        nd = o.get('n_diem', 0)
        if nd <= 0:
            return True                                                         
        return nd >= max(cfg.min_diem, mat_do_can * o['n'])

    for o in objs:
        o['thua'] = not du_day(o)
    objs = [o for o in objs if o['n'] >= cfg.min_object_points and du_rong(o)]

    i = 0
    while i < len(objs) - 1:
        a, b = objs[i], objs[i + 1]
        ho = b['bins'][0] - a['bins'][1]
        r_a = 0.5 * (a['r'] + a['r_min'])
        r_b = 0.5 * (b['r'] + b['r_min'])
        if ho <= cfg.gap_bins * 2 and abs(r_a - r_b) <= cfg.merge_range_mm:
            na, nb = a['n'], b['n']
            cx = (a['cx'] * na + b['cx'] * nb) / (na + nb)
            cy = (a['cy'] * na + b['cy'] * nb) / (na + nb)
            objs[i] = {
                'bins': (a['bins'][0], b['bins'][1]), 'n': na + nb,
                'cx': cx, 'cy': cy, 'r': float(math.hypot(cx, cy)),
                'r_min': min(a['r_min'], b['r_min']),
                'theta': math.atan2(cy, cx),
                'width': a['width'] + b['width'],
            }
            objs.pop(i + 1)
        else:
            i += 1
    return objs


def xac_nhan_vat_nho(history, cfg):

    a = np.asarray(list(history), dtype=float)
    minimum = int(cfg.vat_nho_min_mau)
    if len(a) < minimum:
        return False
    for count in range(minimum, len(a) + 1):
        w = a[-count:]
        tt = w[:, 0] - w[0, 0]
        duration = float(tt[-1])
        if duration < 0.30 or np.any(np.diff(tt) <= 0) or np.max(np.diff(tt)) > 0.4:
            continue
        p = w[:, 1:]
        net = float(np.linalg.norm(p[-1] - p[0]))
        steps = np.diff(p, axis=0)
        path = float(np.linalg.norm(steps, axis=1).sum())
        if net < cfg.vat_nho_net_mm or net / max(path, 1e-9) < 0.80:
            continue
        tc = tt - tt.mean()
        vel = (tc[:, None] * (p - p.mean(axis=0))).sum(axis=0) / float(tc @ tc)
        residual = p - (p.mean(axis=0) + tc[:, None] * vel)
        error = float(np.sqrt(np.mean(np.sum(residual ** 2, axis=1))))
        speed = float(np.linalg.norm(vel))
        axis = vel / max(speed, 1e-9)
        forward = steps @ axis
        if (error <= cfg.vat_nho_residual_mm
                and 15.0 <= speed <= cfg.max_speed_mm_s
                and np.count_nonzero(forward > 1.0) >= count - 2
                and float(np.max(np.linalg.norm(steps, axis=1))) <= 0.60 * net):
            return True
    return False


def them_vat_nho(objs, mask, r, grid, cfg, pts, dtheta_deg, tracks=()):

    if not cfg.vat_nho_bat or not pts:
        return []
    large = [(o['cx'], o['cy'], o['width']) for o in objs
             if o['width'] > 60.0 or int(o.get('n_diem', 0)) > cfg.vat_nho_max_diem]
    large.extend((tr.last_meas[0], tr.last_meas[1], tr.hud_width) for tr in tracks
                 if tr.n_updates >= 3 and tr.hud_width > 60.0)

    def near_large(x, y):
        return any(math.hypot(x-lx, y-ly) < max(150.0, 1.5*width)
                   for lx, ly, width in large)

    free = mask.copy()
    small = []
    for o in objs:
        b0, b1 = o['bins']
        free[max(0, b0-1):min(grid.nb, b1+2)] = False
        if (3 <= int(o.get('n_diem', 0)) <= cfg.vat_nho_max_diem
                and o.get('thua', False) and o['width'] <= 60.0
                and not near_large(o['cx'], o['cy'])):
            small.append(dict(o, vat_nho=True, vat_nho_rieng=True, thua=False))
    chosen = []
    for p in pts:
        rel, d, x, y = p
        b = int((rel + cfg.fov_half_deg) / grid.span * grid.nb)
        if (0 <= b < grid.nb and free[b] and math.isfinite(r[b])
                and abs(d-r[b]) <= 15.0):
            chosen.append((rel, d, x, y, b))
    chosen.sort(key=lambda p: p[0])
    groups = []
    for p in chosen:
        if (not groups or p[0] - groups[-1][-1][0] > max(1.0, 1.8*dtheta_deg)
                or abs(p[1] - groups[-1][-1][1]) > 18.0):
            groups.append([])
        groups[-1].append(p)
    for group in groups:
        if not 3 <= len(group) <= cfg.vat_nho_max_diem:
            continue
        a = np.asarray(group, dtype=float)
        if len(set(a[:, 0])) < 3 or np.ptp(a[:, 1]) > 25.0:
            continue
        width = float(np.linalg.norm(np.ptp(a[:, 2:4], axis=0)))
        if not 3.0 <= width <= 60.0:
            continue
        cx, cy = np.mean(a[:, 2:4], axis=0)
        if near_large(cx, cy):
            continue
        bs = a[:, 4].astype(int)
        small.append({'cx': float(cx), 'cy': float(cy),
                     'r': float(math.hypot(cx, cy)), 'r_min': float(a[:, 1].min()),
                     'theta': math.atan2(cy, cx), 'width': width,
                     'bins': (int(bs.min()), int(bs.max())),
                     'n': len(set(bs)), 'n_diem': len(group),
                     'thua': False, 'vat_nho': True, 'vat_nho_rieng': True,
                     '_layer_points': frozenset((round(p[0], 6), round(p[1], 6))
                                               for p in group)})
    return small


def gom_nhom_hud(mask, r, grid, cfg, pts):

    if not pts or not np.any(mask):
        return []
    half = cfg.fov_half_deg
    span = 2.0 * half
    nb = grid.nb
    sat_mat = max(20.0, 2.0 * float(cfg.diff_mm))
    chon = []
    for rel, d, x, y in pts:
        b = int((rel + half) / span * nb)
        if b < 0 or b >= nb or not mask[b] or math.isnan(r[b]):
            continue
        if abs(d - r[b]) <= sat_mat:
            chon.append((b, float(d), float(x), float(y)))
    if not chon:
        return []

    cac_nhom = []
    nhom = [chon[0]]
    for p in chon[1:]:
        truoc = nhom[-1]
        ho = p[0] - truoc[0]
        nguong_r = 90.0 + 0.06 * min(p[1], truoc[1])
        if ho <= cfg.gap_bins + 1 and abs(p[1] - truoc[1]) <= nguong_r:
            nhom.append(p)
        else:
            cac_nhom.append(nhom)
            nhom = [p]
    cac_nhom.append(nhom)

    out = []
    rong_san = 0.35 * cfg.min_object_width_ratio * cfg.max_range_mm
    for nhom in cac_nhom:
        bins = sorted({p[0] for p in nhom})
        if len(nhom) < 3 or len(bins) < 2:
            continue
        xs = np.asarray([p[2] for p in nhom], dtype=float)
        ys = np.asarray([p[3] for p in nhom], dtype=float)
        ds = np.asarray([p[1] for p in nhom], dtype=float)
        rong = float(math.hypot(xs.max() - xs.min(), ys.max() - ys.min()))
        if rong < rong_san:
            continue
        w = 1.0 / np.maximum(ds - ds.min() + 20.0, 1.0) ** 2
        cx = float((xs * w).sum() / w.sum())
        cy = float((ys * w).sum() / w.sum())
        out.append({'cx': cx, 'cy': cy, 'width': rong,
                    'bins': (bins[0], bins[-1]), 'n_diem': len(nhom)})
    return out


class Track:
    _next = 1

    def __init__(self, o, t, cfg):
        self.id = Track._next
        Track._next += 1
        self.x = np.array([o['cx'], o['cy'], 0.0, 0.0], dtype=float)
        self.P = np.diag([60.0 ** 2, 60.0 ** 2, 500.0 ** 2, 500.0 ** 2])
        self.anchor = (o['cx'], o['cy'])
        self.r_anchor = o['r']
        self.width_seed_clipped = (cfg.fov_half_deg < 180.0 and
            abs(math.degrees(math.atan2(o['cx'], o['cy']))) > cfg.fov_half_deg-5.0)
        self.last_meas = (o['cx'], o['cy'])                                             
        self.last_meas_step = (0.0, 0.0)
        self.last_meas_dt = 1.0 / 6.0
        self.nis_cuoi = 0.0
        self.vi_tri_hud = (float(o['cx']), float(o['cy']))
        self.van_toc_hud = (0.0, 0.0)
        self.he_so_hud = 1.0
        self.t_hud = t
        self.hud_raw_prev = self.vi_tri_hud
        self.hud_filter_pos = self.vi_tri_hud
        self.hud_filter_vel = (0.0, 0.0)
        self.t_hud_filter = t
        self.trong_cum_gop = False
        self.gop_hud_active = False
        self.gop_hud_t0 = t
        self.gop_hud_p0 = self.vi_tri_hud
        self.gop_hud_v0 = (0.0, 0.0)
        self.hud_tu_diem = False
        self.hud_bins = tuple(o.get('bins', (0, 0)))
        self.hud_width = float(o.get('width', 0.0))
        self.fast_step_prev = None
        self.cham_hits = 0
        self.t_created = t
        self.t_seen = t
        self.state = STATIC
        self.hits = 0
        self.misses = 0
        self.last_matched = True
        self.n_updates = 1
        self.evidence_bins = 0
        self.gates = []
        self.dang_tin_cay = True
        self.vi_tri_ve = (float(o['cx']), float(o['cy']))
        self.t_vi_tri_ve = t
        self.sigma_goc_ve_deg = float(self.bearing_sigma_deg)
        self.sigma_tam_ve_mm = float(self.range_sigma_mm)
        self.dong_bang_hien_thi = False
        self.vi_tri_bien_cuoi = (float(o['cx']), float(o['cy']))
        self.van_toc_bien_cuoi = (0.0, 0.0)
        self.buoc_do_bien_cuoi = (0.0, 0.0)
        self.co_cong_manh = False
        self.bi_che = False
        self.so_vong_che = 0
        self.t_chot_dong = None
        self.tho_troi = 0.0                                     
        self.g6_bins = 0                                             
        self.feat = {'d_anchor': 0.0, 'd_radial': 0.0, 'straight': 0.0}
        self.lich_do = deque(maxlen=int(getattr(cfg, 'pham_vi_so_vong', 30)))
        self.lich_do.append((float(o['cx']), float(o['cy'])))
        self.lich_rong = deque(maxlen=int(getattr(cfg, 'rong_so_vong', 20)))
        if float(o.get('width', 0.0)) > 0:
            self.lich_rong.append(float(o['width']))
        self.lich_rong_id = deque(maxlen=int(getattr(cfg, 'rong_id_so_vong', 80)))
        if float(o.get('width', 0.0)) > 0:
            self.lich_rong_id.append(float(o['width']))
        self.lich_ty_le_diem_id = deque(
            maxlen=int(getattr(cfg, 'diem_id_so_vong', 80)))
        self.lich_cuong_do_id = deque(
            maxlen=int(getattr(cfg, 'cuong_do_id_so_vong', 80)))
        self.cap_nhat_cuong_do_id(o, cfg, True)
        self.hud_n_diem_that = int(o.get('n_diem', o.get('n', 0)))
        self.hud_n_diem_du_kien = max(self.hud_n_diem_that, 1)
        self.hud_ty_le_thay = 1.0
        self.dang_che_mot_phan = False
        self.hud_tu_lop_cu_ly = False
        self.bao_ve_lop_cu_ly = 0
        self.lich_ghep = deque(maxlen=25)
        self.hist = deque(maxlen=24)
        self.hist.append((t, o['cx'], o['cy']))
        self.vat_nho = bool(o.get('vat_nho', False))
        self.vat_nho_rieng = bool(o.get('vat_nho_rieng', False))
        self.lich_vat_nho = deque(maxlen=24)
        if self.vat_nho:
            self.lich_vat_nho.append((t, o['cx'], o['cy']))
        self.id_tach_rieng = set()

    def cap_nhat_cuong_do_id(self, o, cfg, duoc_hoc):
        if not duoc_hoc or getattr(cfg, 'cuong_do_id_bat', 0.0) < 0.5:
            return
        lr = o.get('cuong_do_log_rho')
        if lr is None or not math.isfinite(float(lr)):
            return
        if int(o.get('cuong_do_n', 0)) < int(cfg.cuong_do_mau_toi_thieu):
            return
        if len(self.lich_cuong_do_id) >= int(cfg.cuong_do_id_khoa_sau):
            return
        lr = float(lr)
        if len(self.lich_cuong_do_id) < 6:
            self.lich_cuong_do_id.append(lr)
            return
        aa = np.asarray(self.lich_cuong_do_id, dtype=float)
        med = float(np.median(aa))
        mad = 1.4826 * float(np.median(np.abs(aa - med)))
        sig = max(float(cfg.cuong_do_sigma_log_san), mad)
        if abs(lr - med) <= cfg.cuong_do_nguong_ngoai_lai_sigma * sig:
            self.lich_cuong_do_id.append(lr)

    def predict(self, dt, cfg):
        dt = max(dt, 1e-3)
        F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], float)
        q = cfg.sigma_a_mm_s2 ** 2
        Q = np.array([[dt**4/4, 0, dt**3/2, 0],
                      [0, dt**4/4, 0, dt**3/2],
                      [dt**3/2, 0, dt**2, 0],
                      [0, dt**3/2, 0, dt**2]], float) * q
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def nis_cho_do(self, o, cfg, dtheta_deg):

        n = max(int(o.get('n', 1)), 1)
        d = max(float(o.get('r', math.hypot(o['cx'], o['cy']))), 1.0)
        if getattr(cfg, 'dung_sigma_r_moi', True):
            sr = float(cfg.sigma_r_tia_moi_mm) / math.sqrt(n)
        else:
            sr = cfg.sigma_r_mm * (d / 1000.0) ** cfg.sigma_r_exp
            sr = max(sr, 3.0) / math.sqrt(n)
        st = max(d * math.radians(dtheta_deg), 6.0) / math.sqrt(n)
        rong = float(o.get('width', 0.0))
        st = max(st, 0.12 * rong)
        che_mot_phan = bool(o.get('che_mot_phan', False))
        if che_mot_phan:
            st = max(st, 0.50 * float(o.get('width_expected', rong)))
        if not getattr(cfg, 'dung_sigma_r_moi', False):
            sr = max(sr, 0.06 * rong)

        th = float(o.get('theta', math.atan2(o['cy'], o['cx'])))
        c, sn = math.cos(th), math.sin(th)
        rot = np.array([[c, -sn], [sn, c]])
        R = rot @ np.diag([sr ** 2, st ** 2]) @ rot.T
        y = np.array([o['cx'] - self.x[0], o['cy'] - self.x[1]], float)
        S = self.P[:2, :2] + R
        try:
            eps = float(y @ np.linalg.solve(S, y))
        except np.linalg.LinAlgError:
            return float('inf')
        return eps if math.isfinite(eps) else float('inf')

    def update(self, o, t, cfg, dtheta_deg, chung_cum=False):
        expected = self.be_rong_id_uoc
        if (self.state == DYNAMIC and expected >= 60.0
                and (getattr(self, 'bi_che', False)
                     or t-getattr(self, 'partial_motion_time', -1e9) < 1.0)
                and 0 < float(o.get('width', 0)) < 0.75*expected
                and not o.get('che_mot_phan', False)):
            o = dict(o, partial_surface_motion=True)
        if o.get('partial_surface_motion', False) and getattr(self, 'bi_che', False):
            self.partial_motion_time = float(t)
        self.surface_observation = o
        if not chung_cum and not o.get('che_mot_phan', False):
            self.vat_nho_rieng = bool(o.get('vat_nho_rieng', False))
        if self.vat_nho or o.get('vat_nho', False):
            self.vat_nho = True
            if (not chung_cum and not o.get('che_mot_phan', False)
                    and 3 <= int(o.get('n_diem', 0)) <= cfg.vat_nho_max_diem):
                if self.lich_vat_nho and t - self.lich_vat_nho[-1][0] > 0.4:
                    self.lich_vat_nho.clear()
                self.lich_vat_nho.append((t, o['cx'], o['cy']))
            else:
                self.lich_vat_nho.clear()
        self.last_meas_dt = max(float(t - self.t_seen), 1e-3)
        self.last_meas_step = (o['cx'] - self.last_meas[0],
                               o['cy'] - self.last_meas[1])
        self.last_meas = (o['cx'], o['cy'])
        self.lich_do.append((float(o['cx']), float(o['cy'])))
        rong_do = float(o.get('width', 0.0))
        che_mot_phan = bool(o.get('che_mot_phan', False))
        duoc_hoc_hinh_dang = not chung_cum and not che_mot_phan
        if rong_do > 0 and duoc_hoc_hinh_dang:
            self.lich_rong.append(rong_do)
            if len(self.lich_rong_id) < 6:
                self.lich_rong_id.append(rong_do)
            else:
                rr = np.asarray(self.lich_rong_id, dtype=float)
                med = float(np.median(rr))
                mad = 1.4826 * float(np.median(np.abs(rr - med)))
                sig = max(float(cfg.rong_id_sigma_san_mm),
                          float(cfg.rong_id_sigma_ty_le) * med, mad)
                if abs(rong_do - med) <= cfg.rong_id_nguong_ngoai_lai_sigma * sig:
                    self.lich_rong_id.append(rong_do)
        n_diem_do = int(o.get('n_diem', o.get('n', 0)))
        if duoc_hoc_hinh_dang and rong_do > 0 and n_diem_do > 0:
            so_tia = self._so_tia_hinh_hoc(rong_do, float(o.get('r', 0.0)),
                                           dtheta_deg)
            ti_le = min(max(n_diem_do / max(so_tia, 1.0), 0.05), 1.5)
            if len(self.lich_ty_le_diem_id) < 6:
                self.lich_ty_le_diem_id.append(ti_le)
            else:
                aa = np.asarray(self.lich_ty_le_diem_id, dtype=float)
                med = float(np.median(aa))
                mad = 1.4826 * float(np.median(np.abs(aa - med)))
                sig = max(float(cfg.diem_id_sigma_san), mad)
                if abs(ti_le - med) <= cfg.diem_id_nguong_ngoai_lai_sigma * sig:
                    self.lich_ty_le_diem_id.append(ti_le)
        self.cap_nhat_cuong_do_id(o, cfg, duoc_hoc_hinh_dang)
        n = max(o['n'], 1)
        d = max(o['r'], 1.0)
        if getattr(cfg, 'dung_sigma_r_moi', True):
            sr = float(cfg.sigma_r_tia_moi_mm) / math.sqrt(n)
        else:
            sr = cfg.sigma_r_mm * (d / 1000.0) ** cfg.sigma_r_exp
            sr = max(sr, 3.0) / math.sqrt(n)
        st = max(d * math.radians(dtheta_deg), 6.0) / math.sqrt(n)

        rong = float(o.get('width', 0.0))
        st = max(st, 0.12 * rong)
        if che_mot_phan:
            st = max(st, 0.50 * float(o.get('width_expected', rong)))
        if not getattr(cfg, 'dung_sigma_r_moi', False):
            sr = max(sr, 0.06 * rong)
        self.sigma_r_used = float(sr)
        self.sigma_t_used = float(st)

        th = o['theta']
        c, s = math.cos(th), math.sin(th)
        Rot = np.array([[c, -s], [s, c]])
        R = Rot @ np.diag([sr ** 2, st ** 2]) @ Rot.T

        if chung_cum and getattr(cfg, 'gop_phong_R', True):
            them = (0.5 * max(rong, 1.0)) ** 2
            R = R + np.eye(2) * them

        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], float)
        z = np.array([o['cx'], o['cy']], float)
        y = z - H @ self.x
        S = H @ self.P @ H.T + R

        eps = float(y @ np.linalg.solve(S, y))
        self.nis_cuoi = eps
        R_eff = R
        if eps > cfg.nis_nguong:
            he_so = eps / cfg.nis_nguong
            R_eff = he_so * R
            S = H @ self.P @ H.T + R_eff

        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I_KH = np.eye(4) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R_eff @ K.T
        self.P = 0.5 * (self.P + self.P.T)

        v = math.hypot(self.x[2], self.x[3])
        if v > cfg.max_speed_mm_s:
            f = cfg.max_speed_mm_s / v
            self.x[2] *= f
            self.x[3] *= f

        sx, sy = self.last_meas_step
        buoc = math.hypot(sx, sy)
        nen = max(float(cfg.diff_mm), 1e-6)
        u = min(1.0, max(0.0, (buoc - 0.5 * nen) / nen))
        g_buoc = u * u * (3.0 - 2.0 * u)
        g_nis = (0.0 if eps <= cfg.nis_nguong else
                 1.0 - cfg.nis_nguong / max(eps, 1e-9))
        g = max(g_buoc, g_nis)
        if o.get('partial_surface_motion', False):
            g = 0.0                                                           

        kx, ky = self.pos
        mx, my = self.last_meas
        hx0, hy0 = self.vi_tri_hud
        if buoc <= 0.5 * nen:
            if math.hypot(mx - hx0, my - hy0) <= 0.5 * nen:
                tx, ty = hx0, hy0
            else:
                tx, ty = mx, my
            g_ve = 0.0
        else:
            tx = kx + g * (mx - kx)
            ty = ky + g * (my - ky)
            g_ve = g
        if not (math.isfinite(tx) and math.isfinite(ty)):
            tx, ty = hx0, hy0
        hx, hy, hvx, hvy = self.loc_hud(tx, ty, t, cfg)
        if o.get('partial_surface_motion', False):
            limit = max(float(cfg.diff_mm), 0.20*expected)
            displacement = math.hypot(hx-hx0, hy-hy0)
            if displacement > limit:
                hx = hx0+(hx-hx0)*limit/displacement
                hy = hy0+(hy-hy0)*limit/displacement
                hud_dt = max(t-self.t_hud, 1e-3)
                hvx, hvy = (hx-hx0)/hud_dt, (hy-hy0)/hud_dt
                self.hud_filter_pos = (hx, hy)
                self.hud_raw_prev = (hx, hy)
                self.hud_filter_vel = (hvx, hvy)
        hv = math.hypot(hvx, hvy)
        if hv > cfg.max_speed_mm_s:
            f = cfg.max_speed_mm_s / hv
            hvx, hvy = hvx * f, hvy * f
        self.vi_tri_hud = (float(hx), float(hy))
        self.van_toc_hud = (float(hvx), float(hvy))
        self.he_so_hud = float(g_ve)
        self.gop_hud_active = False
        self.t_hud = t
        self.hud_tu_diem = False
        self.hud_bins = tuple(o.get('bins', self.hud_bins))
        self.hud_width = float(
            o.get('width_expected', self.hud_width)
            if che_mot_phan else o.get('width', self.hud_width))
        self.hud_n_diem_that = n_diem_do
        self.hud_n_diem_du_kien = max(
            int(o.get('n_diem_du_kien', 0)),
            self.so_diem_du_kien(dtheta_deg),
            n_diem_do,
        )
        self.hud_ty_le_thay = min(1.0, n_diem_do /
                                  max(self.hud_n_diem_du_kien, 1))
        self.dang_che_mot_phan = che_mot_phan
        self.hud_tu_lop_cu_ly = bool(o.get('tu_lop_cu_ly', False))

        self.hist.append((t, self.x[0], self.x[1]))
        self.t_seen = t
        self.n_updates += 1

        if self.bearing_sigma_deg <= cfg.goc_ve_max:
            self.vi_tri_ve = self.vi_tri_hud
            self.t_vi_tri_ve = t
            self.sigma_goc_ve_deg = float(self.bearing_sigma_deg)
            self.sigma_tam_ve_mm = float(self.range_sigma_mm)

        self.vi_tri_bien_cuoi = (float(o['cx']), float(o['cy']))
        self.van_toc_bien_cuoi = (float(self.x[2]), float(self.x[3]))
        self.buoc_do_bien_cuoi = tuple(map(float, self.last_meas_step))

    def loc_hud(self, x_raw, y_raw, t, cfg):
        dt = max(float(t - self.t_hud_filter), 1e-3)
        rx0, ry0 = self.hud_raw_prev
        dx_raw = (float(x_raw) - rx0) / dt
        dy_raw = (float(y_raw) - ry0) / dt
        ad = 1.0 / (1.0 + 1.0 /
                    (2.0 * math.pi * cfg.hud_derivative_cutoff_hz * dt))
        dvx0, dvy0 = self.hud_filter_vel
        dvx = ad * dx_raw + (1.0 - ad) * dvx0
        dvy = ad * dy_raw + (1.0 - ad) * dvy0
        cutoff = cfg.hud_min_cutoff_hz + cfg.hud_beta * math.hypot(dvx, dvy)
        alpha = 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))
        fx0, fy0 = self.hud_filter_pos
        fx = alpha * float(x_raw) + (1.0 - alpha) * fx0
        fy = alpha * float(y_raw) + (1.0 - alpha) * fy0
        self.hud_raw_prev = (float(x_raw), float(y_raw))
        self.hud_filter_pos = (float(fx), float(fy))
        self.hud_filter_vel = (float(dvx), float(dvy))
        self.t_hud_filter = float(t)
        return float(fx), float(fy), float(dvx), float(dvy)

    def cap_nhat_hud_cum_gop(self, t, cfg):
        if not self.gop_hud_active:
            self.gop_hud_active = True
            self.gop_hud_t0 = float(t)
            self.gop_hud_p0 = tuple(self.vi_tri_hud)
            vx, vy = float(self.x[2]), float(self.x[3])
            if math.hypot(vx, vy) < cfg.gop_hud_speed_min_mm_s:
                vx = vy = 0.0
            self.gop_hud_v0 = (vx, vy)
        vx, vy = self.gop_hud_v0
        elapsed = max(0.0, float(t) - self.gop_hud_t0)
        horizon = min(elapsed, max(float(cfg.gop_hud_predict_s), 0.0))
        x0, y0 = self.gop_hud_p0
        px, py = x0 + vx * horizon, y0 + vy * horizon
        if t-getattr(self, 'partial_motion_time', -1e9) < 1.0:
            budget = max(float(cfg.diff_mm), 0.25*self.be_rong_id_uoc)
            distance = math.hypot(px-x0, py-y0)
            if distance > budget:
                px = x0+(px-x0)*budget/distance
                py = y0+(py-y0)*budget/distance
                vx = vy = 0.0
        rr = math.hypot(px, py)
        gh = 0.98 * cfg.max_range_mm
        if rr > gh:
            px, py = px * gh / rr, py * gh / rr
        self.vi_tri_hud = (float(px), float(py))
        self.vi_tri_ve = self.vi_tri_hud
        self.t_vi_tri_ve = float(t)
        self.hud_filter_pos = self.vi_tri_hud
        self.hud_raw_prev = self.vi_tri_hud
        self.t_hud_filter = float(t)
        dang_chay = (math.hypot(vx, vy) >= cfg.gop_hud_speed_min_mm_s
                     and elapsed < cfg.gop_hud_predict_s)
        self.van_toc_hud = ((vx, vy) if dang_chay else (0.0, 0.0))
        return dang_chay

    @property
    def pos(self):
        return float(self.x[0]), float(self.x[1])

    @property
    def speed(self):
        return float(math.hypot(self.x[2], self.x[3]))

    @property
    def range_mm(self):
        return float(math.hypot(self.x[0], self.x[1]))

    @property
    def bearing_deg(self):
        return math.degrees(math.atan2(self.x[0], self.x[1]))

    @property
    def bearing_sigma_deg(self):


        x, y = float(self.x[0]), float(self.x[1])
        d2 = x * x + y * y
        if d2 < 100.0:
            return 90.0
        J = np.array([y / d2, -x / d2])
        return math.degrees(math.sqrt(max(float(J @ self.P[:2, :2] @ J.T), 0.0)))

    @property
    def range_sigma_mm(self):
        x, y = float(self.x[0]), float(self.x[1])
        r = math.hypot(x, y)
        if r < 10.0:
            return 0.0
        J = np.array([x / r, y / r])
        return math.sqrt(max(float(J @ self.P[:2, :2] @ J.T), 0.0))

    def co_bang_chung_ra_khoi(self, cfg, t, dt):

        if self.last_matched or self.misses < int(cfg.so_vong_xac_nhan_ra):
            return False

        x0, y0 = self.vi_tri_bien_cuoi
        vx, vy = self.van_toc_bien_cuoi
        dx, dy = self.buoc_do_bien_cuoi
        toc_do = math.hypot(vx, vy)
        if toc_do < cfg.toc_do_ra_toi_thieu_mm_s:
            return False

        tuoi = max(0.0, t - self.t_seen)
        x1, y1 = x0 + vx * tuoi, y0 + vy * tuoi
        r0 = math.hypot(x0, y0)
        r1 = math.hypot(x1, y1)
        if r0 < 1.0:
            return False

        be_day_vanh = max(cfg.max_range_mm - cfg.min_range_mm, 1.0)
        le_mm = max(25.0, min(0.25 * be_day_vanh,
                             1.5 * toc_do * max(dt, 1e-3)))
        vr = (x0 * vx + y0 * vy) / r0
        buoc_xuyen_tam = (x0 * dx + y0 * dy) / r0
        buoc_toi_thieu = max(2.0, 0.25 * cfg.diff_mm)

        if (r0 >= cfg.max_range_mm - le_mm
                and r1 > cfg.max_range_mm
                and vr > cfg.toc_do_ra_toi_thieu_mm_s
                and buoc_xuyen_tam > buoc_toi_thieu):
            return True

        if (r0 <= cfg.min_range_mm + le_mm
                and r1 < cfg.min_range_mm
                and vr < -cfg.toc_do_ra_toi_thieu_mm_s
                and buoc_xuyen_tam < -buoc_toi_thieu):
            return True

        half = float(cfg.fov_half_deg)
        if half < 179.0:
            goc0 = math.degrees(math.atan2(x0, y0))
            goc1 = math.degrees(math.atan2(x1, y1))
            goc_truoc = math.degrees(math.atan2(x0 - dx, y0 - dy))
            dau = 1.0 if goc0 >= 0.0 else -1.0
            le_goc = max(2.0, min(15.0,
                                  math.degrees(le_mm / max(r0, 1.0))))
            buoc_huong_ra = dau * (goc0 - goc_truoc)
            van_toc_huong_ra = dau * (goc1 - goc0)
            if (abs(goc0) >= half - le_goc
                    and abs(goc1) > half
                    and buoc_huong_ra > 0.15
                    and van_toc_huong_ra > 0.0):
                return True

        return False

    def nhan_so_do_tu_vet_trung(self, khac):

        self.x = khac.x.copy()
        self.P = khac.P.copy()
        self.last_meas = tuple(khac.last_meas)
        self.last_meas_step = tuple(khac.last_meas_step)
        self.last_meas_dt = khac.last_meas_dt
        self.nis_cuoi = khac.nis_cuoi
        self.vi_tri_hud = tuple(khac.vi_tri_hud)
        self.van_toc_hud = tuple(khac.van_toc_hud)
        self.he_so_hud = khac.he_so_hud
        self.t_hud = khac.t_hud
        self.hud_tu_diem = khac.hud_tu_diem
        self.hud_bins = tuple(khac.hud_bins)
        self.hud_width = khac.hud_width
        self.fast_step_prev = khac.fast_step_prev
        self.cham_hits = max(self.cham_hits, khac.cham_hits)
        self.hud_raw_prev = tuple(khac.hud_raw_prev)
        self.hud_filter_pos = tuple(khac.hud_filter_pos)
        self.hud_filter_vel = tuple(khac.hud_filter_vel)
        self.t_hud_filter = khac.t_hud_filter
        self.trong_cum_gop = khac.trong_cum_gop
        self.gop_hud_active = khac.gop_hud_active
        self.gop_hud_t0 = khac.gop_hud_t0
        self.gop_hud_p0 = tuple(khac.gop_hud_p0)
        self.gop_hud_v0 = tuple(khac.gop_hud_v0)
        self.t_seen = khac.t_seen
        self.last_matched = True
        self.misses = 0
        self.hits = max(self.hits, khac.hits)
        self.n_updates = max(self.n_updates, khac.n_updates) + 1
        self.evidence_bins = khac.evidence_bins
        self.gates = list(khac.gates)
        self.dang_tin_cay = True
        self.vi_tri_ve = tuple(khac.vi_tri_ve)
        self.t_vi_tri_ve = khac.t_vi_tri_ve
        self.sigma_goc_ve_deg = khac.sigma_goc_ve_deg
        self.sigma_tam_ve_mm = khac.sigma_tam_ve_mm
        self.dong_bang_hien_thi = False
        self.vi_tri_bien_cuoi = tuple(khac.vi_tri_bien_cuoi)
        self.van_toc_bien_cuoi = tuple(khac.van_toc_bien_cuoi)
        self.buoc_do_bien_cuoi = tuple(khac.buoc_do_bien_cuoi)
        self.co_cong_manh = self.co_cong_manh or khac.co_cong_manh
        self.tho_troi = khac.tho_troi
        self.g6_bins = khac.g6_bins
        self.feat = dict(khac.feat)
        if khac.hist:
            self.hist.append(khac.hist[-1])
        self.lich_ghep.append(1.0)

    def tinh_dac_trung(self):
        px, py = self.pos
        d_anchor = math.hypot(px - self.anchor[0], py - self.anchor[1])
        d_radial = self.r_anchor - self.range_mm                            

        h = list(self.hist)
        thang = 0.0
        if len(h) >= 3:
            d_net = math.hypot(h[-1][1] - h[0][1], h[-1][2] - h[0][2])
            path = sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(h, h[1:]))
            thang = d_net / path if path > 1e-6 else 0.0

        self.feat = {'d_anchor': d_anchor, 'd_radial': d_radial, 'straight': thang}
        return self.feat

    def xet_cong(self, cfg, ev_theo_thang):

        f = self.feat
        g = []
        if ev_theo_thang.get(1, 0) >= cfg.evidence_min_bins:
            g.append('G1')
        if any(ev_theo_thang.get(k, 0) >= cfg.evidence_min_bins
               for k in cfg.diff_scales if k > 1):
            g.append('G2')
        if f['d_radial'] > cfg.g3_radial_mm:
            g.append('G3')
        if f['d_anchor'] > cfg.g4_anchor_mm:
            g.append('G4')
        if self.tho_troi >= cfg.evidence_min_bins:
            g.append('G5')
        if self.g6_bins >= cfg.evidence_min_bins:
            g.append('G6')
        self.gates = g
        return bool(g)

    def ty_le_ghep(self):
        if len(self.lich_ghep) < 15:
            return 1.0
        return sum(self.lich_ghep) / len(self.lich_ghep)

    def xet_xac_nhan_nhanh(self, cfg, g1_manh, matched):

        if getattr(cfg, 'fast_confirm', 0.0) < 0.5 or not matched or not g1_manh:
            self.fast_step_prev = None
            return False

        dx, dy = self.last_meas_step
        do_dai = math.hypot(dx, dy)
        if do_dai < cfg.diff_mm:
            self.fast_step_prev = None
            return False

        truoc = self.fast_step_prev
        self.fast_step_prev = (dx, dy)
        if truoc is None:
            return False

        tx, ty = truoc
        do_dai_truoc = math.hypot(tx, ty)
        if do_dai_truoc < cfg.diff_mm:
            return False
        cos_huong = (tx * dx + ty * dy) / (do_dai_truoc * do_dai)
        if cos_huong < cfg.fast_confirm_cos:
            return False

        self.co_cong_manh = True
        if 'GF' not in self.gates:
            self.gates.append('GF')
        return True

    @property
    def be_rong_uoc(self):

        if len(self.lich_rong) < 3:
            return 0.0
        return float(np.median(self.lich_rong))

    @staticmethod
    def _so_tia_hinh_hoc(rong_mm, r_mm, dtheta_deg):
        if rong_mm <= 0 or r_mm <= 1 or dtheta_deg <= 1e-6:
            return 1.0
        span_deg = math.degrees(2.0 * math.atan2(0.5 * rong_mm, r_mm))
        return max(span_deg / dtheta_deg, 1.0)

    @property
    def ty_le_diem_id_uoc(self):
        if len(self.lich_ty_le_diem_id) < 3:
            return 1.0
        return float(np.median(self.lich_ty_le_diem_id))

    def so_diem_du_kien(self, dtheta_deg):
        rong = self.be_rong_id_uoc
        if rong <= 0:
            rong = max(float(self.hud_width), 1.0)
        n = self._so_tia_hinh_hoc(rong, self.range_mm, dtheta_deg)
        return max(1, int(round(n * self.ty_le_diem_id_uoc)))

    @property
    def be_rong_id_uoc(self):
        if len(self.lich_rong_id) < 6:
            return 0.0
        return float(np.median(self.lich_rong_id))

    def sigma_be_rong_id(self, cfg):
        if len(self.lich_rong_id) < 6:
            return float('inf')
        rr = np.asarray(self.lich_rong_id, dtype=float)
        med = float(np.median(rr))
        mad = 1.4826 * float(np.median(np.abs(rr - med)))
        return max(float(cfg.rong_id_sigma_san_mm),
                   float(cfg.rong_id_sigma_ty_le) * med, mad)

    @property
    def cuong_do_id_uoc(self):
        if len(self.lich_cuong_do_id) < 6:
            return None
        return float(np.median(self.lich_cuong_do_id))

    def sigma_cuong_do_id(self, cfg):
        if len(self.lich_cuong_do_id) < 6:
            return float('inf')
        aa = np.asarray(self.lich_cuong_do_id, dtype=float)
        med = float(np.median(aa))
        mad = 1.4826 * float(np.median(np.abs(aa - med)))
        return max(float(cfg.cuong_do_sigma_log_san), mad)

    def pham_vi_do(self):

        if len(self.lich_do) < 2:
            return 0.0
        P = np.asarray(self.lich_do, dtype=float)
        d = P[:, None, :] - P[None, :, :]
        return float(np.sqrt((d * d).sum(-1)).max())

    def chuyen_dong_cham_nhat_quan(self, cfg):
        P = np.asarray(list(self.lich_do), dtype=float)
        if len(P) < int(cfg.cham_min_mau):
            return False
        z = P - P.mean(axis=0)
        try:
            vals, vecs = np.linalg.eigh(z.T @ z)
        except np.linalg.LinAlgError:
            return False
        tong = float(vals.sum())
        if tong <= 1e-9:
            return False
        axis = vecs[:, int(np.argmax(vals))]
        proj = z @ axis
        if proj[-1] < proj[0]:
            proj = -proj
        span = float(np.ptp(proj))
        net = float(np.linalg.norm(P[-1] - P[0]))
        path = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
        thang = net / max(path, 1e-9)
        tuyen_tinh = float(vals.max()) / tong
        don_dieu = float(np.mean(np.diff(proj) >= -3.0))
        return (span >= cfg.cham_span_mm
                and net >= cfg.cham_net_ratio * cfg.cham_span_mm
                and thang >= cfg.cham_straight_min
                and tuyen_tinh >= cfg.cham_linearity_min
                and don_dieu >= cfg.cham_monotonic_min)

    def cap_nhat_trang_thai(self, cfg, co_bang_chung, matched, bi_che=False):
        if bi_che:
            self.hits = 0
            self.cham_hits = 0
            return
        self.lich_ghep.append(1.0 if matched else 0.0)
        if not matched:
            self.hits = 0
            self.cham_hits = 0
            self.misses += 1
            if (self.state == DYNAMIC and cfg.latch_dynamic < 0.5
                    and self.misses >= 4):
                self.state = SUSPECT
            return

        self.misses = 0
        if self.state == DYNAMIC:
            return                       

        if self.vat_nho:
            if xac_nhan_vat_nho(self.lich_vat_nho, cfg):
                self.state = DYNAMIC
                self.gates = ['GN']
                self.co_cong_manh = True
                self.t_chot_dong = self.t_seen
                return
            if self.vat_nho_rieng:
                self.state = STATIC
                return

        cham = co_bang_chung and self.chuyen_dong_cham_nhat_quan(cfg)
        self.cham_hits = self.cham_hits + 1 if cham else 0
        if self.cham_hits >= int(cfg.cham_confirm_frames):
            self.co_cong_manh = True
            if 'GS' not in self.gates:
                self.gates.append('GS')
        if co_bang_chung and any(g in ('G3', 'G4') for g in self.gates):
            self.co_cong_manh = True
        can = int(cfg.k_confirm if self.co_cong_manh else cfg.k_confirm_yeu)
        self.hits = self.hits + 1 if co_bang_chung else 0

        du_duong = (cfg.pham_vi_toi_thieu_mm <= 0.0
                    or self.pham_vi_do() >= cfg.pham_vi_toi_thieu_mm
                    or self.cham_hits >= int(cfg.cham_confirm_frames))
        if self.hits >= can and not du_duong:
            self.state = SUSPECT                                                 
            return
        if self.hits >= can:
            self.state = DYNAMIC
            if self.t_chot_dong is None:
                self.t_chot_dong = self.t_seen
        else:
            self.state = SUSPECT if co_bang_chung else STATIC


def _huong_va_nua_goc(cx, cy, rong):
    r = max(math.hypot(cx, cy), 1.0)
    return (math.degrees(math.atan2(cx, cy)),
            math.degrees(math.atan2(max(rong, 1.0) * 0.5, r)), r)


def tach_lop_cu_ly_theo_vet(objs, pts, tracks, grid, cfg, dtheta_deg):

    dyn_tracks = [tr for tr in tracks
                  if tr.state == DYNAMIC and tr.n_updates >= 3]
    if (not getattr(cfg, 'lop_cu_ly_bat', 0.0)
            or not pts or len(dyn_tracks) < 2 or not objs):
        return objs
    nb = grid.nb
    half = cfg.fov_half_deg
    span = 2.0 * half
    bin_deg = span / max(float(nb), 1.0)
    ket_qua = []

    for o in objs:
        b0, b1 = o.get('bins', (0, -1))
        if o.get('layer_track_id') is not None:
            ket_qua.append(o)
            continue
        ung_vien = []
        angular_support = {}
        for tr in dyn_tracks:
            if (tr.state != DYNAMIC or tr.n_updates < 3
                    or tr.id in o.get('_surface_exclude', ())):
                continue
            px, py = tr.pos
            rr = math.hypot(px, py)
            if rr < cfg.min_range_mm or rr > cfg.max_range_mm:
                continue
            goc = math.degrees(math.atan2(px, py))
            bc = int((goc + half) / span * nb)
            rong_id = tr.be_rong_id_uoc
            if rong_id <= 0:
                rong_id = max(float(tr.hud_width), 1.0)
            nua_deg = math.degrees(math.atan2(0.5 * rong_id, max(rr, 1.0)))
            nua_o = int(math.ceil(nua_deg / max(bin_deg, 1e-6))) \
                + int(cfg.lop_cu_ly_le_goc_o)
            if bc + nua_o < b0 or bc - nua_o > b1:
                continue
            gate_r = max(float(cfg.lop_cu_ly_cong_san_mm),
                         float(cfg.lop_cu_ly_cong_theo_rong) * rong_id)
            gate_r = min(gate_r, float(cfg.lop_cu_ly_cong_toi_da_mm))
            ung_vien.append((tr, rr, goc, rong_id, gate_r))
            angular_support[tr.id] = (bc-nua_o, bc+nua_o)

        if len(ung_vien) < 2:
            ket_qua.append(o)
            continue
        own_count = 0
        for other in objs:
            k0, k1 = other.get('bins', (0, -1))
            if (math.hypot(other['cx']-o['cx'], other['cy']-o['cy'])
                    <= cfg.gate_base_mm
                    or any(angular_support[tr.id][0] <= k1
                           and angular_support[tr.id][1] >= k0
                           for tr, *_ in ung_vien)):
                own_count += 1
        if own_count >= len(ung_vien):
            ket_qua.append(o)
            continue
        rs = sorted(x[1] for x in ung_vien)
        if max((b - a for a, b in zip(rs, rs[1:])), default=0.0) \
                < cfg.lop_cu_ly_cach_vet_toi_thieu_mm:
            ket_qua.append(o)
            continue

        diem = []
        for rel, dd, x, y in pts:
            bb = int((rel + half) / span * nb)
            if b0 <= bb <= b1:
                diem.append((rel, dd, x, y, bb))
        if len(diem) < 2 * int(cfg.lop_cu_ly_diem_toi_thieu):
            ket_qua.append(o)
            continue

        radial = []
        for p in sorted(diem, key=lambda p: p[1]):
            if not radial or p[1] - radial[-1][-1][1] >= 12.0:
                radial.append([])
            radial[-1].append(p)
        radial = [pp for pp in radial
                  if len(pp) >= int(cfg.lop_cu_ly_diem_toi_thieu)]
        if len(radial) < 2 or len(radial) > len(ung_vien):
            ket_qua.append(o)
            continue
        nhom = {tr.id: [] for tr, *_ in ung_vien}
        ambiguous = False
        for pp in radial:
            rm = float(np.median([p[1] for p in pp]))
            choices = sorted((abs(rm-rr), tr.id, gate_r)
                             for tr, rr, _, _, gate_r in ung_vien)
            if (choices[0][0] > choices[0][2]
                    or choices[1][0] - choices[0][0] < 5.0
                    or nhom[choices[0][1]]):
                ambiguous = True
                break
            nhom[choices[0][1]] = pp
        if ambiguous:
            ket_qua.append(o)
            continue

        lop = []
        for tr, rr, goc, rong_id, _ in ung_vien:
            pp = nhom.get(tr.id, [])
            if len(pp) < int(cfg.lop_cu_ly_diem_toi_thieu):
                continue
            ds0 = np.asarray([p[1] for p in pp], dtype=float)
            med0 = float(np.median(ds0))
            mad0 = 1.4826 * float(np.median(np.abs(ds0 - med0)))
            le = max(4.0, 3.5 * mad0)
            sach = [p for p in pp if abs(p[1] - med0) <= le]
            if len(sach) < int(cfg.lop_cu_ly_diem_toi_thieu):
                continue

            ds = np.asarray([p[1] for p in sach], dtype=float)
            rm = float(np.median(ds))
            th = math.radians(goc)
            ux, uy = math.sin(th), math.cos(th)
            tx, ty = uy, -ux
            tiep = np.asarray([p[2] * tx + p[3] * ty for p in sach], dtype=float)
            rong_thay = float(np.ptp(tiep)) if len(tiep) >= 2 else 0.0
            n_du_kien = max(tr.so_diem_du_kien(dtheta_deg), len(sach), 1)
            ti_le_thay = min(1.0, len(sach) / max(n_du_kien, 1))
            che_mot_phan = (ti_le_thay < 0.72
                             or (rong_id > 0 and rong_thay < 0.60 * rong_id))

            if che_mot_phan:
                half_width = 0.5 * rong_id
                slack = max(2.0, rm * math.radians(dtheta_deg))
                low = float(tiep.max()) - half_width - slack
                high = float(tiep.min()) + half_width + slack
                offset = float(np.clip(0.0, low, high)) if low <= high else 0.0
                cx, cy = rm * ux + offset * tx, rm * uy + offset * ty
            else:
                cx = float(np.mean([p[2] for p in sach]))
                cy = float(np.mean([p[3] for p in sach]))

            moi = dict(o)
            cac_o = [p[4] for p in sach]
            moi.update({
                'bins': (min(cac_o), max(cac_o)),
                'n': max(1, len(set(cac_o))),
                'n_diem': len(sach),
                'cx': cx, 'cy': cy,
                'r': float(math.hypot(cx, cy)),
                'r_min': float(np.min(ds)),
                'theta': math.atan2(cy, cx),
                'width': max(rong_thay, 1.0),
                'width_observed': max(rong_thay, 0.0),
                'width_expected': max(rong_id, rong_thay, 1.0),
                'n_diem_du_kien': n_du_kien,
                'ty_le_thay': ti_le_thay,
                'che_mot_phan': che_mot_phan,
                'tu_lop_cu_ly': True,
                'layer_track_id': tr.id,
                'thua': True,
                '_layer_points': frozenset((round(p[0], 6), round(p[1], 6))
                                           for p in sach),
            })
            lop.append((rm, moi))

        if len(lop) < 2:
            ket_qua.append(o)
            continue
        lop.sort(key=lambda x: x[0])
        if max((b[0] - a[0] for a, b in zip(lop, lop[1:])), default=0.0) \
                < cfg.lop_cu_ly_cach_vet_toi_thieu_mm:
            ket_qua.append(o)
            continue
        ket_qua.extend(moi for _, moi in lop)
    return ket_qua


def gan_cuong_do_cho_cum(objs, intensity_points, grid, cfg):

    if (not getattr(cfg, 'cuong_do_id_bat', 0.0)
            or not objs or not intensity_points):
        return

    half = float(cfg.fov_half_deg)
    span = 2.0 * half
    nb = int(grid.nb)
    diem = []
    for p in intensity_points:
        if len(p) < 3:
            continue
        a, d, q = float(p[0]), float(p[1]), int(p[2])
        if (q <= 0 or q >= 255
                or d < cfg.cuong_do_r_min_mm
                or d > cfg.cuong_do_r_max_mm):
            continue
        rel = ((a * cfg.angle_sign - cfg.fov_center_deg + 180.0)
               % 360.0) - 180.0
        if abs(rel) > half:
            continue
        b = int((rel + half) / span * nb)
        b = min(max(b, 0), nb - 1)
        diem.append((b, d, math.log(float(q)) + 2.0 * math.log(d),
                     (round(rel, 6), round(d, 6))))

    if not diem:
        return
    for o in objs:
        b0, b1 = o.get('bins', (0, -1))
        rr = float(o.get('r', math.hypot(o['cx'], o['cy'])))
        rong = max(float(o.get('width_expected',
                               o.get('width', 0.0))), 1.0)
        if o.get('tu_lop_cu_ly', False):
            gate_r = max(15.0, min(35.0, 0.18 * rong + 10.0))
        else:
            gate_r = max(35.0, min(80.0, 0.40 * rong))
        members = o.get('_layer_points')
        vals = [lr for b, d, lr, key in diem
                if ((key in members) if members is not None
                    else (b0 <= b <= b1 and abs(d - rr) <= gate_r))]
        if len(vals) < int(cfg.cuong_do_mau_toi_thieu):
            continue
        aa = np.asarray(vals, dtype=float)
        med = float(np.median(aa))
        mad = 1.4826 * float(np.median(np.abs(aa - med)))
        o['cuong_do_log_rho'] = med
        o['cuong_do_log_mad'] = mad
        o['cuong_do_n'] = len(vals)


def hoc_be_mat_tinh(tracks, pts, grid, cfg, t):
    for tr in tracks:
        if not hasattr(tr, 'surface_history'):
            tr.surface_history = deque(maxlen=24)
            tr.surface_reference = None
        if getattr(tr, 'surface_hold', False):
            continue
        o = getattr(tr, 'surface_observation', None)
        if (tr.state != DYNAMIC or not tr.last_matched or o is None
                or tr.dang_che_mot_phan or tr.trong_cum_gop
                or o.get('tu_lop_cu_ly', False)):
            tr.surface_history.clear()
            continue
        ref = tr.surface_reference
        if ref is not None:
            departure = getattr(tr, 'surface_departure', deque(maxlen=2))
            if getattr(tr, 'surface_departure_ref', None) != ref['time']:
                departure.clear()
                tr.surface_departure_ref = ref['time']
            tr.surface_departure = departure
            px, py = tr.last_meas
            dx, dy = px-ref['center'][0], py-ref['center'][1]
            if (float(o.get('width', 0)) >= 0.85*ref['width']
                    and math.hypot(dx, dy) > 10.0):
                departure.append((t, px, py))
                if len(departure) == 2:
                    t0, x0, y0 = departure[0]
                    sx, sy = px-x0, py-y0
                    if (0 < t-t0 <= 0.5 and math.hypot(sx, sy) > 3.0
                            and sx*dx+sy*dy > 0):
                        tr.surface_reference = None
                        tr.surface_history.clear()
                        departure.clear()
                        continue
            else:
                departure.clear()
            lo,hi = ref['points'][0,0],ref['points'][-1,0]
            margin = 2.0*grid.span/grid.nb
            approaching = False
            for other in tracks:
                if other is tr or other.state != DYNAMIC or t-other.t_seen>0.8:
                    continue
                x,y=other.last_meas
                r=math.hypot(x,y)
                a=math.degrees(math.atan2(x,y))
                h=math.degrees(math.atan2(0.5*other.hud_width,max(r,1)))
                if r<math.hypot(*ref['center'])-25 and min(hi,a+h+margin)>max(lo,a-h-margin):
                    approaching=True
                    break
            if approaching:
                continue
        tr.surface_history.append((t, *tr.last_meas))
        h = np.asarray(tr.surface_history)
        if len(h) < 20 or h[-1, 0]-h[0, 0] < 2.0:
            continue
        center = np.median(h[:, 1:3], axis=0)
        if np.max(np.linalg.norm(h[:, 1:3]-center, axis=1)) > 10.0:
            tr.surface_reference = None
            continue
        b0, b1 = o['bins']
        selected = [p for p in pts if b0 <= int((p[0]+cfg.fov_half_deg)/grid.span*grid.nb) <= b1]
        if len(selected) < 6:
            continue
        lo, hi = selected[0][0], selected[-1][0]
        overlap = False
        for other in tracks:
            if other is tr or other.state != DYNAMIC or not other.last_matched:
                continue
            x, y = other.last_meas
            r = math.hypot(x, y)
            angle = math.degrees(math.atan2(x, y))
            half = math.degrees(math.atan2(0.5*other.hud_width, max(r, 1)))
            if min(hi, angle+half)-max(lo, angle-half) > 0:
                overlap = True
        if not overlap:
            tr.surface_reference = dict(points=np.asarray(selected), center=tuple(center),
                width=float(o['width']), time=t)
            seed = tr.be_rong_id_uoc
            samples = getattr(tr, 'width_relearn_samples', deque(maxlen=8))
            tr.width_relearn_samples = samples
            eligible = (getattr(tr, 'width_seed_clipped', False)
                        and 0 < seed < 60.0 and o['width'] > 2.5*seed
                        and b0 > 1 and b1 < grid.nb-2)
            if eligible:
                if samples and t-samples[-1][0] > 0.3:
                    samples.clear()
                samples.append((t, float(o['width'])))
                widths = [w for _, w in samples]
                if (len(samples) == 8 and t-samples[0][0] >= 0.7
                        and max(widths) <= 1.2*min(widths)):
                    tr.lich_rong_id.clear()
                    tr.lich_rong_id.extend(widths)
                    tr.width_seed_clipped = False
                    samples.clear()
            else:
                samples.clear()


def phan_be_mat_bi_che(objs, pts, tracks, grid, cfg, t, dt):

    def key(p):
        return (round(p[0], 6), round(p[1], 6))
    def bin_of(p):
        return min(grid.nb-1, max(0, int((p[0]+cfg.fov_half_deg)/grid.span*grid.nb)))
    def observation(group, old=None):
        a = np.asarray(group)
        w = 1.0 / np.maximum(a[:, 1]-a[:, 1].min()+20.0, 1.0)**2
        x, y = (a[:, 2:4]*w[:, None]).sum(axis=0)/w.sum()
        bins = [bin_of(p) for p in group]
        return dict(old or {}, cx=float(x), cy=float(y), r=math.hypot(x,y),
            r_min=float(a[:, 1].min()), theta=math.atan2(y,x),
            width=float(np.linalg.norm(np.ptp(a[:, 2:4],axis=0))),
            bins=(min(bins),max(bins)), n=len(set(bins)), n_diem=len(group),
            _layer_points=frozenset(key(p) for p in group))
    active = []
    for tr in tracks:
        was_hold = getattr(tr, 'surface_hold', False)
        tr.surface_hold = False
        ref = getattr(tr, 'surface_reference', None)
        if tr.state != DYNAMIC or ref is None or not pts:
            continue
        template = ref['points']
        lo, hi = template[0,0], template[-1,0]
        center = ref['center']
        near_tracks = []
        merged_peers = []
        for other in tracks:
            if other is tr or other.state != DYNAMIC or t-other.t_seen > 0.8:
                continue
            x,y = other.pos
            r = math.hypot(x,y)
            angle = math.degrees(math.atan2(x,y))
            half = math.degrees(math.atan2(0.5*other.hud_width,max(r,1)))
            margin=2.0*grid.span/grid.nb
            if r < math.hypot(*center)-25 and min(hi,angle+half+margin)-max(lo,angle-half-margin) > 0:
                near_tracks.append(other)
            center_angle = math.degrees(math.atan2(*center))
            ca = int((center_angle+cfg.fov_half_deg)/grid.span*grid.nb)
            cb = int((angle+cfg.fov_half_deg)/grid.span*grid.nb)
            if any(o.get('layer_track_id') is None
                   and o.get('width', 0) > 1.5*ref['width']
                   and o['bins'][0] <= min(ca, cb)
                   and o['bins'][1] >= max(ca, cb)
                   and math.hypot(o['cx']-x, o['cy']-y) < o['width']/2+cfg.diff_mm
                   for o in objs):
                merged_peers.append(other)
        near_tracks = list({other.id: other for other in near_tracks+merged_peers}.values())
        if not near_tracks:
            continue
        covered = [p for p in pts if lo <= p[0] <= hi]
        predicted = np.interp([p[0] for p in covered],template[:,0],template[:,1])
        front = [p for p,r in zip(covered,predicted) if p[1]<r-25.0]
        visible = [p for p,r in zip(covered,predicted) if abs(p[1]-r)<=12.0]
        candidates = []
        if len(visible) < max(3, 0.2*len(template)):
            for o in objs:
                ow = float(o.get('width', 0))
                distance = math.hypot(o['cx']-center[0], o['cy']-center[1])
                rr = math.hypot(o['cx'], o['cy'])
                if (o.get('layer_track_id') not in (None, tr.id)
                        or o.get('n_diem', 0) < 6
                        or not max(35.0, 0.3*ref['width']) <= ow <= 1.35*ref['width']
                        or not max(20.0, 0.15*ref['width']) < distance < 0.95*ref['width']
                        or abs(rr-math.hypot(*center)) > 0.5*ref['width']):
                    continue
                if any(rr-math.hypot(*other.last_meas)
                       < max(50.0, 0.5*other.hud_width) for other in near_tracks):
                    continue
                if any(other is not tr and other.state == DYNAMIC
                       and other not in near_tracks and t-other.t_seen < 0.5
                       and math.hypot(o['cx']-other.last_meas[0],
                                      o['cy']-other.last_meas[1]) < 80.0
                       for other in tracks):
                    continue
                candidates.append(o)
        pending = getattr(tr, 'rear_departure', deque(maxlen=3))
        tr.rear_departure = pending
        if getattr(tr, 'rear_departure_ref', None) != ref['time']:
            pending.clear()
            tr.rear_departure_ref = ref['time']
        if len(candidates) == 1:
            o = candidates[0]
            if pending and (t-pending[-1][0] > 0.3 or
                    math.hypot(o['cx']-pending[-1][1],o['cy']-pending[-1][2]) > 40.0):
                pending.clear()
            pending.append((t, o['cx'], o['cy']))
            if len(pending) == 3:
                _, x0, y0 = pending[0]
                _, x1, y1 = pending[1]
                dx, dy = o['cx']-x0, o['cy']-y0
                coherent = (math.hypot(dx,dy)>5.0 and
                    (x1-x0)*(o['cx']-x1)+(y1-y0)*(o['cy']-y1)>0.0)
                if coherent:
                    o.update(layer_track_id=tr.id, thua=True, che_mot_phan=True,
                             width_expected=ref['width'], partial_surface_motion=True)
                    tr.surface_reference = None
                    tr.surface_history.clear()
                    pending.clear()
                    tr.rear_reacquired = True
                    continue
            if len(pending) < 3:
                o['thua'] = True
        else:
            pending.clear()
        displaced = [p for p,r in zip(covered,predicted)
            if (12.0<p[1]-r<90.0 or
                (-90.0<p[1]-r<-12.0 and all(
                    abs(p[1]-math.hypot(*other.pos)) > max(30.0,0.5*other.hud_width)
                    for other in near_tracks)))]
        edge_slack = 2.0*float(np.median(np.diff(template[:,0])))
        edges_seen = (visible and visible[0][0] <= lo+edge_slack
                      and visible[-1][0] >= hi-edge_slack)
        measured_merge = (bool(merged_peers) and edges_seen
                          and len(visible)>=max(6,0.6*len(template)))
        if ((len(front)<2 and not measured_merge)
                or len(displaced)>=max(3,len(visible))):
            continue
        if not visible and len(front)<max(3,0.35*len(template)):
            continue
        tr.surface_hold = True
        if not was_hold:
            tr.surface_saved_hud = tuple(tr.vi_tri_hud)
        tr.x[:2] = center
        tr.x[2:] = 0.0
        active.append((tr, ref, visible, near_tracks))
    if not active:
        return objs
    result = list(objs)
    for tr,ref,visible,near_tracks in active:
        owned = frozenset(key(p) for p in visible)
        rebuilt = []
        for o in result:
            if o.get('layer_track_id') == tr.id:
                continue
            lo,hi = o['bins']
            membership = o.get('_layer_points')
            members = [p for p in pts if (key(p) in membership if membership is not None
                        else lo <= bin_of(p) <= hi)]
            rest = [p for p in members if key(p) not in owned]
            if not rest:
                continue
            changed = len(rest)!=len(members)
            new = observation(rest,o) if changed else dict(o)
            new['_surface_exclude'] = set(o.get('_surface_exclude',())) | {tr.id}
            if new.get('layer_track_id') is None:
                candidates = sorted((min(math.hypot(new['cx']-x,new['cy']-y)
                    for x,y in (other.pos,other.last_meas)),other.id) for other in near_tracks)
                if (candidates and candidates[0][0] < 140.0
                        and (len(candidates)==1 or candidates[1][0]-candidates[0][0]>30.0)):
                    new['layer_track_id']=candidates[0][1]
                    new['thua']=True
            if changed and len(rest)<3:
                new['thua']=True
            rebuilt.append(new)
        if len(visible)>=2:
            a = observation(visible)
            x,y=ref['center']
            a.update(cx=x,cy=y,r=math.hypot(x,y),theta=math.atan2(y,x),
                layer_track_id=tr.id,thua=True,che_mot_phan=True,
                surface_stationary=True,width_expected=ref['width'],
                ev_bins=0,ev_thang={},ev_tho=0,g6_bins=0)
            rebuilt.append(a)
        result=rebuilt
    return result


def cuu_vat_nho_da_biet(objs, pts, tracks, grid, cfg, dtheta_deg, dt,
                       intensity_points=None):

    narrow = []
    for tr in tracks:
        width = tr.be_rong_id_uoc or tr.hud_width
        if (tr.state != DYNAMIC or not getattr(tr, 'narrow_confirmed', False)
                or not 3.0 <= width <= 60.0
                or any(o.get('layer_track_id') == tr.id for o in objs)):
            continue
        if any(o.get('width', 0) > max(60.0, 2.5*width)
               and math.hypot(o['cx']-tr.pos[0], o['cy']-tr.pos[1])
                   <= max(150.0, 1.5*o['width']) + 50.0 for o in objs):
            narrow.append((tr, width))
    if not narrow or not pts:
        return objs
    def bin_of(p):
        return min(grid.nb-1, max(0, int((p[0]+cfg.fov_half_deg)/grid.span*grid.nb)))
    def key(p):
        return (round(p[0], 6), round(p[1], 6))
    reserved = set()
    for o in objs:
        if o.get('layer_track_id') is not None:
            members = o.get('_layer_points')
            if members is not None:
                reserved.update(members)
            else:
                lo, hi = o['bins']
                reserved.update(key(p) for p in pts if lo <= bin_of(p) <= hi)
    groups = []
    for p in sorted(pts, key=lambda p: p[0]):
        if (not groups or p[0]-groups[-1][-1][0] > max(1.2, 1.8*dtheta_deg)
                or abs(p[1]-groups[-1][-1][1]) > 12.0):
            groups.append([])
        groups[-1].append(p)
    fragments = []
    for group in groups:
        if any(key(p) in reserved for p in group):
            continue
        if not 2 <= len(group) <= 8 or len({p[0] for p in group}) < 2:
            continue
        a = np.asarray(group, dtype=float)
        width = float(np.linalg.norm(np.ptp(a[:, 2:4], axis=0)))
        if np.ptp(a[:, 1]) > 25.0 or not 2.0 <= width <= 65.0:
            continue
        cx, cy = np.mean(a[:, 2:4], axis=0)
        bins = [bin_of(p) for p in group]
        fragments.append(dict(cx=float(cx), cy=float(cy), width=width,
            r=float(math.hypot(cx, cy)), r_min=float(a[:, 1].min()),
            theta=math.atan2(cy, cx), n=len(set(bins)), n_diem=len(group),
            bins=(min(bins), max(bins)), thua=True,
            ev_bins=0, ev_thang={}, ev_tho=0, g6_bins=0,
            _layer_points=frozenset(key(p) for p in group)))
    gan_cuong_do_cho_cum(fragments, intensity_points, grid, cfg)
    proposals = []
    for i, (tr, expected) in enumerate(narrow):
        gate = min(160.0, max(70.0, 3.0*tr.speed*dt))
        for j, o in enumerate(fragments):
            distance = math.hypot(o['cx']-tr.pos[0], o['cy']-tr.pos[1])
            if (distance > gate or o['width'] > 1.8*expected+4.0
                    or o['width'] < 0.25*expected):
                continue
            nis = tr.nis_cho_do(o, cfg, dtheta_deg)
            if not math.isfinite(nis) or nis > max(30.0, cfg.ghep_nis_nguong):
                continue
            power_penalty = 0.0
            rho = o.get('cuong_do_log_rho')
            if tr.cuong_do_id_uoc is not None and rho is not None:
                sigma = math.hypot(tr.sigma_cuong_do_id(cfg),
                    max(cfg.cuong_do_sigma_do_log, o.get('cuong_do_log_mad', 0.0)))
                z = abs(rho-tr.cuong_do_id_uoc) / max(sigma, 1e-6)
                power_penalty = 20.0*min(z*z, 9.0)
            score = (distance + 3.0*min(nis, 20.0)
                     + 20.0*abs(math.log(o['width']/expected)) + power_penalty)
            proposals.append((score, i, j))
    used_tracks, used_groups, claimed, recovered = set(), set(), set(), []
    for score, i, j in sorted(proposals):
        if i in used_tracks or j in used_groups:
            continue
        row = sorted(s for s, ii, jj in proposals if ii == i)
        col = sorted(s for s, ii, jj in proposals if jj == j)
        if (score != row[0] or score != col[0]
                or (len(row) > 1 and row[1]-row[0] < 12.0)
                or (len(col) > 1 and col[1]-col[0] < 12.0)):
            continue
        tr, expected = narrow[i]
        o = dict(fragments[j])
        o.update(layer_track_id=tr.id, known_narrow_recovery=True,
                 vat_nho=True, vat_nho_rieng=True,
                 che_mot_phan=(o['n_diem'] < 3 or o['width'] < 0.55*expected),
                 width_expected=expected, n_diem_du_kien=tr.so_diem_du_kien(dtheta_deg))
        recovered.append(o)
        claimed.update(o['_layer_points'])
        used_tracks.add(i)
        used_groups.add(j)
    if not recovered:
        return objs
    result = []
    for o in objs:
        if o.get('layer_track_id') is not None:
            result.append(o)
            continue
        lo, hi = o['bins']
        old_members = o.get('_layer_points')
        members = [p for p in pts if (key(p) in old_members
                   if old_members is not None else lo <= bin_of(p) <= hi)]
        remainder = [p for p in members if key(p) not in claimed]
        if len(remainder) == len(members):
            result.append(o)
            continue
        if len(remainder) < 3:
            continue
        a = np.asarray(remainder, dtype=float)
        w = 1.0 / np.maximum(a[:, 1]-a[:, 1].min()+20.0, 1.0)**2
        cx, cy = (a[:, 2:4]*w[:, None]).sum(axis=0)/w.sum()
        width = float(np.linalg.norm(np.ptp(a[:, 2:4], axis=0)))
        b = [bin_of(p) for p in remainder]
        partial = width < 0.6*float(o['width']) or len(remainder) < 0.5*len(members)
        result.append(dict(o, cx=float(cx), cy=float(cy), r=math.hypot(cx, cy),
            r_min=float(a[:, 1].min()), theta=math.atan2(cy, cx),
            n=len(set(b)), n_diem=len(remainder), bins=(min(b), max(b)),
            width=width, width_expected=o['width'], che_mot_phan=partial,
            _layer_points=frozenset(key(p) for p in remainder)))
    return result + recovered


def bao_ve_vet_tai_vao(objs, tracks, cfg, t, dt):

    stale = [tr for tr in tracks if tr.state == DYNAMIC
             and t-tr.t_seen > cfg.cuong_do_reid_mat_toi_da_s
             and not getattr(tr, 'surface_hold', False)]
    if not stale:
        return
    recent = [tr for tr in tracks if tr.state == DYNAMIC
              and tr.n_updates >= 3 and tr.last_matched
              and t-tr.t_seen <= max(0.4, 2.5*dt)
              and not tr.dang_che_mot_phan
              and not (getattr(tr, 'surface_observation', None) or {}).get('che_mot_phan', False)]
    for o in objs:
        if o.get('che_mot_phan', False) or o.get('thua', False):
            continue
        owners = []
        for tr in recent:
            if (tr.id in o.get('_surface_exclude', ())
                    or o.get('layer_track_id', tr.id) != tr.id):
                continue
            d = math.hypot(o['cx']-tr.pos[0], o['cy']-tr.pos[1])
            gate = max(cfg.gate_base_mm + cfg.gate_vel_gain*tr.speed*dt,
                       0.35*cfg.max_speed_mm_s*dt)
            if d <= gate:
                owners.append(tr)
        if len(owners) != 1:
            continue
        owner = owners[0]
        excluded = set(o.get('_surface_exclude', ()))
        for tr in stale:
            if (owner.t_created <= tr.t_seen
                    or owner.id in tr.id_tach_rieng
                    or tr.id in owner.id_tach_rieng):
                continue
            excluded.add(tr.id)
        if excluded:
            o['_surface_exclude'] = frozenset(excluded)


def danh_dau_bi_che(tracks, objs, cfg):

    if not tracks:
        return
    truoc = []
    for o in objs:
        th, na, r = _huong_va_nua_goc(o['cx'], o['cy'],
                                      float(o.get('width', 0.0)))
        truoc.append((th, na, r, o.get('_surface_exclude', ())))
    for tr in tracks:
        px, py = tr.pos
        th_i, na_i, r_i = _huong_va_nua_goc(px, py, float(tr.hud_width))
        che = False
        for th_c, na_c, r_c, excluded in truoc:
            if tr.id in excluded:
                continue
            if r_c >= r_i - cfg.che_sau_mm:
                continue
            lech = abs(((th_c - th_i + 180.0) % 360.0) - 180.0)
            if lech <= na_c + na_i + cfg.che_le_goc_deg:
                che = True
                break
        tr.bi_che = che


def ghep(tracks, objs, cfg, dt, dtheta_deg):
    if not tracks or not objs:
        return {}, set(range(len(objs)))
    BIG = 1e9
    cost = np.full((len(tracks), len(objs)), BIG)
    base_cost = np.full((len(tracks), len(objs)), BIG)
    profiles = [(tr.be_rong_id_uoc, tr.sigma_be_rong_id(cfg)) for tr in tracks]
    rong_phan_biet_duoc = any(
        (math.isfinite(sa) and math.isfinite(sb)
         and abs(a - b) >= cfg.ghep_rong_tach_sigma * math.hypot(sa, sb))
        for k, (a, sa) in enumerate(profiles)
        for b, sb in profiles[k + 1:])
    power_profiles = [(tr.cuong_do_id_uoc,
                       tr.sigma_cuong_do_id(cfg)) for tr in tracks]
    power_phan_biet_duoc = any(
        (a is not None and b is not None
         and math.isfinite(sa) and math.isfinite(sb)
         and abs(a - b) >= cfg.ghep_cuong_do_tach_sigma
             * math.hypot(sa, sb))
        for k, (a, sa) in enumerate(power_profiles)
        for b, sb in power_profiles[k + 1:])
    for i, tr in enumerate(tracks):
        px, py = tr.pos
        gate = cfg.gate_base_mm + cfg.gate_vel_gain * tr.speed * dt
        if tr.n_updates < 3:
            gate = max(gate, cfg.max_speed_mm_s * dt)
        else:
            gate = max(gate, 0.35 * cfg.max_speed_mm_s * dt)
        if getattr(tr, 'so_vong_che', 0) > 0:
            gate *= cfg.che_he_so_cong
        rong_i = tr.be_rong_uoc
        for j, o in enumerate(objs):
            if tr.id in o.get('_surface_exclude', ()):
                continue
            goi_y_id = o.get('layer_track_id')
            if goi_y_id is not None and int(goi_y_id) != int(tr.id):
                continue
            dx, dy = o['cx'] - px, o['cy'] - py
            d = math.hypot(dx, dy)
            if d > gate:
                continue

            gia = d
            base_cost[i, j] = d
            if getattr(cfg, 'ghep_dung_nis', False):
                nis = tr.nis_cho_do(o, cfg, dtheta_deg)
                nis_gate = cfg.ghep_nis_nguong
                if getattr(tr, 'so_vong_che', 0) > 0:
                    nis_gate *= cfg.ghep_nis_he_so_che
                if nis > nis_gate:
                    continue
                gia += cfg.ghep_nis_trong_so_mm * min(nis, nis_gate)

            if (getattr(tr, 'so_vong_che', 0) > 0
                    and tr.speed >= cfg.ghep_huong_toc_min):
                mx = float(o['cx']) - float(tr.last_meas[0])
                my = float(o['cy']) - float(tr.last_meas[1])
                md = math.hypot(mx, my)
                if md >= cfg.diff_mm:
                    cos_huong = (mx * tr.x[2] + my * tr.x[3]) / (md * tr.speed)
                    if cos_huong < 0.0:
                        gia += cfg.ghep_huong_phat * cos_huong * cos_huong

            rong_j = float(o.get('width', 0.0))
            phat = 0.0
            he_so_rong = cfg.ghep_he_so_rong
            if getattr(tr, 'so_vong_che', 0) > 0:
                he_so_rong = max(he_so_rong,
                                  cfg.ghep_he_so_rong_sau_che)
            if he_so_rong > 0 and rong_i > 0 and rong_j > 0:
                phat = min(he_so_rong * abs(rong_j - rong_i),
                           cfg.ghep_phat_rong_toi_da)
            if (rong_phan_biet_duoc and rong_j > 0
                    and not o.get('che_mot_phan', False)):
                mu_rong, sig_rong = profiles[i]
                if mu_rong > 0 and math.isfinite(sig_rong):
                    sig_do = max(cfg.rong_id_sigma_san_mm,
                                 cfg.rong_id_sigma_ty_le * rong_j)
                    z2 = ((rong_j - mu_rong) ** 2
                          / max(sig_rong ** 2 + sig_do ** 2, 1e-9))
                    phat += min(cfg.ghep_rong_nll_mm * z2,
                                cfg.ghep_rong_nll_toi_da_mm)
            lr_j = o.get('cuong_do_log_rho')
            mu_p, sig_p = power_profiles[i]
            if (power_phan_biet_duoc and mu_p is not None
                    and lr_j is not None
                    and int(o.get('cuong_do_n', 0))
                        >= int(cfg.cuong_do_mau_toi_thieu)
                    and not o.get('che_mot_phan', False)):
                sig_do = max(float(cfg.cuong_do_sigma_do_log),
                             float(o.get('cuong_do_log_mad', 0.0)))
                z2p = ((float(lr_j) - float(mu_p)) ** 2
                       / max(sig_p ** 2 + sig_do ** 2, 1e-9))
                phat += min(cfg.ghep_cuong_do_nll_mm * z2p,
                            cfg.ghep_cuong_do_nll_toi_da_mm)
            base_cost[i, j] += phat
            cost[i, j] = gia + phat

    if (getattr(cfg, 'ghep_dung_nis', False)
            and getattr(cfg, 'ghep_nis_chi_khi_mo_ho', False)):
        hop_le = base_cost < BIG
        so_cum_moi_vet = np.sum(hop_le, axis=1)
        so_vet_moi_cum = np.sum(hop_le, axis=0)
        for i in range(len(tracks)):
            for j in range(len(objs)):
                if not hop_le[i, j]:
                    continue
                mo_ho = (so_cum_moi_vet[i] >= 2
                         and so_vet_moi_cum[j] >= 2)
                if not mo_ho:
                    cost[i, j] = base_cost[i, j]
    pairs = {}
    newest = max((tr.t_seen for tr in tracks), default=0.0)
    for i, tr in enumerate(tracks):
        if tr.state != DYNAMIC or tr.n_updates < 12 or newest-tr.t_seen > 0.4:
            continue
        ranked = sorted((math.hypot(o['cx']-tr.last_meas[0],
                                    o['cy']-tr.last_meas[1]), j)
                        for j,o in enumerate(objs) if cost[i,j] < BIG
                        and o.get('layer_track_id') is None)
        if not ranked or ranked[0][0] > 30.0:
            continue
        distance,j = ranked[0]
        if len(ranked)>1 and ranked[1][0] < distance+60.0:
            continue
        o=objs[j]
        rear_context = any(k != i and other.state == DYNAMIC
            and getattr(other,'rear_reacquired',False)
            and newest-other.t_seen < 2.0
            and math.hypot(*other.last_meas) > math.hypot(*tr.last_meas)+60.0
            and math.hypot(o['cx']-other.last_meas[0],
                           o['cy']-other.last_meas[1]) > 80.0
            for k,other in enumerate(tracks))
        if not rear_context:
            continue
        for k in range(len(tracks)):
            if k != i:
                cost[k,j] = base_cost[k,j] = BIG
        for jj in range(len(objs)):
            if jj != j:
                cost[i,jj] = base_cost[i,jj] = BIG
    if HAVE_SCIPY:
        ri, ci = linear_sum_assignment(cost)
        for i, j in zip(ri, ci):
            if cost[i, j] < BIG:
                pairs[i] = j
    else:
        order = sorted((cost[i, j], i, j)
                       for i in range(len(tracks)) for j in range(len(objs))
                       if cost[i, j] < BIG)
        ut, uo = set(), set()
        for _, i, j in order:
            if i in ut or j in uo:
                continue
            pairs[i] = j
            ut.add(i)
            uo.add(j)
    cuu_danh_tinh_sau_che(tracks, objs, pairs, cfg)
    chua_ghep = set(range(len(objs))) - set(pairs.values())

    chua_vet = [i for i in range(len(tracks)) if i not in pairs]
    if len(chua_vet) == 1 and len(chua_ghep) == 1:
        i = chua_vet[0]
        j = next(iter(chua_ghep))
        tr = tracks[i]
        px, py = tr.pos
        ban_kinh_cuu = min(max(cfg.cuu_vot_min_mm,
                               cfg.cuu_vot_he_so * tr.speed * dt),
                           cfg.max_speed_mm_s * dt)
        if (objs[j].get('layer_track_id', tr.id) == tr.id
                and objs[j].get('ev_bins', 0) > 0
                and math.hypot(objs[j]['cx'] - px, objs[j]['cy'] - py) <= ban_kinh_cuu):
            pairs[i] = j
            chua_ghep.discard(j)

    if getattr(cfg, 'cuong_do_id_bat', 0.0) >= 0.5 and chua_ghep:
        vet_cd = [
            i for i, tr in enumerate(tracks)
            if (i not in pairs and tr.state == DYNAMIC
                and tr.cuong_do_id_uoc is not None
                and tr.misses * dt <= cfg.cuong_do_reid_mat_toi_da_s)
        ]
        BIG_CD = 1e9
        cd_cost = np.full((len(vet_cd), len(chua_ghep)), BIG_CD)
        cum_cd = sorted(chua_ghep)
        for ii, i in enumerate(vet_cd):
            tr = tracks[i]
            mu = float(tr.cuong_do_id_uoc)
            sig = tr.sigma_cuong_do_id(cfg)
            mat_s = max(float(tr.misses) * dt, dt)
            gate = max(1.7 * cfg.gate_base_mm,
                       1.25 * tr.speed * min(mat_s, 1.0))
            gate = min(float(cfg.cuong_do_reid_gate_mm), gate,
                       0.55 * cfg.max_range_mm)
            refs = [tr.pos, tr.last_meas, tr.vi_tri_hud, tr.vi_tri_ve]
            for jj, j in enumerate(cum_cd):
                o = objs[j]
                goi_y_id = o.get('layer_track_id')
                if goi_y_id is not None and int(goi_y_id) != int(tr.id):
                    continue
                lr = o.get('cuong_do_log_rho')
                if (lr is None or int(o.get('cuong_do_n', 0))
                        < int(cfg.cuong_do_mau_toi_thieu)
                        or o.get('che_mot_phan', False)
                        or o.get('ev_bins', 0) <= 0):
                    continue
                sig_do = max(float(cfg.cuong_do_sigma_do_log),
                             float(o.get('cuong_do_log_mad', 0.0)))
                z = abs(float(lr) - mu) / max(
                    math.hypot(sig, sig_do), 1e-9)
                if z > cfg.cuong_do_reid_z_toi_da:
                    continue
                d = min(math.hypot(float(o['cx']) - float(px),
                                   float(o['cy']) - float(py))
                        for px, py in refs)
                if d > gate:
                    continue
                phat_rong = 0.0
                mu_r = tr.be_rong_id_uoc
                if mu_r > 0 and float(o.get('width', 0.0)) > 0:
                    phat_rong = 0.15 * abs(float(o['width']) - mu_r)
                cd_cost[ii, jj] = d + 70.0 * z + phat_rong

        if len(vet_cd) and len(cum_cd):
            if HAVE_SCIPY:
                rr, cc = linear_sum_assignment(cd_cost)
                de_xuat = list(zip(rr, cc))
            else:
                de_xuat = []
                da_r, da_c = set(), set()
                for _, ii, jj in sorted(
                        (cd_cost[ii, jj], ii, jj)
                        for ii in range(len(vet_cd))
                        for jj in range(len(cum_cd))
                        if cd_cost[ii, jj] < BIG_CD):
                    if ii not in da_r and jj not in da_c:
                        de_xuat.append((ii, jj))
                        da_r.add(ii)
                        da_c.add(jj)

            for ii, jj in de_xuat:
                gia = cd_cost[ii, jj]
                if gia >= BIG_CD:
                    continue
                hang = sorted(x for x in cd_cost[ii, :] if x < BIG_CD)
                cot = sorted(x for x in cd_cost[:, jj] if x < BIG_CD)
                le = float(cfg.cuong_do_reid_margin_mm)
                if ((len(hang) > 1 and hang[1] - hang[0] < le)
                        or (len(cot) > 1 and cot[1] - cot[0] < le)):
                    continue
                i, j = vet_cd[ii], cum_cd[jj]
                if i in pairs or j not in chua_ghep:
                    continue
                pairs[i] = j
                chua_ghep.discard(j)
                objs[j]['reid_cuong_do'] = True
    for i,j in list(pairs.items()):
        if tracks[i].id in objs[j].get('_surface_exclude', ()):
            pairs.pop(i)
            chua_ghep.add(j)
    return pairs, chua_ghep


def cuu_danh_tinh_sau_che(tracks, objs, pairs, cfg):
    if getattr(cfg,'cuong_do_id_bat',0.0) < 0.5:
        return
    newest=max((tr.t_seen for tr in tracks),default=0.0)
    for young_index,j in list(pairs.items()):
        young=tracks[young_index]
        o=objs[j]
        lr=o.get('cuong_do_log_rho')
        if (young.state == DYNAMIC or newest-young.t_created > 3.5
                or o.get('layer_track_id') is not None or lr is None
                or o.get('n_diem',0) < 6
                or o.get('cuong_do_n',0) < cfg.cuong_do_mau_toi_thieu):
            continue
        rr=math.hypot(o['cx'],o['cy'])
        choices=[]
        for i,tr in enumerate(tracks):
            if (i in pairs or tr.state != DYNAMIC
                    or not getattr(tr,'rear_reacquired',False)
                    or newest-tr.t_seen > cfg.cuong_do_reid_mat_toi_da_s
                    or tr.id in o.get('_surface_exclude',())
                    or tr.cuong_do_id_uoc is None):
                continue
            if (abs(rr-math.hypot(*tr.last_meas)) > 90.0
                    or math.hypot(o['cx']-tr.last_meas[0],o['cy']-tr.last_meas[1])
                        > cfg.cuong_do_reid_gate_mm
                    or o.get('width',0) > 1.35*tr.be_rong_id_uoc):
                continue
            sig=math.hypot(tr.sigma_cuong_do_id(cfg),
                max(cfg.cuong_do_sigma_do_log,o.get('cuong_do_log_mad',0.0)))
            if abs(lr-tr.cuong_do_id_uoc) > 1.5*sig:
                continue
            if not any(k not in (i,young_index) and peer.state == DYNAMIC
                and newest-peer.t_seen < 0.4
                and math.hypot(*peer.last_meas)+80.0 < min(rr,math.hypot(*tr.last_meas))
                for k,peer in enumerate(tracks)):
                continue
            choices.append((i,tr))
        if len(choices)!=1:
            continue
        i,tr=choices[0]
        vote=getattr(tr,'rear_reid_vote',None)
        tr.rear_reid_vote=(young.id,newest,o['cx'],o['cy'])
        if (vote is not None and vote[0]==young.id and 0 < newest-vote[1] <= 0.3
                and math.hypot(o['cx']-vote[2],o['cy']-vote[3]) < 80.0):
            pairs.pop(young_index,None)
            pairs[i]=j
            if o.get('width',0)<0.8*tr.be_rong_id_uoc:
                o.update(che_mot_phan=True,width_expected=tr.be_rong_id_uoc,
                         partial_surface_motion=True)
            tr.rear_reid_vote=None


class Detector:

    def __init__(self, cfg):
        self.cfg = cfg
        self.grid = BinGrid(cfg)
        self.bg = Background(cfg, self.grid.nb)
        self.ev = MotionEvidence(cfg, self.grid.nb)
        self.neo = NeoOGoc(cfg, self.grid.nb)
        self.tracks = []
        self.identity_gallery = {}
        self.narrow_candidates = []
        self.t_prev = None
        self.dt_hist = deque(maxlen=15)
        self.n_pts_hist = deque(maxlen=60)
        self.dtheta_deg = 0.72
        self.canh_bao = None
        self.gan_hist = deque(maxlen=30)
        self.phu_hist = deque(maxlen=30)
        self.mask_mu = None                                                 
        self.n_fov_hist = deque(maxlen=30)
        self.da_chinh_luoi = False
        self.thong_bao_luoi = None
        self.cung_bi_chan = None                                                
        self.sensor_moved = False
        self.sensor_guard = False
        self.so_vong_nghi_xe_dich = 0
        self.pose_ref_points = None
        self.pose_ref_tree = None
        self.pose_last = None

    def _chinh_luoi(self):



        if self.da_chinh_luoi or len(self.n_fov_hist) < 15:
            return
        diem_truoc_mat = float(np.median(self.n_fov_hist))
        nb = int(round(diem_truoc_mat / 2.0))
        nb = max(48, min(200, nb))
        self.da_chinh_luoi = True
        if abs(nb - self.grid.nb) <= 8:
            return

        ty = nb / float(self.cfg.n_bins)                                     
        cfg = self.cfg
        cfg.n_bins = nb
        cfg.diff_min_run = max(3, int(round(cfg.diff_min_run * ty)))
        cfg.evidence_min_bins = max(2, int(round(cfg.evidence_min_bins * ty)))
        cfg.strong_ev_bins = max(3, int(round(cfg.strong_ev_bins * ty)))
        cfg.gap_bins = max(3, int(round(cfg.gap_bins * ty)))
        cfg.min_object_bins = max(3, int(round(cfg.min_object_bins * ty)))

        self.grid = BinGrid(cfg)
        self.bg = Background(cfg, self.grid.nb)
        self.ev = MotionEvidence(cfg, self.grid.nb)
        self.neo = NeoOGoc(cfg, self.grid.nb)
        self.tracks = []
        self.identity_gallery = {}
        self.gan_hist.clear()
        self.phu_hist.clear()
        self.n_fov_hist.clear()
        self.mask_mu = None
        self.thong_bao_luoi = (f"lưới ô góc {nb} ô "
                               f"({2*cfg.fov_half_deg/nb:.2f}°/ô) theo "
                               f"{diem_truoc_mat:.0f} điểm trong vùng quét")

    def hoc_lai_nen(self):

        self.bg = Background(self.cfg, self.grid.nb)
        self.ev.reset()
        self.neo.reset()
        self.tracks = []
        self.narrow_candidates = []
        self.identity_gallery = {}
        self.sensor_moved = False
        self.sensor_guard = False
        self.so_vong_nghi_xe_dich = 0
        self.pose_ref_points = None
        self.pose_ref_tree = None
        self.pose_last = None

    def _luu_danh_tinh_an(self, tr, t):
        if (getattr(self.cfg, 'cuong_do_id_bat', 0.0) < 0.5
                or tr.state != DYNAMIC
                or tr.cuong_do_id_uoc is None):
            return
        self.identity_gallery[int(tr.id)] = {
            'id': int(tr.id),
            't': float(t),
            'cuong_do': list(tr.lich_cuong_do_id),
            'rong': list(tr.lich_rong_id),
            'ty_le_diem': list(tr.lich_ty_le_diem_id),
        }

    def _ghep_danh_tinh_an(self, objs, chua_ghep, t):
        cfg = self.cfg
        if getattr(cfg, 'cuong_do_id_bat', 0.0) < 0.5:
            return {}
        het = [i for i, g in self.identity_gallery.items()
               if t - float(g['t']) > cfg.cuong_do_gallery_s]
        for i in het:
            self.identity_gallery.pop(i, None)
        if not self.identity_gallery or not chua_ghep:
            return {}

        gallery = list(self.identity_gallery.values())
        js = sorted(chua_ghep)
        BIG = 1e9
        cost = np.full((len(gallery), len(js)), BIG)
        for i, g in enumerate(gallery):
            aa = np.asarray(g.get('cuong_do', []), dtype=float)
            if len(aa) < 6:
                continue
            mu = float(np.median(aa))
            mad = 1.4826 * float(np.median(np.abs(aa - mu)))
            sig = max(float(cfg.cuong_do_sigma_log_san), mad)
            rr = np.asarray(g.get('rong', []), dtype=float)
            mu_r = float(np.median(rr)) if len(rr) >= 6 else 0.0
            sig_r = max(float(cfg.rong_id_sigma_san_mm),
                        float(cfg.rong_id_sigma_ty_le) * max(mu_r, 1.0))
            for k, j in enumerate(js):
                o = objs[j]
                lr = o.get('cuong_do_log_rho')
                if (lr is None or int(o.get('cuong_do_n', 0))
                        < int(cfg.cuong_do_mau_toi_thieu)
                        or o.get('che_mot_phan', False)
                        or (o.get('ev_bins', 0) <= 0
                            and not o.get('_small_motion_verified', False))):
                    continue
                sig_do = max(float(cfg.cuong_do_sigma_do_log),
                             float(o.get('cuong_do_log_mad', 0.0)))
                z = abs(float(lr) - mu) / max(
                    math.hypot(sig, sig_do), 1e-9)
                if z > cfg.cuong_do_gallery_z_toi_da:
                    continue
                z_r = 0.0
                if mu_r > 0 and float(o.get('width', 0.0)) > 0:
                    z_r = abs(float(o['width']) - mu_r) / sig_r
                cost[i, k] = z + 0.15 * min(z_r, 4.0)

        if HAVE_SCIPY:
            ri, ci = linear_sum_assignment(cost)
            de_xuat = list(zip(ri, ci))
        else:
            de_xuat = []
            da_i, da_k = set(), set()
            for _, i, k in sorted(
                    (cost[i, k], i, k)
                    for i in range(len(gallery))
                    for k in range(len(js)) if cost[i, k] < BIG):
                if i not in da_i and k not in da_k:
                    de_xuat.append((i, k))
                    da_i.add(i)
                    da_k.add(k)

        out = {}
        for i, k in de_xuat:
            if cost[i, k] >= BIG:
                continue
            hang = sorted(x for x in cost[i, :] if x < BIG)
            cot = sorted(x for x in cost[:, k] if x < BIG)
            le = float(cfg.cuong_do_gallery_margin)
            if ((len(hang) > 1 and hang[1] - hang[0] < le)
                    or (len(cot) > 1 and cot[1] - cot[0] < le)):
                continue
            out[js[k]] = gallery[i]
        return out

    def _phuc_hoi_danh_tinh(self, tr, old, o, cfg):
        tr.id = int(old['id'])
        moi_cd = list(tr.lich_cuong_do_id)
        tr.lich_cuong_do_id.clear()
        tr.lich_cuong_do_id.extend(old.get('cuong_do', []))
        tr.lich_cuong_do_id.extend(moi_cd)
        moi_r = list(tr.lich_rong_id)
        tr.lich_rong_id.clear()
        tr.lich_rong_id.extend(old.get('rong', []))
        tr.lich_rong_id.extend(moi_r)
        moi_d = list(tr.lich_ty_le_diem_id)
        tr.lich_ty_le_diem_id.clear()
        tr.lich_ty_le_diem_id.extend(old.get('ty_le_diem', []))
        tr.lich_ty_le_diem_id.extend(moi_d)
        tr.tai_nhan_danh_cuong_do = True
        o['reid_gallery'] = True
        self.identity_gallery.pop(int(old['id']), None)

    def _diem_toan_canh(self, raw_points):
        pts, goc = [], []
        for a, d in raw_points or []:
            d = float(d)
            if d < self.cfg.min_range_mm or d > self.cfg.pose_guard_max_range_mm:
                continue
            q = math.radians(float(a))
            pts.append((d * math.sin(q), d * math.cos(q)))
            goc.append(float(a) % 360.0)
        if len(pts) < 50:
            return np.empty((0, 2)), np.empty(0)
        pts = np.asarray(pts, dtype=float)
        goc = np.asarray(goc, dtype=float)
        nmax = int(self.cfg.pose_guard_max_points)
        if len(pts) > nmax:
            lay = np.linspace(0, len(pts) - 1, nmax, dtype=int)
            pts, goc = pts[lay], goc[lay]
        return pts, goc

    @staticmethod
    def _khop_cung(src, dst):
        ca, cb = src.mean(axis=0), dst.mean(axis=0)
        u, _, vt = np.linalg.svd((src - ca).T @ (dst - cb))
        R = vt.T @ u.T
        if np.linalg.det(R) < 0:
            vt[-1] *= -1
            R = vt.T @ u.T
        return R, cb - ca @ R.T

    def _dat_moc_tu_the(self, raw_points):
        pts, _ = self._diem_toan_canh(raw_points)
        if HAVE_KDTREE and len(pts) >= 50:
            self.pose_ref_points = pts
            self.pose_ref_tree = cKDTree(pts)

    def _uoc_luong_tu_the(self, raw_points):

        if not HAVE_KDTREE or self.pose_ref_tree is None:
            return None
        src, goc = self._diem_toan_canh(raw_points)
        if len(src) < 50:
            return None
        tree = self.pose_ref_tree
        starts = []
        for deg in range(-40, 41, 5):
            a = math.radians(deg)
            R = np.array(((math.cos(a), -math.sin(a)),
                          (math.sin(a),  math.cos(a))))
            d, _ = tree.query(src @ R.T)
            n = max(32, int(0.65 * len(d)))
            starts.append((float(np.mean(np.sort(d)[:n])), R, np.zeros(2)))

        best = None
        for _, R, trans in sorted(starts, key=lambda z: z[0])[:4]:
            for _ in range(8):
                q = src @ R.T + trans
                d, j = tree.query(q)
                keep = np.argsort(d)[:max(40, int(0.70 * len(d)))]
                keep = keep[d[keep] < 500.0]
                if len(keep) < 40:
                    break
                Rn, tn = self._khop_cung(src[keep], self.pose_ref_points[j[keep]])
                if (np.max(np.abs(Rn - R)) < 1e-6
                        and np.linalg.norm(tn - trans) < 0.05):
                    R, trans = Rn, tn
                    break
                R, trans = Rn, tn
            d, _ = tree.query(src @ R.T + trans)
            n = max(32, int(0.65 * len(d)))
            score = float(np.mean(np.sort(d)[:n]))
            if best is None or score < best[0]:
                best = (score, R, trans, d)
        if best is None:
            return None

        score, R, trans, d = best
        d0, _ = tree.query(src)
        n = max(32, int(0.65 * len(d0)))
        score0 = float(np.mean(np.sort(d0)[:n]))
        rot = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        dich = float(np.linalg.norm(trans))
        inlier = d < self.cfg.pose_guard_inlier_mm
        so_vung = 0
        for lo in range(0, 360, 45):
            m = (goc >= lo) & (goc < lo + 45)
            if np.count_nonzero(m) >= 5 and np.mean(inlier[m]) >= 0.45:
                so_vung += 1
        ty_khop = float(np.mean(inlier))
        ty_diem = score / max(score0, 1e-6)
        da_doi = (ty_diem < self.cfg.pose_guard_score_ratio
                  and score < self.cfg.pose_guard_score_max_mm
                  and ty_khop >= self.cfg.pose_guard_inlier_ratio
                  and so_vung >= self.cfg.pose_guard_min_sectors
                  and (abs(rot) >= self.cfg.pose_guard_rot_deg
                       or dich >= self.cfg.pose_guard_trans_mm))
        return {'moved': bool(da_doi), 'rotation_deg': float(rot),
                'translation_mm': dich, 'score_mm': score,
                'improvement_ratio': ty_diem, 'inlier_ratio': ty_khop,
                'sectors': int(so_vung)}

    def _ket_qua_bao_ve_tu_the(self, dt, r, da_xac_nhan):
        self.sensor_guard = True
        self.narrow_candidates = []
        self.ev.reset()
        self.neo.reset()
        if da_xac_nhan:
            self.sensor_moved = True
            self.tracks = []
            canh_bao = 'THIẾT BỊ/NỀN ĐÃ XÊ DỊCH — BẤM HỌC LẠI NỀN'
        else:
            canh_bao = 'ĐANG KIỂM TRA THIẾT BỊ/NỀN — TẠM NGẮT BÁO VẬT ĐỘNG'
        self.canh_bao = canh_bao
        pose = self.pose_last or {}
        return {'dt': dt, 'r_bins': r,
                'fg': np.zeros(self.grid.nb, dtype=bool),
                'ev': np.zeros(self.grid.nb, dtype=bool),
                'objs': [], 'dtheta': self.dtheta_deg,
                'khop_nen': np.zeros(self.grid.nb, dtype=bool),
                'bg_ready': True, 'canh_bao': canh_bao,
                'sensor_guard': True, 'sensor_moved': bool(self.sensor_moved),
                'pose_rotation_deg': float(pose.get('rotation_deg', 0.0)),
                'pose_translation_mm': float(pose.get('translation_mm', 0.0))}

    def dt_smooth(self):
        return float(np.median(self.dt_hist)) if self.dt_hist else 1.0 / 6.0

    def do_phu_song(self, raw_points):



        cfg = self.cfg
        m = np.zeros(self.grid.nb, dtype=bool)
        dem = 0
        for a, d in raw_points:
            if d <= 20.0:
                continue
            rel = ((a * cfg.angle_sign - cfg.fov_center_deg + 180.0) % 360.0) - 180.0
            if abs(rel) > cfg.fov_half_deg:
                continue
            dem += 1
            b = int((rel + cfg.fov_half_deg) / (2 * cfg.fov_half_deg) * self.grid.nb)
            if 0 <= b < self.grid.nb:
                m[b] = True
        self.n_fov_hist.append(dem)
        return m

    def dem_qua_gan(self, raw_points):

        cfg = self.cfg
        m = np.zeros(self.grid.nb)
        for a, d in raw_points:
            if d <= 20.0 or d >= cfg.min_range_mm:
                continue
            rel = ((a * cfg.angle_sign - cfg.fov_center_deg + 180.0) % 360.0) - 180.0
            if abs(rel) > cfg.fov_half_deg:
                continue
            b = int((rel + cfg.fov_half_deg) / (2 * cfg.fov_half_deg) * self.grid.nb)
            if 0 <= b < self.grid.nb:
                m[b] += 1
        return m

    def step(self, t, pts, n_raw_points, raw_points=None,
             intensity_points=None):
        cfg = self.cfg
        self.cung_bi_chan = None
        if raw_points is not None:
            phu = self.do_phu_song(raw_points)
            self.gan_hist.append(self.dem_qua_gan(raw_points) > 0)
            self.phu_hist.append(phu)
        if raw_points is not None and cfg.bac_cau_vung_mu >= 0.5:
            if len(self.gan_hist) >= 20:
                ty_gan = np.mean(np.array(self.gan_hist), axis=0)
                ty_phu = np.mean(np.array(self.phu_hist), axis=0)
                bit = (ty_phu < 0.10) | (ty_gan > 0.60)
                rong_toi_da = max(6, int(self.grid.nb * 40.0 /
                                         (2 * cfg.fov_half_deg)))
                if np.mean(ty_phu > 0.5) > 0.5:
                    dai = _runs_at_least(bit, 3)
                    if np.count_nonzero(dai) > 0.25 * self.grid.nb:
                        dai = np.zeros_like(dai)
                    else:
                        i2, N2 = 0, len(dai)
                        while i2 < N2:
                            if dai[i2]:
                                j2 = i2
                                while j2 < N2 and dai[j2]:
                                    j2 += 1
                                if (j2 - i2) > rong_toi_da:
                                    dai[i2:j2] = False
                                i2 = j2
                            else:
                                i2 += 1
                    bi = np.flatnonzero(dai)
                    if bi.size >= 3:
                        self.cung_bi_chan = (self.grid.bin_angle(int(bi[0])),
                                             self.grid.bin_angle(int(bi[-1])))
                        self.mask_mu = dai
                    else:
                        self.mask_mu = None
        if self.t_prev is not None:
            d = t - self.t_prev
            if 0.02 < d < 1.0:
                self.dt_hist.append(d)
        self.t_prev = t
        dt = self.dt_smooth()

        if n_raw_points > 20:
            self.n_pts_hist.append(n_raw_points)
            self.dtheta_deg = 360.0 / max(float(np.median(self.n_pts_hist)), 1.0)
            self._chinh_luoi()

        r = self.grid.build(pts)

        if self.sensor_moved:
            return self._ket_qua_bao_ve_tu_the(dt, r, True)
        if self.bg.ready(t) and raw_points is not None and HAVE_KDTREE:
            if self.pose_ref_tree is None:
                self._dat_moc_tu_the(raw_points)
            else:
                self.pose_last = self._uoc_luong_tu_the(raw_points)
                if self.pose_last is not None and self.pose_last['moved']:
                    self.so_vong_nghi_xe_dich += 1
                    da_xac_nhan = (self.so_vong_nghi_xe_dich
                                   >= cfg.pose_guard_confirm_frames)
                    return self._ket_qua_bao_ve_tu_the(dt, r, da_xac_nhan)
                self.so_vong_nghi_xe_dich = 0
                self.sensor_guard = False

        loai_tru = self._mask_vet_dong()
        self.bg.push(t, r, loai_tru)
        self.bg.maybe_recompute(t)

        if not self.bg.ready(t):
            self.tracks = []
            fg = np.zeros(self.grid.nb, dtype=bool)
            self.ev.reset()                                                           
            return {'dt': dt, 'r_bins': r, 'fg': fg,
                    'ev': np.zeros(self.grid.nb, dtype=bool),
                    'objs': [], 'dtheta': self.dtheta_deg,
                    'bg_ready': False,
                    'sensor_guard': False, 'sensor_moved': False,
                    'canh_bao': (f'VÙNG MÙ '
                                 f'{self.cung_bi_chan[0]:+.0f}°..'
                                 f'{self.cung_bi_chan[1]:+.0f}° — CÓ VẬT CHE'
                                 if self.cung_bi_chan else 'ĐANG HỌC NỀN')}

        fg = self.bg.foreground(r)
        fg_hud = fg.copy()

        self.ev.push(r)
        ev_mask, ev_thang, ev_tho = self.ev.evidence(self.bg, self.mask_mu)

        o_nn = self.ev.mask_nn
        o_nn = o_nn & ~loai_tru
        if o_nn.any():
            fg = fg & ~o_nn

        tho_any = np.zeros(self.grid.nb, dtype=bool)
        for m in ev_tho.values():
            tho_any |= m

        troi_o = self.neo.cap_nhat(r, cfg.buoc_neo_mm)
        g6 = _runs_at_least(troi_o > cfg.g3_radial_mm, cfg.diff_min_run,
                            self.mask_mu)
        tho_any |= g6

        with np.errstate(all='ignore'):
            nen_that = (~np.isnan(self.bg.bg)) & \
                       (self.bg.bg < self.bg.MOC_TRONG * 0.5)
            khop_nen = (~np.isnan(r)) & nen_that & \
                       (np.abs(r - self.bg.bg) <= self.bg.le_tien_canh())
        hat_tho = tho_any & ~khop_nen

        objs = gom_vat_the(fg | hat_tho, r, self.grid, cfg, self.mask_mu, pts,
                           self.dtheta_deg)
        small = them_vat_nho(objs, (fg | hat_tho) & ~o_nn & ~khop_nen,
                            r, self.grid, cfg, pts, self.dtheta_deg, self.tracks)
        small_pending = []
        for o in small:
            for key in ('ev_bins', 'ev_tho', 'g6_bins'):
                o[key] = 0
            o['ev_thang'] = {}
            owners = sorted((math.hypot(o['cx']-(tr.x[0]+dt*tr.x[2]),
                                       o['cy']-(tr.x[1]+dt*tr.x[3])), tr.id)
                            for tr in self.tracks
                            if getattr(tr, 'narrow_confirmed', False))
            if (owners and owners[0][0] <= cfg.gate_base_mm
                    and (len(owners) == 1 or owners[1][0]-owners[0][0] >= 15.0)):
                o['layer_track_id'] = owners[0][1]
                o['thua'] = True
                objs.append(o)
            else:
                small_pending.append(o)
        for o in objs:
            b0, b1 = o['bins']
            lo, hi = max(0, b0 - 2), min(self.grid.nb, b1 + 3)
            o['ev_bins'] = int(np.count_nonzero(ev_mask[lo:hi]))
            o['ev_thang'] = {k: int(np.count_nonzero(m[lo:hi]))
                             for k, m in ev_thang.items()}
            o['ev_tho'] = max((int(np.count_nonzero(m[lo:hi]))
                               for m in ev_tho.values()), default=0)
            o['g6_bins'] = int(np.count_nonzero(g6[lo:hi]))
            o['g6_troi'] = float(np.max(troi_o[lo:hi])) if hi > lo else 0.0

        mask_hud = (fg_hud | hat_tho) & ~o_nn & ~khop_nen
        for o in objs:
            b0, b1 = o['bins']
            mask_hud[max(0, b0):min(self.grid.nb, b1 + 1)] = False

        for tr in self.tracks:
            tr.hud_tu_diem = False
            tr.trong_cum_gop = False
            tr.hud_tu_lop_cu_ly = False
            tr.dang_che_mot_phan = False
            tr.hud_n_diem_that = 0
            tr.hud_n_diem_du_kien = max(
                tr.so_diem_du_kien(self.dtheta_deg), 1)
            tr.hud_ty_le_thay = 0.0
            tr.bao_ve_lop_cu_ly = max(
                0, int(getattr(tr, 'bao_ve_lop_cu_ly', 0)) - 1)
            tr.predict(dt, cfg)
        objs = phan_be_mat_bi_che(objs, pts, self.tracks, self.grid, cfg, t, dt)
        bao_ve_vet_tai_vao(objs, self.tracks, cfg, t, dt)
        objs = cuu_vat_nho_da_biet(objs, pts, self.tracks, self.grid, cfg,
                                  self.dtheta_deg, dt, intensity_points)
        for o in objs:
            if o.get('known_narrow_recovery', False):
                b0, b1 = o['bins']
                mask_hud[max(0, b0):min(self.grid.nb, b1+1)] = False
        objs = tach_lop_cu_ly_theo_vet(
            objs, pts, self.tracks, self.grid, cfg, self.dtheta_deg)
        gan_cuong_do_cho_cum(objs, intensity_points, self.grid, cfg)
        pairs, chua_ghep = ghep(self.tracks, objs, cfg, dt, self.dtheta_deg)
        danh_dau_bi_che(self.tracks, objs, cfg)
        for tr in self.tracks:
            if getattr(tr, 'surface_hold', False):
                tr.bi_che = True
        for i_tr, tr in enumerate(self.tracks):
            if (getattr(tr, 'bao_ve_lop_cu_ly', 0) > 0
                    and i_tr not in pairs):
                tr.bi_che = True
                tr.trong_cum_gop = True

        gop_indices = set()
        if getattr(cfg, 'gop_dong_bang_nhom', False):
            for i_g, j_g in list(pairs.items()):
                if pairs.get(i_g) != j_g:
                    continue
                o_g = objs[j_g]
                if o_g.get('layer_track_id') is not None:
                    continue
                nua_g = 0.5 * float(o_g.get('width', 0.0)) + cfg.diff_mm
                nhom_g = [
                    k for k, tr_g in enumerate(self.tracks)
                    if ((k == i_g or k not in pairs)
                        and tr_g.state == DYNAMIC
                        and not getattr(tr_g, 'surface_hold', False)
                        and tr_g.id not in o_g.get('_surface_exclude', ())
                        and min(math.hypot(px - o_g['cx'], py - o_g['cy'])
                                for px, py in (tr_g.pos,
                                               tr_g.vi_tri_hud,
                                               tr_g.vi_tri_ve)) <= nua_g)
                ]
                if len(nhom_g) >= 2 and any(k not in pairs for k in nhom_g):
                    theo_r = sorted(
                        ((math.hypot(*self.tracks[k].pos), k) for k in nhom_g))
                    r_g = float(o_g.get('r', math.hypot(o_g['cx'], o_g['cy'])))
                    r_truoc, k_truoc = theo_r[0]
                    do_sau = theo_r[-1][0] - r_truoc
                    che_xuyen_tam = (
                        do_sau >= max(cfg.che_sau_mm,
                                     cfg.gop_xuyen_tam_min_mm)
                        and abs(r_g - r_truoc) <= cfg.gop_xuyen_tam_sai_so_mm)
                    k_rong = None
                    rong_g = float(o_g.get('width', 0.0))
                    diem_rong = []
                    tong_rong = 0.0
                    for k in nhom_g:
                        tr_k = self.tracks[k]
                        mu_k = tr_k.be_rong_id_uoc
                        sig_k = tr_k.sigma_be_rong_id(cfg)
                        if mu_k > 0 and math.isfinite(sig_k) and rong_g > 0:
                            sig_do = max(cfg.rong_id_sigma_san_mm,
                                         cfg.rong_id_sigma_ty_le * rong_g)
                            z2 = ((rong_g - mu_k) ** 2
                                  / max(sig_k ** 2 + sig_do ** 2, 1e-9))
                            diem_rong.append((z2, k))
                            tong_rong += mu_k
                    diem_rong.sort()
                    if (len(diem_rong) >= 2
                            and diem_rong[0][0] <= cfg.gop_rong_khop_z2
                            and diem_rong[1][0] - diem_rong[0][0]
                                >= cfg.gop_rong_cach_z2
                            and rong_g <= cfg.gop_rong_tong_ratio * tong_rong):
                        k_rong = diem_rong[0][1]

                    k_thay = (k_rong if k_rong is not None
                              else (k_truoc if che_xuyen_tam else None))
                    if k_thay is not None:
                        for k in list(pairs):
                            if k != k_thay and pairs.get(k) == j_g:
                                pairs.pop(k, None)
                        pairs[k_thay] = j_g
                        gop_indices.update(k for k in nhom_g if k != k_thay)
                    else:
                        gop_indices.update(nhom_g)
            for i_g in gop_indices:
                self.tracks[i_g].bi_che = True
                self.tracks[i_g].trong_cum_gop = True
                pairs.pop(i_g, None)

        for i, tr in enumerate(self.tracks):
            ok = i in pairs
            if ok:
                tr.so_vong_che = 0
                o = objs[pairs[i]]
                nua = 0.5 * float(o.get('width', 0.0)) + cfg.diff_mm
                chung = any(
                    (k != i and k not in pairs
                     and tk.id not in o.get('_surface_exclude', ())
                     and math.hypot(tk.pos[0] - o['cx'],
                                    tk.pos[1] - o['cy']) <= nua)
                    for k, tk in enumerate(self.tracks))
                tr.update(o, t, cfg, self.dtheta_deg, chung_cum=chung)
                if o.get('che_mot_phan', False):
                    tr.dang_che_mot_phan = True
                if o.get('tu_lop_cu_ly', False):
                    tr.bao_ve_lop_cu_ly = int(cfg.lop_cu_ly_bao_ve_vong)
                    tr.bi_che = True
                tr.evidence_bins = o['ev_bins']
                tr.tho_troi = float(o.get('ev_tho', 0.0))
                tr.g6_bins = int(o.get('g6_bins', 0))
                tr.tinh_dac_trung()
                co = tr.xet_cong(cfg, o['ev_thang'])
                tr.xet_xac_nhan_nhanh(
                    cfg,
                    o['ev_thang'].get(1, 0) >= cfg.strong_ev_bins,
                    True,
                )
            elif tr.bi_che:
                tr.evidence_bins = 0
                co = False
                tr.so_vong_che += 1
                if (getattr(tr, 'bao_ve_lop_cu_ly', 0) > 0
                        and tr.so_vong_che > 4):
                    mx, my = tr.last_meas
                    troi = math.hypot(tr.x[0] - mx, tr.x[1] - my)
                    tran = 0.55 * cfg.gate_base_mm
                    if troi > tran:
                        f = tran / troi
                        tr.x[0] = mx + (tr.x[0] - mx) * f
                        tr.x[1] = my + (tr.x[1] - my) * f
                    tr.x[2] *= 0.82
                    tr.x[3] *= 0.82
                rr = math.hypot(tr.x[0], tr.x[1])
                gh = 0.98 * cfg.max_range_mm
                if rr > gh:
                    tr.x[0] *= gh / rr
                    tr.x[1] *= gh / rr
                if tr.trong_cum_gop:
                    tr.cap_nhat_hud_cum_gop(t, cfg)
                tr.tinh_dac_trung()
                tr.xet_xac_nhan_nhanh(cfg, False, False)
            else:
                tr.evidence_bins = 0
                co = False
                mx, my = tr.last_meas
                troi = math.hypot(tr.x[0] - mx, tr.x[1] - my)
                tran = 0.15 * cfg.gate_base_mm
                if troi > tran:
                    f = tran / troi
                    tr.x[0] = mx + (tr.x[0] - mx) * f
                    tr.x[1] = my + (tr.x[1] - my) * f
                rr = math.hypot(tr.x[0], tr.x[1])
                gh = 0.98 * cfg.max_range_mm
                if rr > gh:
                    tr.x[0] *= gh / rr
                    tr.x[1] *= gh / rr
                tr.x[2] *= 0.7
                tr.x[3] *= 0.7
                tr.tinh_dac_trung()
                tr.xet_xac_nhan_nhanh(cfg, False, False)
            tr.last_matched = ok
            tr.cap_nhat_trang_thai(cfg, co, ok, bi_che=(not ok and tr.bi_che))

        gallery_matches = self._ghep_danh_tinh_an(objs, chua_ghep, t)
        for j in chua_ghep:
            o = objs[j]
            if o.get('thua', False):
                continue
            tr = Track(o, t, cfg)
            old_identity = gallery_matches.get(j)
            if old_identity is not None:
                self._phuc_hoi_danh_tinh(
                    tr, old_identity, o, cfg)
            tr.evidence_bins = o['ev_bins']
            tr.tho_troi = float(o.get('ev_tho', 0.0))
            tr.g6_bins = int(o.get('g6_bins', 0))
            tr.tinh_dac_trung()
            if o['ev_thang'].get(1, 0) >= cfg.strong_ev_bins:
                tr.gates = ['G1']
                tr.state = SUSPECT
                tr.hits = max(int(cfg.k_confirm) - 1, 0)
            self.tracks.append(tr)

        for ia, a in enumerate(self.tracks):
            for b in self.tracks[ia+1:]:
                if (a.state != DYNAMIC or b.state != DYNAMIC
                        or not a.last_matched or not b.last_matched
                        or min(a.n_updates, b.n_updates) < 8
                        or a.dang_che_mot_phan or b.dang_che_mot_phan):
                    continue
                distance = math.hypot(a.last_meas[0]-b.last_meas[0],
                                      a.last_meas[1]-b.last_meas[1])
                if distance > 0.5*(a.hud_width+b.hud_width) + 25.0:
                    a.id_tach_rieng.add(b.id)
                    b.id_tach_rieng.add(a.id)

        nguong_trung = 0.35 * cfg.gate_base_mm
        i = 0
        while i < len(self.tracks):
            j = i + 1
            while j < len(self.tracks):
                a_, b_ = self.tracks[i], self.tracks[j]
                pa, pb = a_.pos, b_.pos
                ca_hai_ghep = a_.last_matched and b_.last_matched
                bao_a = getattr(a_, 'bao_ve_lop_cu_ly', 0) > 0
                bao_b = getattr(b_, 'bao_ve_lop_cu_ly', 0) > 0
                mot_bao_ve = (bool(bao_a) ^ bool(bao_b)) and not (
                    a_.state == DYNAMIC and b_.state == DYNAMIC)
                dang_che = ((getattr(a_, 'bi_che', False)
                             or getattr(b_, 'bi_che', False)
                             or getattr(a_, 'so_vong_che', 0) > 0
                             or getattr(b_, 'so_vong_che', 0) > 0)
                            and not mot_bao_ve) \
                    or (bao_a and bao_b)
                da_tach_rieng = (b_.id in a_.id_tach_rieng
                                 and a_.id in b_.id_tach_rieng)
                if (not ca_hai_ghep and not dang_che and not da_tach_rieng
                        and math.hypot(pa[0] - pb[0], pa[1] - pb[1]) <= nguong_trung):
                    if mot_bao_ve:
                        bo = j if bao_a else i
                    elif a_.n_updates != b_.n_updates:
                        bo = j if a_.n_updates > b_.n_updates else i
                    else:
                        bo = j if a_.last_matched else i

                    giu_i = j if bo == i else i
                    vet_giu = self.tracks[giu_i]
                    vet_bo = self.tracks[bo]
                    if (vet_giu.state == DYNAMIC
                            and not vet_giu.last_matched and vet_bo.last_matched):
                        if vet_bo.state == DYNAMIC:
                            vet_giu.nhan_so_do_tu_vet_trung(vet_bo)
                        else:
                            mx, my = map(float, vet_bo.last_meas)
                            hx, hy = vet_giu.vi_tri_hud
                            khoang_t = max(t - vet_giu.t_hud, 1e-3)
                            dx, dy = mx - hx, my - hy
                            do_dai = math.hypot(dx, dy)
                            vet_giu.vi_tri_hud = (mx, my)
                            if do_dai > 0.5 * cfg.diff_mm:
                                hvx, hvy = dx / khoang_t, dy / khoang_t
                                toc = math.hypot(hvx, hvy)
                                if toc > cfg.max_speed_mm_s:
                                    f = cfg.max_speed_mm_s / toc
                                    hvx *= f
                                    hvy *= f
                                vet_giu.van_toc_hud = (float(hvx), float(hvy))
                                vet_giu.he_so_hud = 1.0
                            else:
                                vet_giu.van_toc_hud = (0.0, 0.0)
                                vet_giu.he_so_hud = 0.0
                            vet_giu.t_hud = t
                            vet_giu.hud_tu_diem = True
                            vet_giu.hud_bins = tuple(vet_bo.hud_bins)
                            vet_giu.hud_width = float(vet_bo.hud_width)
                            vet_giu.vi_tri_ve = tuple(vet_giu.vi_tri_hud)
                            vet_giu.t_vi_tri_ve = t
                    self.tracks.pop(bo)
                    if bo == i:
                        j = i + 1
                        continue
                else:
                    j += 1
            i += 1

        vet_hut = [tr for tr in self.tracks
                   if (tr.state == DYNAMIC and not tr.last_matched
                       and not getattr(tr, 'surface_hold', False)
                       and (t - tr.t_seen) <= 2.5 * dt)]
        nhom_hud = (gom_nhom_hud(mask_hud, r, self.grid, cfg, pts)
                    if vet_hut else [])
        if vet_hut and nhom_hud:
            ung_vien = []
            for i_h, tr in enumerate(vet_hut):
                hx, hy = tr.vi_tri_hud
                hvx, hvy = tr.van_toc_hud
                dt_hud = min(max(t - tr.t_hud, 0.0), dt)
                rx = hx + hvx * dt_hud
                ry = hy + hvy * dt_hud
                toc = math.hypot(hvx, hvy)
                gate = max(cfg.gate_base_mm,
                           0.5 * tr.hud_width + 1.25 * toc * dt)
                gate = min(gate,
                           max(cfg.gate_base_mm, cfg.max_speed_mm_s * dt))
                r_ref = math.hypot(rx, ry)
                if r_ref < 1.0:
                    continue
                urx, ury = rx / r_ref, ry / r_ref
                vr = hvx * urx + hvy * ury
                vt = -hvx * ury + hvy * urx
                gate_r = min(gate, max(45.0, 0.5 * tr.hud_width
                                       + 1.25 * abs(vr) * dt))
                gate_t = min(gate, max(45.0, 0.5 * tr.hud_width
                                       + 1.25 * abs(vt) * dt))
                for j_h, nhom in enumerate(nhom_hud):
                    ddx = nhom['cx'] - rx
                    ddy = nhom['cy'] - ry
                    kc = math.hypot(ddx, ddy)
                    le_r = abs(ddx * urx + ddy * ury)
                    le_t = abs(-ddx * ury + ddy * urx)
                    huong_hop = True
                    buoc_hud = math.hypot(nhom['cx'] - hx,
                                          nhom['cy'] - hy)
                    if toc > 0.5 * cfg.diff_mm / max(dt, 1e-3) \
                            and buoc_hud > 0.5 * cfg.diff_mm:
                        cos_huong = (((nhom['cx'] - hx) * hvx
                                     + (nhom['cy'] - hy) * hvy)
                                    / max(buoc_hud * toc, 1e-9))
                        huong_hop = cos_huong >= -0.25
                    if (kc <= gate and le_r <= gate_r and le_t <= gate_t
                            and huong_hop):
                        ung_vien.append((kc, i_h, j_h, gate))

            da_vet, da_nhom = set(), set()
            for kc, i_h, j_h, gate in sorted(ung_vien):
                if i_h in da_vet or j_h in da_nhom:
                    continue
                hang = sorted(x[0] for x in ung_vien if x[1] == i_h)
                cot = sorted(x[0] for x in ung_vien if x[2] == j_h)
                if kc != hang[0] or kc != cot[0]:
                    continue
                le = max(30.0, 0.25 * gate)
                if ((len(hang) > 1 and hang[1] - hang[0] < le)
                        or (len(cot) > 1 and cot[1] - cot[0] < le)):
                    continue

                tr = vet_hut[i_h]
                nhom = nhom_hud[j_h]
                hx, hy, hvx, hvy = tr.loc_hud(
                    float(nhom['cx']), float(nhom['cy']), t, cfg)
                toc = math.hypot(hvx, hvy)
                if toc > cfg.max_speed_mm_s:
                    f = cfg.max_speed_mm_s / toc
                    hvx, hvy = hvx * f, hvy * f
                tr.vi_tri_hud = (hx, hy)
                tr.van_toc_hud = (float(hvx), float(hvy))
                tr.he_so_hud = 1.0
                tr.gop_hud_active = False
                tr.t_hud = t
                tr.hud_tu_diem = True
                tr.hud_bins = tuple(nhom['bins'])
                tr.hud_width = float(nhom['width'])
                tr.vi_tri_ve = tuple(tr.vi_tri_hud)
                tr.t_vi_tri_ve = t
                da_vet.add(i_h)
                da_nhom.add(j_h)

        rmax = cfg.max_range_mm
        giu = []
        for tr in self.tracks:
            if (tr.state == DYNAMIC
                    and t - tr.t_seen >= max(float(cfg.lost_timeout_dyn_s), 0.0)):
                self._luu_danh_tinh_an(tr, t)
                continue
            if (getattr(tr, 'bi_che', False)
                    and tr.so_vong_che <= cfg.che_toi_da_vong
                    and math.hypot(*tr.pos) <= rmax):
                giu.append(tr)
                continue
            if tr.state == DYNAMIC:
                if tr.co_bang_chung_ra_khoi(cfg, t, dt):
                    self._luu_danh_tinh_an(tr, t)
                    continue
                if t - tr.t_seen >= max(float(cfg.lost_timeout_dyn_s), 0.0):
                    self._luu_danh_tinh_an(tr, t)
                    continue
            else:
                if (t - tr.t_seen > cfg.lost_timeout_s
                        or math.hypot(*tr.pos) > rmax):
                    continue

            if (tr.state != DYNAMIC
                    and tr.ty_le_ghep() < cfg.ghep_toi_thieu):
                continue

            giu.append(tr)
        self.tracks = giu

        for tr in self.tracks:
            thay_truc_tiep = ((tr.last_matched
                               and tr.bearing_sigma_deg <= cfg.goc_ve_max)
                              or tr.hud_tu_diem)
            if tr.state == DYNAMIC:
                if tr.trong_cum_gop:
                    tr.dong_bang_hien_thi = (math.hypot(*tr.van_toc_hud) < 1.0)
                else:
                    tr.dong_bang_hien_thi = not thay_truc_tiep
                tr.dang_tin_cay = True
            else:
                tr.dong_bang_hien_thi = False
                tr.dang_tin_cay = ((t - tr.t_seen) <= cfg.ngung_ve_sau_s
                                   and tr.bearing_sigma_deg <= cfg.goc_ve_max)

        for tr in self.tracks:
            if getattr(tr, 'surface_hold', False):
                tr.x[:2] = tr.surface_reference['center']
                tr.x[2:] = 0.0
                tr.vi_tri_hud = tr.surface_saved_hud
                tr.vi_tri_ve = tr.surface_saved_hud
                tr.van_toc_hud = (0.0,0.0)
                tr.hud_filter_pos = tr.surface_saved_hud
                tr.hud_raw_prev = tr.surface_saved_hud
                tr.hud_filter_vel = (0.0,0.0)
                tr.gop_hud_active = False
        hoc_be_mat_tinh(self.tracks, pts, self.grid, cfg, t)
        gan_cuong_do_cho_cum(small_pending, intensity_points, self.grid, cfg)
        self._cap_nhat_ung_vien_nho(t, small_pending, dt)
        self._kiem_tra_hong(t, r, n_raw_points)
        return {
            'dt': dt, 'r_bins': r, 'fg': fg, 'ev': ev_mask,
            'objs': objs, 'dtheta': self.dtheta_deg,
            'khop_nen': khop_nen,
            'bg_ready': self.bg.ready(t), 'canh_bao': self.canh_bao,
            'sensor_guard': False, 'sensor_moved': False,
            'pose_rotation_deg': float((self.pose_last or {}).get('rotation_deg', 0.0)),
            'pose_translation_mm': float((self.pose_last or {}).get('translation_mm', 0.0)),
        }

    def _cap_nhat_ung_vien_nho(self, t, objects, dt):

        cfg = self.cfg
        candidates = getattr(self, 'narrow_candidates', [])
        objects = [o for o in objects if not any(
            tr.state == DYNAMIC and min(math.hypot(o['cx']-px, o['cy']-py)
                for px, py in (tr.pos, tr.last_meas, tr.vi_tri_hud))
                < max(150.0, 1.5*tr.hud_width)
            for tr in self.tracks)]
        for tr in candidates:
            tr.predict(dt, cfg)
        pairs, unused = ghep(candidates, objects, cfg, dt, self.dtheta_deg)
        keep = []
        confirmed = []
        for i, tr in enumerate(candidates):
            if i in pairs:
                tr.update(objects[pairs[i]], t, cfg, self.dtheta_deg)
                tr.last_matched = True
                tr.cap_nhat_trang_thai(cfg, False, True)
            else:
                tr.last_matched = False
                tr.misses += 1
            if tr.state == DYNAMIC:
                probe = dict(objects[pairs[i]], _small_motion_verified=True)
                if tr.cuong_do_id_uoc is not None:
                    probe['cuong_do_log_rho'] = tr.cuong_do_id_uoc
                confirmed.append((tr, probe))
            elif t-tr.t_seen <= 0.4:
                keep.append(tr)
        probes = [o for _, o in confirmed]
        old_ids = self._ghep_danh_tinh_an(probes, set(range(len(probes))), t)
        active_ids = {tr.id for tr in self.tracks}
        for j, (tr, probe) in enumerate(confirmed):
            old = old_ids.get(j)
            if old is not None and int(old['id']) not in active_ids:
                self._phuc_hoi_danh_tinh(tr, old, probe, cfg)
            else:
                tr.id = Track._next
                Track._next += 1
            tr.narrow_confirmed = True
            active_ids.add(tr.id)
            self.tracks.append(tr)
        for j in unused:
            next_id = Track._next
            tr = Track(objects[j], t, cfg)
            Track._next = next_id
            self.narrow_sequence = getattr(self, 'narrow_sequence', 0) + 1
            tr.id = -self.narrow_sequence
            keep.append(tr)
        self.narrow_candidates = keep

    def _mask_vet_dong(self):

        m = np.zeros(self.grid.nb, dtype=bool)
        nguong = self.cfg.g4_anchor_mm * 0.4
        for tr in self.tracks:
            if tr.state != DYNAMIC:
                continue
            if tr.feat['d_anchor'] < nguong and tr.evidence_bins == 0:
                continue
            px, py = tr.pos
            r = math.hypot(px, py)
            if r < 1.0:
                continue
            th = math.degrees(math.atan2(px, py))
            nua = max(math.degrees(math.atan2(250.0, r)), 3.0)
            half = self.cfg.fov_half_deg
            span = 2 * half
            b0 = int((th - nua + half) / span * self.grid.nb)
            b1 = int((th + nua + half) / span * self.grid.nb)
            m[max(0, b0):min(self.grid.nb, b1 + 1)] = True
        return m

    def _kiem_tra_hong(self, t, r, n_raw):

        cfg = self.cfg
        self.canh_bao = None
        if self.cung_bi_chan is not None:
            g0, g1 = self.cung_bi_chan
            self.canh_bao = f'VÙNG MÙ {g0:+.0f}°..{g1:+.0f}° — CÓ VẬT CHE'
            return
        if not self.n_pts_hist or len(self.n_pts_hist) < 10:
            return
        nen = float(np.median(self.n_pts_hist))
        if n_raw < nen * cfg.blind_ratio:
            self.canh_bao = 'NGHI BỊ CHE'
            return
        if self.bg.ready(t):
            with np.errstate(all='ignore'):
                khe = self.bg.bg - cfg.min_range_mm - self.bg.le_tien_canh()
                hep = (~np.isnan(self.bg.bg)) & (khe < 20.0)
            if np.count_nonzero(_runs_at_least(hep, 4)) >= 4:
                bi = np.flatnonzero(_runs_at_least(hep, 4))
                g0 = self.grid.bin_angle(int(bi[0]))
                g1 = self.grid.bin_angle(int(bi[-1]))
                self.canh_bao = f'NỀN CHIẾM HẾT {g0:+.0f}°..{g1:+.0f}°'
                return

