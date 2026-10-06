

import argparse
import csv
import sys
import threading
import math
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from . import cauhinh as C
from .bo_dieu_khien import MoHinhServo, PIDTienDinh
from .nguon_lidar import NguonLidar
from .nguon_iff import TramIFF, THU as IFF_THU
from .bo_loc_kalman import KalmanCV, danh_gia_nis
from .hinh_hoc import HinhHoc
from .canh_bao import tao_bo_canh_bao
from .thuc_nghiem import ThucNghiem

ap = argparse.ArgumentParser()
ap.add_argument("--port", default=C.COM_PORT)
ap.add_argument("--cam", type=int, default=C.CAM_INDEX)
ap.add_argument("--che-do", default="PD", choices=["P", "PD", "PRED", "FULL"],
                help="P    = chi khau ti le, moc so sanh. "
                     "PD   = them khau vi phan. "
                     "PRED = them Kalman va NGOAI SUY vi tri, KHONG tien dinh. "
                     "FULL = them ca khau tien dinh van toc.")
ap.add_argument("--khong-servo", action="store_true")
ap.add_argument("--chi-pan", action="store_true",
                help="chi bam truc pan, giu tilt dung yen o 0 do. "
                     "Dung khi servo tilt chua san sang.")
ap.add_argument("--ten", default="chay")
ap.add_argument("--imgsz", type=int, default=None,
                help="ghi de kich thuoc anh vao. Nho hon thi suy luan nhanh hon, "
                     "tuc T_d giam va nang duoc KP, nhung vat o xa kho nhan hon.")
ap.add_argument("--phoi-sang", type=float, default=None,
                help="thoi gian phoi sang thu cong, thang log2 giay tren Windows. "
                     "-6 la 1/64 giay, -7 la 1/128, -8 la 1/256. Cang am cang "
                     "ngan, anh cang it nhoe khi muc tieu di nhanh, nhung cang toi.")
ap.add_argument("--lidar", nargs="?", const=True, default=None,
                help="ghep voi khoi LiDAR. De trong de dung dia chi mac dinh, "
                     "hoac dua vao mot dia chi luong SSE khac")
ap.add_argument("--iff", nargs="?", const=True, default=None,
                help="ghep voi tram nhan dien ban thu. De trong de dung cong "
                     "mac dinh trong cauhinh, hoac dua vao ten cong khac")
ap.add_argument("--the", nargs="?", const="COM15", default=None,
                help="cong RP2040 Zero cua the IFF de thu nhanh bang phim: "
                     "b = BAN (phan hoi hop le), t = THU (im lang). "
                     "Chi co tac dung khi cua so Pan-tilt tracking dang duoc chon")
ap.add_argument("--nghi-tilt", type=float, default=None,
                help="goc ta o trang thai nghi [do], am la chuc xuong")
ap.add_argument("--gia-toc", type=float, default=None,
                help="tran gia toc goc lenh [do/s^2], 0 de tat")
ap.add_argument("--kff", type=float, default=None,
                help="ghi de he so tien dinh, de thu nhanh khong phai sua file. "
                     "0 = tat han tien dinh, chi giu Kalman va du doan truoc.")
ap.add_argument("--canh-bao", nargs="?", const=True, default=None,
                help="bat canh bao xam nhap: gui Telegram kem anh khi pan-tilt "
                     "bat dau BAM mot muc tieu IFF bao THU, dong thoi phat "
                     "camera len trang web trong mang Wi-Fi. De trong de dung "
                     "tep cau hinh mac dinh, hoac dua vao duong dan tep khac")
ap.add_argument("--kich-ban", default=None,
                help="chay thuc nghiem chuong 4 theo kich ban: bai1..bai6, "
                     "phu_a, phu_b. SPACE bat dau/ket thuc luot, x bo luot")
ap.add_argument("--cong-web", type=int, default=None,
                help="cong cua trang xem camera, mac dinh 8780. 0 de tat trang xem")
args = ap.parse_args()

class OThiGiac:
    def __init__(self):
        self.lock = threading.Lock()
        self.seq = 0
        self.t_chup = 0.0
        self.u = self.v = None
        self.conf = 0.0
        self.bbox = None
        self.t_inf = 0.0
        self.frame = None
        self.dung = False
        self.ngu = False


o = OThiGiac()


def luong_thi_giac():

    try:
        _luong_thi_giac()
    except Exception:
        import traceback
        print("\n[x] LUONG THI GIAC CHET. Nguyen nhan:", flush=True)
        traceback.print_exc()
        print("[x] Dung chuong trinh.", flush=True)
        o.dung = True


