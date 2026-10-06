
import numpy as np


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0],
                     [s,  c, 0.0],
                     [0.0, 0.0, 1.0]])


def Ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[ c, 0.0, s],
                     [0.0, 1.0, 0.0],
                     [-s, 0.0, c]])


def ma_tran_quay(theta_deg, phi_deg):
    return Rz(np.radians(theta_deg)) @ Ry(-np.radians(phi_deg))


def huong_truc_quang(theta_deg, phi_deg):
    t, p = np.radians(theta_deg), np.radians(phi_deg)
    return np.array([np.cos(t) * np.cos(p),
                     np.sin(t) * np.cos(p),
                     np.sin(p)])


C_HOAN_VI = np.array([[0.0, 0.0, 1.0],
                      [-1.0, 0.0, 0.0],
                      [0.0, -1.0, 0.0]])


class HinhHoc:
    def __init__(self, f_u, f_v, c_u, c_v):
        self.fu, self.fv, self.cu, self.cv = f_u, f_v, c_u, c_v

    def pixel_sang_goc_tuyet_doi(self, u, v, theta_s_deg, phi_s_deg):

        xn = (u - self.cu) / self.fu
        yn = (v - self.cv) / self.fv

        d_b = np.array([1.0, -xn, -yn])

        d0 = ma_tran_quay(theta_s_deg, phi_s_deg) @ d_b

        theta_m = np.degrees(np.arctan2(d0[1], d0[0]))
        phi_m = np.degrees(np.arcsin(np.clip(d0[2] / np.linalg.norm(d0), -1.0, 1.0)))
        return theta_m, phi_m

    def pixel_sang_goc_xap_xi(self, u, v, theta_s_deg, phi_s_deg):
        xn = (u - self.cu) / self.fu
        yn = (v - self.cv) / self.fv
        cphi = max(np.cos(np.radians(phi_s_deg)), 0.2)                    
        dtheta = np.degrees(-xn / cphi)
        dphi = np.degrees(-yn)
        return theta_s_deg + dtheta, phi_s_deg + dphi

    def goc_sang_pixel(self, theta_m_deg, phi_m_deg, theta_s_deg, phi_s_deg):
        d0 = huong_truc_quang(theta_m_deg, phi_m_deg)
        d_b = ma_tran_quay(theta_s_deg, phi_s_deg).T @ d0
        if d_b[0] <= 1e-6:
            return None                                                  
        d_c = C_HOAN_VI.T @ d_b
        xn, yn = d_c[0] / d_c[2], d_c[1] / d_c[2]
        return self.cu + xn * self.fu, self.cv + yn * self.fv

    def fov(self, W, H):
        return (2 * np.degrees(np.arctan(W / (2 * self.fu))),
                2 * np.degrees(np.arctan(H / (2 * self.fv))))
