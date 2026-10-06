
import numpy as np


class PIDTienDinh:
    def __init__(self, kp, ki, kd, kff, N_loc,
                 deadband_deg, omega_max, gioi_han_khop,
                 v_ff_max=35.0, tau_ff=0.08, gia_toc_max=0.0):
        self.kp, self.ki, self.kd, self.kff = kp, ki, kd, kff
        self.N = N_loc
        self.deadband = deadband_deg
        self.omega_max = omega_max
        self.q_min, self.q_max = gioi_han_khop
        self.v_ff_max = float(v_ff_max)
        self.tau_ff = float(tau_ff)
        self.v_ff = 0.0
        self.gia_toc_max = float(gia_toc_max)
        self.u_truoc = 0.0

        self.I = 0.0
        self.D = 0.0
        self.y_truoc = None
        self.bao_hoa = False
        self.goc_lenh = None                                               
        self.v_ff = 0.0

    def dat_lai(self):
        self.I = 0.0
        self.D = 0.0
        self.y_truoc = None
        self.bao_hoa = False
        self.goc_lenh = None
        self.v_ff = 0.0
        self.u_truoc = 0.0

    def tinh(self, dat, do_duoc, van_toc_muc_tieu, dt):
        if dt <= 0:
            return do_duoc, 0.0, 0.0

        e = dat - do_duoc

        if abs(e) < self.deadband:
            e = 0.0

        if self.y_truoc is None:
            self.D = 0.0
        else:
            self.D = (self.N * (self.y_truoc - do_duoc) + self.D) / (1.0 + self.N * dt)
        self.y_truoc = do_duoc

        P = self.kp * e
        Ith = self.ki * self.I
        Dth = self.kd * self.D
        v = float(np.clip(van_toc_muc_tieu, -self.v_ff_max, self.v_ff_max))
        a = dt / (self.tau_ff + dt)
        self.v_ff += a * (v - self.v_ff)
        FF = self.kff * self.v_ff

        u = P + Ith + Dth + FF

        u_sat = float(np.clip(u, -self.omega_max, self.omega_max))
        self.bao_hoa = abs(u_sat - u) > 1e-9

        if self.gia_toc_max > 0.0:
            buoc = self.gia_toc_max * dt
            u_sat = float(np.clip(u_sat, self.u_truoc - buoc, self.u_truoc + buoc))
        self.u_truoc = u_sat

        if not (self.bao_hoa and np.sign(e) == np.sign(self.I) and self.I != 0):
            self.I += e * dt

        if self.goc_lenh is None:
            self.goc_lenh = do_duoc
        goc_moi = float(np.clip(self.goc_lenh + u_sat * dt, self.q_min, self.q_max))
        self.goc_lenh = goc_moi
        return goc_moi, e, u_sat


class MoHinhServo:


    def __init__(self, K, T, L, bat=False):
        self.K, self.T, self.L = K, T, L
        self.bat = bat
        self.y = 0.0
        self.hang_doi = []                                                       

    def dat_lai(self, goc=0.0):
        self.y = goc
        self.hang_doi.clear()

    def cap_nhat(self, goc_lenh, t_hien_tai, dt):
        if not self.bat:
            self.y = goc_lenh
            return self.y

        self.hang_doi.append((t_hien_tai, goc_lenh))

        u = self.hang_doi[0][1]
        while len(self.hang_doi) > 1 and self.hang_doi[0][0] < t_hien_tai - self.L:
            u = self.hang_doi.pop(0)[1]

        alpha = dt / (self.T + dt)
        self.y += alpha * (self.K * u - self.y)
        return self.y