def _luong_thi_giac():
    from ultralytics import YOLO

    imgsz = args.imgsz if args.imgsz else C.IMGSZ
    mp = Path(C.MODEL_PATH)
    print(f"[i] Nap mo hinh {mp}, imgsz={imgsz}", flush=True)
    if not mp.exists():
        raise FileNotFoundError(
            f"Khong thay {mp.resolve()}. Chay lenh tu thu muc goc du an, "
            f"hoac sua MODEL_PATH trong pantilt/cauhinh.py")
    if C.BACKEND == "openvino":
        ov = mp.parent / f"{mp.stem}_ov{imgsz}_openvino_model"
        if not ov.exists():
            print(f"[i] Chua co {ov}, dang xuat OpenVINO cho imgsz={imgsz}, "
                  f"mat khoang mot phut", flush=True)
            goc = YOLO(str(mp)).export(format="openvino", imgsz=imgsz)
            Path(goc).rename(ov)
        model = YOLO(str(ov), task="detect")
    else:
        model = YOLO(str(mp))
    print("[i] Nap mo hinh xong", flush=True)

    print(f"[i] Mo camera {args.cam}", flush=True)
    cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, C.ANH_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, C.ANH_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)                 
    if args.phoi_sang is not None:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)                               
        cap.set(cv2.CAP_PROP_EXPOSURE, args.phoi_sang)
        print(f"[i] Phoi sang thu cong {args.phoi_sang} "
              f"(khoang 1/{2**(-args.phoi_sang):.0f} giay)", flush=True)
    if not cap.isOpened():
        raise RuntimeError(
            f"Khong mo duoc camera {args.cam}. Thu --cam 0 hoac --cam 2, "
            f"va dong moi chuong trinh khac dang dung webcam.")
    ok, thu = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError(f"Camera {args.cam} mo duoc nhung khong doc duoc khung hinh.")
    print(f"[i] Camera {thu.shape[1]}x{thu.shape[0]}. Luong thi giac da chay.", flush=True)

    truoc = None
    n_truot = 0                                                               
    while not o.dung:
        t0 = time.perf_counter()
        ok, frame = cap.read()
        if not ok:
            continue
        t_chup = time.perf_counter()

        if o.ngu:
            with o.lock:
                o.seq += 1
                o.t_chup, o.u, o.v, o.conf = t_chup, None, None, 0.0
                o.bbox, o.t_inf, o.frame = None, 0.0, frame
            truoc = None
            n_truot = 0
            continue

        r = model.predict(frame, imgsz=imgsz, conf=C.CONF, verbose=False)[0]
        t_inf = (time.perf_counter() - t0) * 1000.0

        u = v = None
        conf = 0.0
        bbox = None
        if r.boxes is not None and len(r.boxes) > 0:
            xy = r.boxes.xyxy.cpu().numpy()
            cf = r.boxes.conf.cpu().numpy()
            cx = (xy[:, 0] + xy[:, 2]) / 2
            cy = (xy[:, 1] + xy[:, 3]) / 2
            if truoc is None:
                k = int(np.argmax(cf))                                          
            else:
                d = np.sqrt((cx - truoc[0]) ** 2 + (cy - truoc[1]) ** 2)
                k = int(np.argmin(d))
                cong = C.CONG_HOP_LE_PX + C.CONG_NOI_PX * n_truot
                if d[k] > cong:
                    k = None
            if k is None:
                n_truot += 1
                if n_truot > C.N_MAT_TOI_DA:
                    truoc = None                                           
                    n_truot = 0
            else:
                n_truot = 0
                u, v, conf = float(cx[k]), float(cy[k]), float(cf[k])
                bbox = xy[k].astype(int)
                truoc = (u, v)
        else:
            n_truot += 1
            if n_truot > C.N_MAT_TOI_DA:
                truoc = None
                n_truot = 0

        with o.lock:
            o.seq += 1
            o.t_chup, o.u, o.v, o.conf = t_chup, u, v, conf
            o.bbox, o.t_inf, o.frame = bbox, t_inf, frame

    cap.release()


