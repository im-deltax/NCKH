
import numpy as np


class KalmanCV:
    def __init__(self, sigma_a_deg_s2, sigma_theta_deg, sigma_phi_deg,
                 sigma_v0_deg_s=90.0):
        self.sigma_a = float(sigma_a_deg_s2)

        self.H = np.array([[1.0, 0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0, 0.0]])

        self.R = np.diag([sigma_theta_deg ** 2, sigma_phi_deg ** 2])

        self.sigma_v0 = float(sigma_v0_deg_s)
        self.x = np.zeros(4)
        self.P = np.eye(4)
        self.khoi_tao_roi = False

        self.nu = None                   
        self.S = None                                    
        self.nis = None

    @staticmethod
    def _F(dt):
        F = np.eye(4)
        F[0, 1] = dt
        F[2, 3] = dt
        return F

    def _Q(self, dt):





        q = self.sigma_a ** 2
        q1 = q * np.array([[dt ** 3 / 3.0, dt ** 2 / 2.0],
                           [dt ** 2 / 2.0, dt]])
        Q = np.zeros((4, 4))
        Q[0:2, 0:2] = q1
        Q[2:4, 2:4] = q1
        return Q

    def khoi_tao(self, theta_m, phi_m):
        self.x = np.array([theta_m, 0.0, phi_m, 0.0])
        self.P = np.diag([self.R[0, 0], self.sigma_v0 ** 2,
                          self.R[1, 1], self.sigma_v0 ** 2])
        self.khoi_tao_roi = True
        self.nu = self.S = self.nis = None

    def du_doan(self, dt):
        if not self.khoi_tao_roi or dt <= 0:
            return
        F = self._F(dt)
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self._Q(dt)

    def hieu_chinh(self, theta_m, phi_m, R_thay_the=None):
        if not self.khoi_tao_roi:
            self.khoi_tao(theta_m, phi_m)
            return

        R = self.R if R_thay_the is None else R_thay_the
        z = np.array([theta_m, phi_m])

        self.nu = z - self.H @ self.x
        self.S = self.H @ self.P @ self.H.T + R
        K = self.P @ self.H.T @ np.linalg.inv(self.S)

        self.x = self.x + K @ self.nu

        IKH = np.eye(4) - K @ self.H
        self.P = IKH @ self.P @ IKH.T + K @ R @ K.T

        self.nis = float(self.nu.T @ np.linalg.inv(self.S) @ self.nu)

    def chan_van_toc(self, v_max):

        for i in (1, 3):
            if self.x[i] > v_max:
                self.x[i] = v_max
            elif self.x[i] < -v_max:
                self.x[i] = -v_max

    def suy_giam_van_toc(self, dt, tau):

        if not self.khoi_tao_roi or dt <= 0 or tau <= 0:
            return
        a = float(np.exp(-dt / tau))
        for i in (1, 3):
            v_cu = float(self.x[i])
            self.x[i] = v_cu * a
            self.P[i, i] += (v_cu * (1.0 - a)) ** 2

    def van_toc_co_y_nghia(self, k=2.0):



        ra = []
        for i in (1, 3):
            sd = float(np.sqrt(max(self.P[i, i], 0.0)))
            v = float(self.x[i])
            nguong = k * sd
            if nguong <= 0.0:
                ra.append(v)
            else:
                w = (v * v) / (v * v + nguong * nguong)
                ra.append(v * w)
        return ra[0], ra[1]

    def du_doan_truoc(self, T_d):

        if not self.khoi_tao_roi:
            return None
        return self._F(T_d) @ self.x

    def do_bat_dinh_vi_tri(self, T_d=0.0):
        if not self.khoi_tao_roi:
            return None
        F = self._F(T_d)
        P = F @ self.P @ F.T + self._Q(T_d)
        return np.sqrt(P[0, 0]), np.sqrt(P[2, 2])

    @property
    def theta(self):  return self.x[0]
    @property
    def dtheta(self): return self.x[1]
    @property
    def phi(self):    return self.x[2]
    @property
    def dphi(self):   return self.x[3]


BANG_NIS = {50: (1.55, 2.52), 100: (1.68, 2.37),
            200: (1.77, 2.26), 500: (1.85, 2.16)}


def danh_gia_nis(danh_sach_nis):
    a = np.asarray([v for v in danh_sach_nis if v is not None])
    if a.size < 20:
        return None
    M = a.size
    moc = min(BANG_NIS, key=lambda k: abs(k - M))
    lo, hi = BANG_NIS[moc]
    tb = float(a.mean())
    if tb > hi:
        kl = "Q qua nho, bo loc qua tu tin -> TANG sigma_a"
    elif tb < lo:
        kl = "Q qua lon, bo loc qua de dat -> GIAM sigma_a"
    else:
        kl = "Bo loc nhat quan"
    return tb, lo, hi, kl