def main():
    hh = HinhHoc(C.F_U, C.F_V, C.C_U, C.C_V)

    kf = KalmanCV(C.SIGMA_A, C.SIGMA_THETA, C.SIGMA_PHI)

    kp = C.KP
    ki = C.KI if args.che_do == "FULL" else 0.0
    kd = C.KD if args.che_do in ("PD", "PRED", "FULL") else 0.0
    kff = C.KFF if args.che_do == "FULL" else 0.0
    if args.kff is not None:
        kff = float(args.kff)
        print(f"[i] Ghi de KFF = {kff}", flush=True)
    dung_kalman = args.che_do in ("PRED", "FULL")

    gia_toc = C.GIA_TOC_MAX if args.gia_toc is None else float(args.gia_toc)
    if args.nghi_tilt is not None:
        C.GOC_NGHI_TILT = float(args.nghi_tilt)
    pid_pan = PIDTienDinh(kp, ki, kd, kff, C.N_LOC_VP,
                          C.DEADBAND_DEG, C.OMEGA_MAX, (C.PAN_MIN, C.PAN_MAX),
                          C.V_FF_MAX, C.TAU_FF, gia_toc)
    pid_tilt = PIDTienDinh(kp, ki, kd, kff, C.N_LOC_VP,
                           C.DEADBAND_DEG, C.OMEGA_MAX, (C.TILT_MIN, C.TILT_MAX),
                           C.V_FF_MAX, C.TAU_FF, gia_toc)

    mh_pan = MoHinhServo(C.SERVO_K, C.SERVO_T, C.SERVO_L, C.DUNG_MO_HINH_SERVO)
    mh_tilt = MoHinhServo(C.SERVO_K, C.SERVO_T, C.SERVO_L, C.DUNG_MO_HINH_SERVO)

    link = None
    if not args.khong_servo:
        from serial.tools import list_ports
        from .giao_tiep import KetNoiServo
        co = [q.device for q in list_ports.comports()]
        print(f"[i] Cong dang co tren may: {co if co else 'khong thay cong nao'}",
              flush=True)
        if args.port not in co:
            raise SystemExit(
                f"\n[x] Khong thay {args.port} tren may.\n"
                f"    Cong hien co: {co}\n"
                f"    Cong USB cua Arduino doi so moi lan rut cam lai. Chon dung\n"
                f"    cong o tren, hoac sua COM_PORT trong pantilt/cauhinh.py.\n"
                f"    Neu khong thay cong nao thi rut cap USB, doi 5 giay, cam lai.\n"
                f"    Muon chay khong can servo thi them --khong-servo.")
        try:
            print(f"[i] Mo {args.port}, cho Arduino khoi dong lai 2 giay ...",
                  flush=True)
            link = KetNoiServo(args.port, C.BAUD)
            tra_loi = link.trang_thai()
            if not isinstance(tra_loi, dict) or "p" not in tra_loi:
                raise RuntimeError(
                    f"cong mo duoc nhung khong phai firmware pan-tilt, "
                    f"gui S nhan duoc {tra_loi!r}")
            link.dat_gioi_han(C.PAN_MIN, C.PAN_MAX, C.TILT_MIN, C.TILT_MAX)
            link.bat()
            link.ve_giua()
            print(f"[i] Da noi {args.port}. Bat tay: pan={tra_loi['p']:.2f} tilt={tra_loi['t']:.2f} en={tra_loi.get('en', 0):.0f}", flush=True)
        except Exception as e:
            raise SystemExit(
                f"\n[x] Khong noi duoc {args.port}: {e}\n"
                f"    Thuong gap nhat la mot chuong trinh khac dang giu cong.\n"
                f"    Dong Serial Monitor cua Arduino IDE, dong servo_console.py\n"
                f"    va do_dap_ung.py neu con mo, roi chay lai.\n"
                f"    Muon chay khong can servo thi them --khong-servo.")

    Path(C.THU_MUC_LOG).mkdir(parents=True, exist_ok=True)
    ten_log = Path(C.THU_MUC_LOG) / f"{args.ten}_{args.che_do}_{int(time.time())}.csv"
    f_log = open(ten_log, "w", newline="", encoding="utf-8") if C.GHI_LOG else None
    w_log = csv.writer(f_log) if f_log else None
    if w_log:
        w_log.writerow(["t", "epoch_s", "dt", "co_do", "u", "v", "conf",
                        "theta_m", "phi_m",
                        "theta_hat", "dtheta_hat", "phi_hat", "dphi_hat",
                        "theta_du_doan", "phi_du_doan",
                        "ld_huong", "ld_cu_ly", "ld_toc_do", "trang_thai",
                        "theta_s", "phi_s", "theta_cmd", "phi_cmd",
                        "e_theta", "e_phi", "u_theta", "u_phi",
                        "nis", "t_inf", "e_px",
                        "ld_id", "iff_ket", "iff_ly_do", "iff_ms",
                        "the_che_do", "luot", "nhan", "dang_do"])

    threading.Thread(target=luong_thi_giac, daemon=True).start()

    theta_cmd = phi_cmd = 0.0
    theta_s = phi_s = 0.0
    lich_su = deque(maxlen=400)                                                        
    seq_da_xu_ly = 0
    so_mat = 0
    theta_m_cuoi = phi_m_cuoi = None                                                
    t_do_cuoi = None                                                    
    goc_da_gui = None                                                              
    kich_hoat = False                                                         
    t_mat_ca_hai = None                                                    
    trang_thai = "CHO"
    o.ngu = C.NGU_KHI_CHO
    tram_iff = None
    if args.iff:
        cong = C.IFF_PORT if args.iff is True else str(args.iff)
        try:
            tram_iff = TramIFF(cong, C.IFF_BAUD, C.IFF_CHO_KHOI_DONG_S,
                               C.IFF_SO_LAN_HOI, C.IFF_HAN_CHO_S,
                               C.IFF_HAN_NHO_S, C.IFF_TRE_ROI_VUNG_S,
                               C.IFF_KE_THUA_S)
            tram_iff.bat_dau()
            print(f"[i] Ghep tram IFF tai {cong}", flush=True)
        except Exception as e:
            print(f"[!] Khong mo duoc tram IFF tai {cong}: {e}", flush=True)
            print("[!] Chay tiep khong co khau ban thu.", flush=True)
            tram_iff = None

    tag_iff = None
    khoa_tag = threading.Lock()
    the = {"che_do": ""}
    tn = ThucNghiem(args.kich_ban) if args.kich_ban else None

    def dat_che_do_the(la_ban, nguon="phim"):
        if tag_iff is None:
            print("[!] Chua mo cong the. Chay them --the COM15 de dung b/t.",
                  flush=True)
            return False
        lenh = b"T0\n" if la_ban else b"T4\n"
        mong_doi = "DUNG" if la_ban else "IM_LANG"
        ten = "BAN" if la_ban else "THU"
        try:
            with khoa_tag:
                tag_iff.reset_input_buffer()
                for _ in range(3):
                    tag_iff.write(lenh)
                    tag_iff.flush()
                    han = time.perf_counter() + 0.9
                    while time.perf_counter() < han:
                        dong = tag_iff.readline().decode("utf-8", "ignore").strip()
                        if "CHE DO THU:" not in dong:
                            continue
                        if mong_doi in dong:
                            the["che_do"] = ten
                            print(f"\n[TEST IFF] THE DA XAC NHAN {ten} "
                                  f"({mong_doi}, nguon={nguon}).", flush=True)
                            print("[TEST IFF] Cho LiDAR ve CHO roi moi dua vat vao.",
                                  flush=True)
                            return True
                    time.sleep(0.05)
            print(f"[!] Da gui {ten} nhung the KHONG XAC NHAN. "
                  "Khong dua vat vao; kiem tra COM15/firmware testtag.", flush=True)
        except Exception as e:
            print(f"[!] Khong doi duoc che do the: {e}", flush=True)
        return False

    if args.the:
        try:
            import serial
            tag_iff = serial.Serial(str(args.the), 115200, timeout=0.05,
                                    write_timeout=0.5)
            time.sleep(1.0)
            print(f"[i] Ghep the IFF tai {args.the}.", flush=True)

            tag_iff.reset_input_buffer()
            tag_iff.write(b"R\n")
            tag_iff.flush()
            han_sync = time.perf_counter() + 8.0
            sync_ok = False
            while time.perf_counter() < han_sync:
                dong = tag_iff.readline().decode("utf-8", "ignore").strip()
                if "DONG BO LAI: OK" in dong:
                    sync_ok = True
                    break
            if not sync_ok:
                raise RuntimeError("the khong bat lai duoc Sync cua tram")
            print("[i] The da dong bo lai voi phien tram hien tai.", flush=True)
            print("[i] PHIM THU trong PowerShell hoac cua so camera: "
                  "b = BAN, t = THU, q = thoat.", flush=True)
            dat_che_do_the(True, "khoi_dong")
        except Exception as e:
            print(f"[!] Khong mo duoc the IFF tai {args.the}: {e}", flush=True)
            print("[!] Phim b/t bi tat; IFF van chay theo che do hien tai cua the.",
                  flush=True)
            tag_iff = None

    def xu_ly_phim_thu(phim):
        if tn is not None and phim == ord(" "):
            tn.phim_cach()
            return False
        if tn is not None and phim in (ord("x"), ord("X")):
            tn.phim_x()
            return False
        if phim in (ord("b"), ord("B"), ord("t"), ord("T")):
            dat_che_do_the(phim in (ord("b"), ord("B")), "camera")
            return False
        return phim in (ord("q"), ord("Q"))

    def luong_phim_console():
        if tag_iff is None and tn is None:
            return
        try:
            import msvcrt
        except ImportError:
            return
        while not o.dung:
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                if c == " " and tn is not None:
                    tn.phim_cach()
                elif c in ("x", "X") and tn is not None:
                    tn.phim_x()
                elif c in ("b", "B", "t", "T"):
                    dat_che_do_the(c in ("b", "B"), "PowerShell")
                elif c in ("q", "Q"):
                    o.dung = True
                    return
            time.sleep(0.03)

    if tag_iff is not None or tn is not None:
        threading.Thread(target=luong_phim_console, daemon=True).start()

    def loc_ban_thu(vet):

        if tram_iff is None:
            return True
        ma = vet.get("id")
        if ma is None:
            return True
        return tram_iff.phan_xet(ma) == IFF_THU

    nguon_ld = None
    if args.lidar:
        url = C.LIDAR_URL if args.lidar is True else str(args.lidar)
        nguon_ld = NguonLidar(url, C.LIDAR_D_M, C.LIDAR_LECH_GOC_DEG,
                              C.LIDAR_DAO_DAU, C.LIDAR_HET_HAN_S,
                              C.LIDAR_TOC_DO_MIN,
                              bo_loc=loc_ban_thu if tram_iff else None)
        nguon_ld.bat_dau()
        print(f"[i] Ghep LiDAR tai {url}", flush=True)

    bo_cb = None
    if args.canh_bao:
        tep_cb = C.CANH_BAO_CFG if args.canh_bao is True else str(args.canh_bao)
        cong_web = C.CONG_WEB if args.cong_web is None else args.cong_web
        try:
            bo_cb = tao_bo_canh_bao(tep_cb, cong_web)
        except Exception as e:
            print(f"[!] Khong khoi dong duoc khoi canh bao: {e}", flush=True)
            bo_cb = None

    dang_quet = False                                                       
    ds_nis = []
    ds_e_px = []

    da_canh_bao = False                                                     
    ls_bam = deque(maxlen=300)
    Ts = 1.0 / C.TAN_SO_DIEU_KHIEN
    t0 = time.perf_counter()
    t_truoc = t0
    n_vong = 0

    print(f"[i] Che do {args.che_do}. Cho luong thi giac...", flush=True)
    if tn is not None:
        tn.gioi_thieu()
    t_bao = t0
    da_mo_cua_so = False
    try:
        while not o.dung:
            t_now = time.perf_counter()
            dt = t_now - t_truoc
            if dt < Ts:
                time.sleep(max(0.0, Ts - dt) * 0.8)
                continue
            t_truoc = t_now
            n_vong += 1
            if tn is not None and n_vong % 5 == 0:
                tn.nhac(trang_thai)

            if goc_da_gui is None:
                th_vao, ph_vao = theta_cmd, phi_cmd
            else:
                th_vao, ph_vao = goc_da_gui
            theta_s = mh_pan.cap_nhat(th_vao, t_now, dt)
            phi_s = mh_tilt.cap_nhat(ph_vao, t_now, dt)
            lich_su.append((t_now, theta_s, phi_s))

            vet_ld = nguon_ld.vet_hien_tai(t_now) if nguon_ld else None
            vet_ld_tho = (nguon_ld.vet_tho_hien_tai(t_now)
                          if nguon_ld else None)

            if tram_iff is not None and nguon_ld is not None:
                tram_iff.dat_lidar(vet_ld_tho is not None)

            ghi_iff = ("", "", "")
            ct_iff = None
            if tram_iff is not None and vet_ld_tho is not None:
                ct_iff = tram_iff.chi_tiet(vet_ld_tho.get("id"))
                if ct_iff is not None:
                    ghi_iff = ("BAN" if ct_iff["ban"]
                               else ("THU" if ct_iff["xong"] else "CHO"),
                               ct_iff["ly_do"], ct_iff["ms"])

            with o.lock:
                seq, t_chup, u, v, conf = o.seq, o.t_chup, o.u, o.v, o.conf
                bbox, t_inf, frame = o.bbox, o.t_inf, o.frame

            co_do = (seq != seq_da_xu_ly) and (u is not None)
            theta_m = phi_m = None

            if dung_kalman:
                kf.du_doan(dt)

            if co_do:
                seq_da_xu_ly = seq
                so_mat = 0
                t_anh = t_chup - C.T_CAP
                ts, ps = theta_s, phi_s
                for (tt, th, ph) in reversed(lich_su):
                    if tt <= t_anh:
                        ts, ps = th, ph
                        break
                theta_m, phi_m = hh.pixel_sang_goc_tuyet_doi(u, v, ts, ps)
                theta_m_cuoi, phi_m_cuoi = theta_m, phi_m
                t_do_cuoi = t_now

                if dung_kalman:
                    if not kf.khoi_tao_roi:
                        kf.khoi_tao(theta_m, phi_m)
                    else:
                        kf.hieu_chinh(theta_m, phi_m)
                        kf.chan_van_toc(C.V_MUC_TIEU_MAX)
                        if kf.nis is not None:
                            ds_nis.append(kf.nis)

                ds_e_px.append(np.hypot(u - C.C_U, v - C.C_V))
            elif seq != seq_da_xu_ly:
                seq_da_xu_ly = seq
                so_mat += 1

            if dung_kalman and kf.khoi_tao_roi and so_mat >= 1:
                kf.suy_giam_van_toc(dt, C.TAU_TRUOT_S)

            co_ld = vet_ld is not None
            co_ld_tho = vet_ld_tho is not None
            iff_la_ban = bool(ct_iff is not None
                              and ct_iff["xong"] and ct_iff["ban"])

            if nguon_ld is None or not C.CHO_LIDAR_KICH_HOAT:
                kich_hoat = True
            else:
                kich_hoat = co_ld

            if not kich_hoat:
                dat_theta, dat_phi = C.GOC_NGHI_PAN, C.GOC_NGHI_TILT
                v_theta = v_phi = 0.0
                if dung_kalman and kf.khoi_tao_roi:
                    kf.khoi_tao_roi = False
                theta_m_cuoi = phi_m_cuoi = None
                dang_quet = False
                if iff_la_ban:
                    trang_thai = "BAN_NGHI"
                elif co_ld_tho:
                    trang_thai = "CHO_IFF"
                else:
                    trang_thai = "CHO"
                o.ngu = C.NGU_KHI_CHO
            elif dung_kalman and kf.khoi_tao_roi and so_mat <= C.N_MAT_TOI_DA:
                trang_thai = "BAM"
                o.ngu = False
                v_theta, v_phi = kf.van_toc_co_y_nghia(C.K_KIEM_DINH_V)
                dat_theta = float(kf.x[0] + v_theta * C.T_D)             
                dat_phi = float(kf.x[2] + v_phi * C.T_D)
                if theta_m_cuoi is not None:
                    g = C.NGOAI_SUY_MAX_DEG
                    dat_theta = min(max(dat_theta, theta_m_cuoi - g), theta_m_cuoi + g)
                    dat_phi = min(max(dat_phi, phi_m_cuoi - g), phi_m_cuoi + g)
            elif theta_m_cuoi is not None and so_mat <= C.N_MAT_TOI_DA:
                trang_thai = "BAM"
                o.ngu = False
                dat_theta, dat_phi = theta_m_cuoi, phi_m_cuoi
                v_theta = v_phi = 0.0
            elif (theta_m_cuoi is not None and t_do_cuoi is not None
                  and t_now - t_do_cuoi < C.T_VE_GOC_S):
                dat_theta, dat_phi = theta_m_cuoi, phi_m_cuoi
                v_theta = v_phi = 0.0
            else:
                g_ld = nguon_ld.goc_muc_tieu(t_now) if nguon_ld else None
                if g_ld is not None and t_now - t0 >= C.T_ON_DINH_S:
                    dat_theta = min(max(g_ld, C.PAN_MIN), C.PAN_MAX)
                    R_ld = nguon_ld.cu_ly_ngang(t_now)
                    if R_ld is not None and R_ld > 0.05:
                        dat_phi = math.degrees(math.atan2(C.LIDAR_CHENH_CAO_M, R_ld))
                        dat_phi = min(max(dat_phi, C.TILT_MIN), C.TILT_MAX)
                    else:
                        dat_phi = C.GOC_NGHI_TILT
                    dang_quet = True
                    trang_thai = "BAN_GIAO"
                    o.ngu = False
                else:
                    dat_theta, dat_phi = C.GOC_NGHI_PAN, C.GOC_NGHI_TILT
                    dang_quet = False
                    trang_thai = "NGHI"
                    o.ngu = False
                v_theta = v_phi = 0.0
                if dung_kalman and kf.khoi_tao_roi:
                    kf.khoi_tao_roi = False
                theta_m_cuoi = phi_m_cuoi = None

            if bo_cb is not None:
                if trang_thai == "BAM":
                    if bbox is not None and frame is not None:
                        vet_bc = vet_ld if vet_ld is not None else vet_ld_tho
                        bo_cb.bao_thu(
                            None if vet_bc is None else vet_bc.get("id"),
                            frame, bbox, {
                                "co_iff": tram_iff is not None,
                                "iff_xong": bool(ct_iff and ct_iff["xong"]),
                                "iff_ly_do": ct_iff["ly_do"] if ct_iff else "",
                                "iff_ms": ct_iff["ms"] if ct_iff else 0,
                                "ld_cu_ly": None if vet_bc is None
                                else float(vet_bc.get("range", 0.0)),
                                "ld_huong": None if vet_bc is None
                                else float(vet_bc.get("bearing", 0.0)),
                                "ld_toc_do": None if vet_bc is None
                                else float(vet_bc.get("speed", 0.0)),
                                "conf": float(conf), "pan": float(theta_s),
                                "tilt": float(phi_s),
                            })
                else:
                    bo_cb.khong_bam()

            theta_cmd, e_th, u_th = pid_pan.tinh(dat_theta, theta_s, v_theta, dt)
            phi_cmd, e_ph, u_ph = pid_tilt.tinh(dat_phi, phi_s, v_phi, dt)
            if args.chi_pan:
                phi_cmd = 0.0                                                     

            if co_do and u is not None:
                ls_bam.append((t_now, theta_cmd, u))
                cu = [z for z in ls_bam if t_now - z[0] > 2.0]
                if cu and not da_canh_bao:
                    t_cu, th_cu, u_cu = cu[-1]
                    if (abs(theta_cmd - th_cu) > 20.0 and abs(u - u_cu) < 40.0
                            and abs(u - C.C_U) > 90.0 and abs(u_cu - C.C_U) > 90.0):
                        da_canh_bao = True
                        print("\n[!] Canh bao: goc lenh doi nhieu ma muc tieu van "
                              "lech xa tam anh.", flush=True)
                        print("    Co the co cau khong bam theo lenh, hoac muc tieu "
                              "di nhanh hon", flush=True)
                        print("    kha nang bam. Chuong trinh VAN CHAY TIEP.\n", flush=True)


            if link:
                if (goc_da_gui is None
                        or abs(theta_cmd - goc_da_gui[0]) >= C.NGUONG_GUI_DEG
                        or abs(phi_cmd - goc_da_gui[1]) >= C.NGUONG_GUI_DEG):
                    link.dat_goc(theta_cmd, phi_cmd, cho_phan_hoi=False)
                    goc_da_gui = (theta_cmd, phi_cmd)

            if w_log:
                w_log.writerow([
                    f"{t_now - t0:.4f}", f"{time.time():.6f}", f"{dt:.4f}", int(co_do),
                    "" if u is None else f"{u:.2f}", "" if v is None else f"{v:.2f}",
                    f"{conf:.3f}",
                    "" if theta_m is None else f"{theta_m:.4f}",
                    "" if phi_m is None else f"{phi_m:.4f}",
                    f"{kf.theta:.4f}", f"{kf.dtheta:.4f}",
                    f"{kf.phi:.4f}", f"{kf.dphi:.4f}",
                    f"{dat_theta:.4f}", f"{dat_phi:.4f}",
                    "" if vet_ld_tho is None else f"{vet_ld_tho.get('bearing', 0.0):.4f}",
                    "" if vet_ld_tho is None else f"{vet_ld_tho.get('range', 0.0):.4f}",
                    "" if vet_ld_tho is None else f"{vet_ld_tho.get('speed', 0.0):.4f}",
                    trang_thai,
                    f"{theta_s:.4f}", f"{phi_s:.4f}",
                    f"{theta_cmd:.4f}", f"{phi_cmd:.4f}",
                    f"{e_th:.4f}", f"{e_ph:.4f}", f"{u_th:.3f}", f"{u_ph:.3f}",
                    "" if kf.nis is None else f"{kf.nis:.4f}",
                    f"{t_inf:.1f}",
                    "" if u is None else f"{np.hypot(u - C.C_U, v - C.C_V):.2f}",
                    "" if vet_ld_tho is None else vet_ld_tho.get("id", ""),
                    ghi_iff[0], ghi_iff[1], ghi_iff[2],
                    the["che_do"], *(tn.cot_log() if tn else (0, "", 0)),
                ])

            if frame is None and time.perf_counter() - t_bao > 5.0:
                t_bao = time.perf_counter()
                print("[.] Chua co khung hinh nao tu luong thi giac...", flush=True)
            if frame is not None and not da_mo_cua_so:
                da_mo_cua_so = True
                print("[i] Da co khung hinh. Nhan q tren cua so anh de thoat.", flush=True)
            if o.ngu and da_mo_cua_so:
                toi = np.clip(frame.astype(np.float32) * 0.20,
                              0, 255).astype(np.uint8)
                h_anh, w_anh = toi.shape[:2]
                if trang_thai == "BAN_NGHI":
                    tieu_de = "BAN"
                    dong_1 = "IFF xac nhan quan minh - camera tam nghi"
                elif trang_thai == "CHO_IFF":
                    tieu_de = "DANG HOI"
                    dong_1 = "Dang cho ket qua IFF"
                else:
                    tieu_de = "CHO"
                    dong_1 = "Camera va co cau dang tam nghi"
                lop = toi.copy()
                cv2.rectangle(lop, (0, 0), (w_anh, 78), (0, 0, 0), -1)
                toi = cv2.addWeighted(lop, 0.52, toi, 0.48, 0.0)
                cv2.putText(toi, tieu_de, (22, 34),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (150, 150, 150), 2)
                cv2.putText(toi, dong_1, (22, 62),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (105, 105, 105), 1)
                cv2.imshow("Pan-tilt tracking", toi)
                if bo_cb is not None:
                    bo_cb.cap_nhat_web(toi, trang_thai_web(
                        trang_thai, tram_iff, nguon_ld, t_now, theta_s, phi_s))
                if xu_ly_phim_thu(cv2.waitKey(1) & 0xFF):
                    o.dung = True
                    break
            elif frame is not None and n_vong % 2 == 0:
                vis = ve(frame.copy(), hh, kf, bbox, u, v, conf, theta_s, phi_s,
                         e_th, e_ph, t_inf, so_mat, dung_kalman, args.che_do,
                         dang_quet, dat_theta, trang_thai,
                         dong_hud_nguon(nguon_ld, tram_iff, t_now, bo_cb))
                if bo_cb is not None:
                    bo_cb.cap_nhat_web(vis, trang_thai_web(
                        trang_thai, tram_iff, nguon_ld, t_now, theta_s, phi_s))
                if xu_ly_phim_thu(cv2.waitKey(1) & 0xFF):
                    break
    finally:
        o.dung = True
        time.sleep(0.2)
        cv2.destroyAllWindows()
        if link:
            try:
                link.ve_giua()
                time.sleep(0.4)
                link.dong()
            except Exception as e:
                print(f"[!] Khong dong duoc co cau: {e}", flush=True)
        if tram_iff:
            tram_iff.dong()
        if bo_cb is not None:
            bo_cb.dong()
            if bo_cb.su_kien:
                bo_cb.ghi_su_kien(str(ten_log).replace(".csv", "_canh_bao.csv"))
        if tn is not None:
            tn.ghi(str(ten_log).replace(".csv", "_danh_dau.csv"))
            print(f"[TN] Da ghi danh dau luot: "
                  f"{str(ten_log).replace('.csv', '_danh_dau.csv')}", flush=True)
        if tag_iff:
            try:
                tag_iff.write(b"T0\n")
                tag_iff.flush()
            except Exception:
                pass
            tag_iff.close()
        if f_log:
            f_log.close()
        bao_cao(ten_log, ds_nis, ds_e_px, n_vong, time.perf_counter() - t0)


def dong_hud_nguon(nguon_ld, tram_iff, t_now, bo_cb=None):
    phan = []
    if nguon_ld is not None:
        phan.append(nguon_ld.mo_ta(t_now))
    if tram_iff is not None:
        phan.append(tram_iff.mo_ta())
    if bo_cb is not None:
        m = bo_cb.mo_ta()
        if m:
            phan.append(m)
    return "   |   ".join(phan) if phan else None


def trang_thai_web(trang_thai, tram_iff, nguon_ld, t_now, theta_s, phi_s):
    return {
        "trang_thai": trang_thai,
        "iff": tram_iff.mo_ta() if tram_iff is not None else "không ghép trạm",
        "lidar": nguon_ld.mo_ta(t_now) if nguon_ld is not None else "không ghép",
        "goc": f"pan {theta_s:+.1f}°, tilt {phi_s:+.1f}°",
    }


def ve(vis, hh, kf, bbox, u, v, conf, theta_s, phi_s,
       e_th, e_ph, t_inf, so_mat, dung_kalman, che_do,
       dang_quet=False, goc_quet=0.0, trang_thai="", dong_lidar=None):
    H, W = vis.shape[:2]
    cv2.drawMarker(vis, (int(C.C_U), int(C.C_V)), (0, 0, 255),
                   cv2.MARKER_CROSS, 22, 1)

    if bbox is not None:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 200, 0), 2)
    if u is not None:
        cv2.drawMarker(vis, (int(u), int(v)), (0, 200, 0), cv2.MARKER_CROSS, 16, 2)
        cv2.line(vis, (int(C.C_U), int(C.C_V)), (int(u), int(v)), (0, 200, 0), 1)

    if dung_kalman and kf.khoi_tao_roi:
        xd = kf.du_doan_truoc(C.T_D)
        p = hh.goc_sang_pixel(xd[0], xd[2], theta_s, phi_s)
        if p and 0 <= p[0] < W and 0 <= p[1] < H:
            cv2.drawMarker(vis, (int(p[0]), int(p[1])), (0, 165, 255),
                           cv2.MARKER_TILTED_CROSS, 18, 2)

    hud = [
        f"che do {che_do}",
        f"servo  {theta_s:+6.1f} {phi_s:+6.1f} do",
        f"sai lech {e_th:+5.2f} {e_ph:+5.2f} do",
        f"T_inf  {t_inf:5.1f} ms",
    ]
    if dung_kalman and kf.khoi_tao_roi:
        hud.append(f"v muc tieu {kf.dtheta:+6.1f} {kf.dphi:+6.1f} do/s")
        if kf.nis is not None:
            hud.append(f"NIS {kf.nis:5.2f}")
    if so_mat:
        hud.append(f"MAT {so_mat}")
    if trang_thai:
        hud.append(trang_thai)
    if dang_quet:
        hud.append(f"-> {goc_quet:+.0f}")
    if dong_lidar:
        hud.append(dong_lidar)

    for i, s in enumerate(hud):
        y = 22 + i * 20
        cv2.putText(vis, s, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(vis, s, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.imshow("Pan-tilt tracking", vis)
    return vis


def bao_cao(ten_log, ds_nis, ds_e_px, n_vong, tong_t):
    print("\n" + "=" * 58)
    print(f"  KET QUA - che do {args.che_do}")
    print("=" * 58)
    print(f"  So chu ky dieu khien : {n_vong}")
    print(f"  Tan so thuc          : {n_vong / max(tong_t, 1e-9):.1f} Hz")
    if ds_e_px:
        a = np.asarray(ds_e_px)
        print(f"  RMSE bam             : {np.sqrt((a ** 2).mean()):6.2f} px")
        print(f"  Sai lech trung binh  : {a.mean():6.2f} px")
        print(f"  Sai lech lon nhat    : {a.max():6.2f} px")
    kq = danh_gia_nis(ds_nis)
    if kq:
        tb, lo, hi, kl = kq
        print(f"  NIS trung binh       : {tb:5.2f}   khoang chap nhan [{lo:.2f}, {hi:.2f}]")
        print(f"  -> {kl}")
    print(f"  Nhat ky              : {ten_log}")
    print("=" * 58)


if __name__ == "__main__":
    main()
