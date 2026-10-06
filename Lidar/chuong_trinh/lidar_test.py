





import argparse
import json
import math
import os
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue

import numpy as np

from lidar_core_test import (Config, Detector, preprocess, DYNAMIC, SUSPECT,
                             STATIC, HAVE_SCIPY)



CFG = Config()

BO_TIA_NHIEU = False
GIU_CUONG_DO = True


def ang_correct_deg(dist_mm):


    if dist_mm <= 1.0:
        return 0.0
    return math.degrees(math.atan(21.8 * (155.3 - dist_mm) / (155.3 * dist_mm)))


def checksum_ok(pkt, bpn):



    lsn = pkt[3]
    if len(pkt) < 10 + lsn * bpn:
        return False
    recv = pkt[8] | (pkt[9] << 8)
    calc = (pkt[0] | (pkt[1] << 8)) ^ (pkt[2] | (pkt[3] << 8)) \
        ^ (pkt[4] | (pkt[5] << 8)) ^ (pkt[6] | (pkt[7] << 8))
    for i in range(lsn):
        o = 10 + i * bpn
        if bpn == 3:
            calc ^= pkt[o + 1] | (pkt[o + 2] << 8)
            calc ^= pkt[o]                                     
        else:
            calc ^= pkt[o] | (pkt[o + 1] << 8)
    return (calc & 0xFFFF) == recv


class ScanParser:


    def __init__(self):
        self.buf = bytearray()
        self.pending = []
        self.frames = deque(maxlen=60)
        self.n_tran = 0                                                   
        self.bpn = None                                                
        self.use_checksum = True
        self._cs_pass = 0
        self._cs_fail = 0
        self._cs_decided = False
        self.t_hat = None                                                    
        self.t_den_truoc = None                                            
        self.d_hist = deque(maxlen=25)
        self.n_hist = deque(maxlen=25)
        self.lat_hist = deque(maxlen=16)
        self.t_ra_truoc = None                                                        
        self.n_bo = 0                                                   

    def _nhip(self, t_den):



        if self.t_hat is None or self.t_den_truoc is None:
            self.t_hat = t_den
            self.t_den_truoc = t_den
            self.t_ra_truoc = t_den
            return t_den

        d = t_den - self.t_den_truoc
        self.t_den_truoc = t_den
        if 0.05 < d < 0.5:
            self.d_hist.append(d)
        if len(self.d_hist) >= 5:
            T = float(np.median(self.d_hist))
        else:
            T = d if 0.05 < d < 0.5 else 1.0 / 6.0
        T = min(max(T, 0.08), 0.35)

        self.t_hat += T

        lat = t_den - self.t_hat
        self.lat_hist.append(lat)
        lat_min = min(self.lat_hist)

        if lat_min > 3.0 * T:                                        
            self.t_hat = t_den
            self.lat_hist.clear()
        elif lat_min < -3.0 * T:                                        
            self.lat_hist.clear()
        else:
            keo = 0.10 * lat_min
            self.t_hat += max(-0.5 * T, min(0.5 * T, keo))

        t_ra = self.t_hat - 0.5 * T

        if self.t_ra_truoc is not None and t_ra < self.t_ra_truoc + 0.60 * T:
            t_ra = self.t_ra_truoc + 0.60 * T
        self.t_ra_truoc = t_ra
        return t_ra

        return self.t_hat

    def _so_byte_moi_mau(self):


        if self.bpn is not None:
            return self.bpn
        for thu in (3, 2):
            i, dat = 0, 0
            for _ in range(6):
                if i + 10 > len(self.buf) or self.buf[i:i + 2] != b'\xAA\x55':
                    break
                L = 10 + self.buf[i + 3] * thu
                if i + L + 2 > len(self.buf):
                    break
                if self.buf[i + L:i + L + 2] != b'\xAA\x55':
                    break
                dat += 1
                i += L
            if dat >= 4:
                self.bpn = thu
                print(f"[+] Thiết bị gửi {thu} byte mỗi mẫu.")
                return thu
        return 3                                                    

    def feed(self, data):
        self.buf.extend(data)
        while True:
            j = self.buf.find(b'\xAA\x55')
            if j < 0:
                if len(self.buf) > 1:
                    del self.buf[:len(self.buf) - 1]
                return
            if j:
                del self.buf[:j]
            if len(self.buf) < 10:
                return
            ct = self.buf[2]
            lsn = self.buf[3]
            bpn = self._so_byte_moi_mau()
            pkt_len = 10 + lsn * bpn
            if lsn == 0 or pkt_len > 4096:
                del self.buf[:2]
                continue
            if len(self.buf) < pkt_len:
                return
            pkt = bytes(self.buf[:pkt_len])
            del self.buf[:pkt_len]
            self._handle(pkt, ct, lsn, bpn)

    def _handle(self, pkt, ct, lsn, bpn):
        if not self._cs_decided:
            if checksum_ok(pkt, bpn):
                self._cs_pass += 1
            else:
                self._cs_fail += 1
            if self._cs_pass + self._cs_fail >= 200:
                rate = self._cs_pass / max(1, self._cs_pass + self._cs_fail)
                self._cs_decided = True
                self.use_checksum = rate > 0.5
                if not self.use_checksum:
                    print("[!] Checksum không khớp giao thức (tỉ lệ đạt "
                          f"{rate*100:.0f}%) -> tự tắt kiểm tra checksum.")
                else:
                    print(f"[+] Checksum hoạt động (tỉ lệ đạt {rate*100:.0f}%).")
        elif self.use_checksum:
            if not checksum_ok(pkt, bpn):
                return

        if ct & 0x01:
            n = len(self.pending)
            if n > 20:
                self.n_hist.append(n)
                med = float(np.median(self.n_hist))
                if len(self.n_hist) < 8 or n >= 0.60 * med:
                    if len(self.frames) == self.frames.maxlen:
                        self.n_tran += 1
                    self.frames.append((self._nhip(time.perf_counter()),
                                        self.pending))
                else:
                    self.n_bo += 1
            self.pending = []

        fsa = pkt[4] | (pkt[5] << 8)
        lsa = pkt[6] | (pkt[7] << 8)
        a0 = (fsa >> 1) / 64.0
        diff = ((lsa >> 1) / 64.0 - a0) % 360.0

        for i in range(lsn):
            o = 10 + i * bpn
            if o + bpn > len(pkt):
                break
            raw = (pkt[o + 1] | (pkt[o + 2] << 8)) if bpn == 3 else (pkt[o] | (pkt[o + 1] << 8))

            d = float(raw >> 2)
            nhieu = raw & 0x03
            if d <= 0.0:
                continue

            if BO_TIA_NHIEU and nhieu in (2, 3):
                continue

            a = a0 + diff * i / (lsn - 1) if lsn > 1 else a0
            a += ang_correct_deg(d)
            if GIU_CUONG_DO:
                self.pending.append((a % 360.0, d,
                                     pkt[o] if bpn == 3 else 0))
            else:
                self.pending.append((a % 360.0, d))

    def pop_frame(self):
        return self.frames.popleft() if self.frames else None


HERE = os.path.dirname(os.path.abspath(__file__))
_clients = []
_clients_lock = threading.Lock()
HOC_LAI = {'co': False}
WEB_DEBUG = {'co': False}


def broadcast(payload):
    line = ('data: ' + json.dumps(payload, separators=(',', ':')) + '\n\n').encode()
    with _clients_lock:
        for q in _clients:
            try:
                q.get_nowait()
            except Empty:
                pass
            q.put_nowait(line)


def du_lieu_vet_dong(tr, t):

    dong_bang = bool(getattr(tr, 'dong_bang_hien_thi', False))
    if dong_bang:
        px, py = getattr(tr, 'vi_tri_ve', tr.last_meas)
        vx = vy = speed = heading = 0.0
        bearing = math.degrees(math.atan2(px, py))
        range_mm = math.hypot(px, py)
        bearing_err = float(getattr(tr, 'sigma_goc_ve_deg',
                                    tr.bearing_sigma_deg))
        range_err = float(getattr(tr, 'sigma_tam_ve_mm',
                                  tr.range_sigma_mm))
    else:
        px, py = getattr(tr, 'vi_tri_hud', tr.pos)
        vx, vy = getattr(tr, 'van_toc_hud',
                         (float(tr.x[2]), float(tr.x[3])))
        speed = math.hypot(vx, vy)
        heading = math.degrees(math.atan2(vx, vy))
        bearing = math.degrees(math.atan2(px, py))
        range_mm = math.hypot(px, py)
        bearing_err = tr.bearing_sigma_deg
        range_err = tr.range_sigma_mm

    stale_age = max(0.0, t - getattr(tr, 't_vi_tri_ve', tr.t_seen))
    partial_occlusion = bool(getattr(tr, 'dang_che_mot_phan', False))
    occluded = bool(
        partial_occlusion
        or (getattr(tr, 'bi_che', False)
            and getattr(tr, 'so_vong_che', 0) <= int(CFG.che_toi_da_vong))
    )
    width_mm = float(getattr(tr, 'be_rong_id_uoc', 0.0))
    if width_mm <= 0:
        width_mm = float(getattr(tr, 'hud_width', 0.0))
    observed_points = max(0, int(getattr(tr, 'hud_n_diem_that', 0)))
    expected_points = max(observed_points,
                          int(getattr(tr, 'hud_n_diem_du_kien', 1)), 1)
    visible_fraction = min(1.0, observed_points / max(expected_points, 1))
    active = bool(
        tr.last_matched
        or getattr(tr, 'hud_tu_diem', False)
        or occluded
        or stale_age <= max(float(CFG.ngung_ve_sau_s), 0.0)
    )

    return {
        'id': tr.id,
        'x': px / 1000.0,
        'y': py / 1000.0,
        'vx': vx / 1000.0,
        'vy': vy / 1000.0,
        'speed': speed / 1000.0,
        'heading': heading,
        'bearing': bearing,
        'bearing_err': bearing_err,
        'range': range_mm / 1000.0,
        'range_err': range_err / 1000.0,
        'age': t - tr.t_created,
        'matched': bool(tr.last_matched),
        'occluded': occluded,
        'partial_occlusion': partial_occlusion,
        'occlusion_frames': int(getattr(tr, 'so_vong_che', 0)),
        'surface_width': width_mm / 1000.0,
        'observed_points': observed_points,
        'expected_points': expected_points,
        'visible_fraction': visible_fraction,
        'range_layer': bool(getattr(tr, 'hud_tu_lop_cu_ly', False)),
        'surface_predicted': bool(occluded or observed_points < expected_points),
        'raw_recovered': bool(getattr(tr, 'hud_tu_diem', False)),
        'frozen': dong_bang,
        'hud_gain': float(getattr(tr, 'he_so_hud', 0.0)),
        'stale_age': stale_age,
        'active': active,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            try:
                with open(os.path.join(HERE, 'radar_hud_test.html'), 'rb') as f:
                    body = f.read()
            except FileNotFoundError:
                self.send_error(404, 'radar_hud_test.html not found next to lidar_test.py')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == '/relearn':
            HOC_LAI['co'] = True
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == '/config':
            body = json.dumps(CFG.as_dict()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('X-Accel-Buffering', 'no')
            self.end_headers()
            q = Queue(maxsize=1)
            with _clients_lock:
                _clients.append(q)
            try:
                while True:
                    try:
                        chunk = q.get(timeout=10.0)
                    except Empty:
                        chunk = b': keep-alive\n\n'
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except Exception:
                pass
            finally:
                with _clients_lock:
                    _clients[:] = [client for client in _clients
                                    if client is not q]
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/relearn':
            HOC_LAI['co'] = True
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/debug':
            n = int(self.headers.get('Content-Length', 0))
            try:
                req = json.loads(self.rfile.read(n) or b'{}')
                WEB_DEBUG['co'] = bool(req.get('enabled', False))
                ok = True
            except Exception:
                ok = False
            body = json.dumps({'ok': ok, 'enabled': WEB_DEBUG['co']}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/config':
            n = int(self.headers.get('Content-Length', 0))
            try:
                CFG.update(json.loads(self.rfile.read(n)))
                ok = True
            except Exception:
                ok = False
            body = json.dumps({'ok': ok, 'config': CFG.as_dict()}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)


class QuietThreadingHTTPServer(ThreadingHTTPServer):

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError,
                            ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def start_server(port):
    srv = QuietThreadingHTTPServer(('127.0.0.1', port), Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def autodetect(port_hint, baud_hint):
    import serial
    from serial.tools import list_ports

    ports = [port_hint] if port_hint else [p.device for p in list_ports.comports()]
    if not ports:
        print("❌ Không thấy cổng COM nào. Kiểm tra cáp và driver USB.")
        return None
    bauds = [baud_hint] if baud_hint else [921600, 460800, 115200]

    for p in ports:
        for b in bauds:
            try:
                ser = serial.Serial(p, b, timeout=0.2)
            except Exception:
                continue
            time.sleep(0.35)
            data = ser.read(8192)
            if data.count(b'\xAA\x55') >= 5:
                print(f"[+] Tìm thấy LiDAR ở {p} @ {b} baud")
                ser.reset_input_buffer()
                return ser
            ser.close()
    print("❌ Không nhận được gói tin YDLidar hợp lệ ở bất kỳ cổng/baud nào.")
    print("   Kiểm tra: động cơ LiDAR có quay không, chân MOTOR_PIN, và PC_BAUD")
    print("   trong firmware có khớp với --baud bên này không.")
    return None


def set_duty(ser, pct):

    try:
        ser.write(f"D{int(pct)}\n".encode())
        ser.flush()
        return True
    except Exception as e:
        print(f"[!] Không gửi được lệnh duty: {e}")
        return False


def measure_hz(ser, seconds=3.0):
    parser = ScanParser()
    parser.use_checksum = False
    parser._cs_decided = True
    stamps = []
    t_end = time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        n = ser.in_waiting
        data = ser.read(n if n else 1)
        if data:
            parser.feed(data)
        while True:
            fr = parser.pop_frame()
            if fr is None:
                break
            stamps.append(fr[0])
    if len(stamps) < 3:
        return None
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    gaps.sort()
    med = gaps[len(gaps) // 2]
    return 1.0 / med if med > 1e-6 else None


def sweep_motor(ser):

    print("\nĐo tần số quét ở từng mức duty của chân M-C.")
    print("Nhắc lại: duty LỚN = quay NHANH (đo được, xem quét toàn dải).\n")
    print("   duty      tần số quét")
    print("   ----      -----------")
    best = None
    for pct in (100, 85, 70, 55, 40, 25, 10, 0):
        if not set_duty(ser, pct):
            return
        time.sleep(2.5)                                           
        ser.reset_input_buffer()
        hz = measure_hz(ser, 3.0)
        if hz is None:
            print(f"   {pct:3d}%      không đọc được dữ liệu")
            continue
        mark = ""
        if 5.0 <= hz <= 8.6:
            if best is None or abs(hz - 8.0) < abs(best[1] - 8.0):
                best = (pct, hz)
        if hz > 8.6:
            mark = "  (vượt dải danh định 5–8 Hz)"
        elif hz < 4.6:
            mark = "  (dưới dải danh định 5–8 Hz)"
        print(f"   {pct:3d}%      {hz:5.2f} Hz{mark}")

    print()
    if best:
        print(f"=> Gần 8 Hz nhất: duty {best[0]}%  ->  {best[1]:.2f} Hz")
        print(f"   Từ giờ chạy kèm:  python lidar_radar.py --duty {best[0]}")
        set_duty(ser, best[0])
    else:
        print("=> Không mức nào rơi vào dải 5–8 Hz. Kiểm tra lại đấu dây chân M-C")
        print("   và nguồn 5V (LiDAR cần 300–500 mA lúc khởi động).")


_PARSER = {'p': None}


def n_cut():
    p = _PARSER['p']
    return p.n_bo if p is not None else 0


def frames_from_serial(ser):




    parser = ScanParser()
    _PARSER['p'] = parser
    dung = threading.Event()

    def doc():
        while not dung.is_set():
            try:
                n = ser.in_waiting
                data = ser.read(n if n else 1)
            except Exception:
                break
            if data:
                parser.feed(data)

    th = threading.Thread(target=doc, daemon=True)
    th.start()
    try:
        while True:
            fr = parser.pop_frame()
            if fr is None:
                time.sleep(0.002)
                continue
            yield fr
    finally:
        dung.set()


def frames_from_replay(path, loop=False):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [json.loads(l) for l in f if l.strip()]
    if not lines:
        return
    t0 = lines[0]['t']
    span = lines[-1]['t'] - t0
    wall0 = time.perf_counter()
    while True:
        for rec in lines:
            target = wall0 + (rec['t'] - t0)
            while time.perf_counter() < target:
                time.sleep(0.002)
            replay_pts = []
            for p in rec['pts']:
                if len(p) >= 3:
                    replay_pts.append((p[0], p[1], p[2]))
                elif len(p) >= 2:
                    replay_pts.append((p[0], p[1]))
            yield (time.perf_counter(), replay_pts)
        if not loop:
            return
        wall0 += span + 1.0 / 8.0


def uoc_luong_goc_mat(pts, cum, cfg):


    b0, b1 = cum.get('bins', (None, None))
    if b0 is None or b1 is None:
        return None

    half = cfg.fov_half_deg
    span_goc = 2.0 * half
    nb = int(cfg.n_bins)
    r_min = float(cum.get('r_min', 0.0))
    sau_toi_da = max(35.0, 0.45 * float(cum.get('width', 0.0)))

    xy = []
    for rel, d, x, y in pts:
        b = int((rel + half) / span_goc * nb)
        if b0 <= b <= b1 and d <= r_min + sau_toi_da:
            xy.append((x, y))
    if len(xy) < 6:
        return None

    a = np.asarray(xy, dtype=float)
    for _ in range(3):
        tam = a.mean(axis=0)
        z = a - tam
        vals, vecs = np.linalg.eigh(z.T @ z)
        huong = vecs[:, int(np.argmax(vals))]
        phap = np.array([-huong[1], huong[0]])
        lech = z @ phap
        med = float(np.median(lech))
        mad = 1.4826 * float(np.median(np.abs(lech - med)))
        giu = np.abs(lech - med) <= max(2.0, 3.5 * mad)
        if int(giu.sum()) < 6 or bool(np.all(giu)):
            break
        a = a[giu]

    if len(a) < 6:
        return None
    tam = a.mean(axis=0)
    z = a - tam
    vals, vecs = np.linalg.eigh(z.T @ z)
    huong = vecs[:, int(np.argmax(vals))]

    if huong[0] < 0.0:
        huong = -huong
    goc = math.degrees(math.atan2(float(huong[1]), float(huong[0])))
    if goc > 90.0:
        goc -= 180.0
    elif goc < -90.0:
        goc += 180.0

    doc = z @ huong
    phap = np.array([-huong[1], huong[0]])
    rms = float(np.sqrt(np.mean((z @ phap) ** 2)))
    dai = float(np.ptp(doc))
    if dai < 60.0 or rms > 8.0:
        return None
    tam_hinh_hoc = tam + 0.5 * (float(doc.min()) + float(doc.max())) * huong
    return (goc, rms, len(a), dai,
            float(tam_hinh_hoc[0]), float(tam_hinh_hoc[1]))


def run(args):
    print("[DEMO] Đang chạy bản nhiều lớp cự ly; ba file gốc không bị sử dụng để ghi đè.")
    if args.replay:
        src = frames_from_replay(args.replay, loop=args.loop)
        print(f"[+] Phát lại từ {args.replay}")
    else:
        ser = autodetect(args.port, args.baud)
        if ser is None:
            return
        if args.sweep:
            sweep_motor(ser)
            ser.close()
            return
        if args.duty is not None:
            set_duty(ser, args.duty)
            print(f"[+] Đặt duty chân M-C = {args.duty}%  (duty lớn = quay nhanh)")
            time.sleep(2.0)                                                      
            ser.reset_input_buffer()
        src = frames_from_serial(ser)

    record_path = args.record_intensity or args.record
    record_intensity = bool(args.record_intensity)
    rec = open(record_path, 'w', encoding='utf-8') if record_path else None
    if record_intensity:
        print(f"[THỰC NGHIỆM] Ghi góc + cự ly + cường độ vào {record_path}")
        print("                 Thuật toán nhận dạng vẫn chỉ dùng góc + cự ly.")
    det = Detector(CFG)
    srv = start_server(args.http_port)
    print(f"[+] Mở trình duyệt tại  http://127.0.0.1:{args.http_port}")
    if not HAVE_SCIPY:
        print("[i] Không có scipy -> dùng ghép tham lam thay cho Hungarian.")

    n_frame = 0
    intensity_total = 0
    intensity_nonzero = 0
    intensity_warned = False
    t_last_print = time.perf_counter()
    ghep_hist = deque(maxlen=60)
    goc_mat_hist = deque(maxlen=20)
    tam_mat_hist = deque(maxlen=20)
    tam_mat_chuan = None
    vi_tri_mat = None
    t_goc_mat_cuoi = None
    if args.calib:
        print("[i] 'góc tâm' cho biết vật nằm ở đâu; 'xoay mặt' cho biết tấm đã tự xoay.")
        print("    'tâm hình học' dùng để giữ đúng một tâm quay ở cả 0°, 15°, 30°.")
        print("    Đặt mặt gần 0° và tâm hình học gần hướng 0°; giữ yên để tự lấy mốc.")

    try:
        for t, raw_pts in src:
            process_started = time.perf_counter()
            n_frame += 1
            raw_geom = [(float(p[0]), float(p[1]))
                        for p in raw_pts if len(p) >= 2]
            if rec is not None:
                if record_intensity:
                    intensity_values = [int(p[2]) for p in raw_pts
                                        if len(p) >= 3]
                    intensity_total += len(intensity_values)
                    intensity_nonzero += sum(q > 0 for q in intensity_values)
                    saved_pts = [[round(float(p[0]), 3), round(float(p[1]), 1),
                                  int(p[2])]
                                 for p in raw_pts if len(p) >= 3]
                    rec_obj = {'t': t, 'format': 'angle_distance_intensity_v1',
                               'pts': saved_pts}
                else:
                    saved_pts = [[round(float(p[0]), 3), round(float(p[1]), 1)]
                                 for p in raw_pts if len(p) >= 2]
                    rec_obj = {'t': t, 'pts': saved_pts}
                rec.write(json.dumps(rec_obj) + '\n')
                if (record_intensity and not intensity_warned and
                        n_frame >= 20 and intensity_nonzero == 0):
                    intensity_warned = True
                    print("[!] Cường độ của 20 frame đầu đều bằng 0.")
                    print("    File vẫn được ghi nhưng chưa phù hợp để hiệu chỉnh ID.")

            if HOC_LAI['co']:
                HOC_LAI['co'] = False
                det.hoc_lai_nen()
                print("[+] Học lại nền theo yêu cầu từ giao diện.")

            if det.thong_bao_luoi:
                print(f"[+] Tự chỉnh {det.thong_bao_luoi}")
                det.thong_bao_luoi = None

            pts = preprocess(raw_geom, CFG)
            info = det.step(t, pts, len(raw_geom), raw_points=raw_geom,
                            intensity_points=raw_pts)
            dt = info['dt']
            clusters = info['objs']
            clusters_sorted = sorted(clusters, key=lambda c: c['r'])

            goc_mat_hien = None
            do_on_goc_mat = None
            tam_x_hien = tam_y_hien = None
            tam_r_hien = tam_goc_hien = None
            do_on_tam = None
            lech_tam = None
            if args.calib and clusters_sorted:
                chinh = clusters_sorted[0]
                est = uoc_luong_goc_mat(pts, chinh, CFG)
                if est is not None:
                    goc_moi, _, _, _, tam_x_moi, tam_y_moi = est
                    pos = (tam_x_moi, tam_y_moi)
                    if (vi_tri_mat is not None
                            and math.hypot(pos[0] - vi_tri_mat[0],
                                           pos[1] - vi_tri_mat[1]) > 80.0):
                        goc_mat_hist.clear()
                        tam_mat_hist.clear()
                    if (goc_mat_hist
                            and abs(goc_moi - float(np.median(goc_mat_hist))) > 5.0):
                        goc_mat_hist.clear()
                        tam_mat_hist.clear()
                    vi_tri_mat = pos
                    goc_mat_hist.append(goc_moi)
                    tam_mat_hist.append(pos)
                    t_goc_mat_cuoi = t
                elif t_goc_mat_cuoi is None or t - t_goc_mat_cuoi > 0.8:
                    goc_mat_hist.clear()
                    tam_mat_hist.clear()
                if goc_mat_hist:
                    goc_mat_hien = float(np.median(goc_mat_hist))
                    do_on_goc_mat = 1.4826 * float(np.median(
                        np.abs(np.asarray(goc_mat_hist) - goc_mat_hien)))
                if tam_mat_hist:
                    tam_x_hien = float(np.median([p[0] for p in tam_mat_hist]))
                    tam_y_hien = float(np.median([p[1] for p in tam_mat_hist]))
                    tam_r_hien = math.hypot(tam_x_hien, tam_y_hien)
                    tam_goc_hien = math.degrees(math.atan2(tam_x_hien, tam_y_hien))
                    do_on_tam = 1.4826 * float(np.median([
                        math.hypot(p[0] - tam_x_hien, p[1] - tam_y_hien)
                        for p in tam_mat_hist]))
                    if (tam_mat_chuan is None
                            and len(goc_mat_hist) == goc_mat_hist.maxlen
                            and abs(goc_mat_hien) <= 3.0
                            and do_on_goc_mat <= 0.3
                            and abs(tam_goc_hien) <= 2.0
                            and do_on_tam <= 2.0):
                        tam_mat_chuan = (tam_x_hien, tam_y_hien)
                    if tam_mat_chuan is not None:
                        lech_tam = math.hypot(tam_x_hien - tam_mat_chuan[0],
                                              tam_y_hien - tam_mat_chuan[1])
            sensor_guard = bool(info.get('sensor_guard', False))
            dyn = ([] if sensor_guard else
                   [tr for tr in det.tracks
                    if tr.state == DYNAMIC and getattr(tr, 'dang_tin_cay', True)])
            dyn_active = [
                tr for tr in dyn
                if (tr.last_matched
                    or getattr(tr, 'hud_tu_diem', False)
                    or (getattr(tr, 'bi_che', False)
                        and getattr(tr, 'so_vong_che', 0)
                            <= int(CFG.che_toi_da_vong))
                    or (t - getattr(tr, 't_vi_tri_ve', tr.t_seen))
                       <= max(float(CFG.ngung_ve_sau_s), 0.0))
            ]
            candidates = ([] if sensor_guard else
                          [tr for tr in det.tracks
                           if tr.state == SUSPECT
                           and getattr(tr, 'dang_tin_cay', True)])

            if args.calib:
                if time.perf_counter() - t_last_print > 0.5:
                    t_last_print = time.perf_counter()
                    print(f"\n--- HIỆU CHỈNH  ({len(pts)} điểm, {len(clusters)} cụm, "
                          f"{1.0/max(dt,1e-3):.1f} Hz) ---")
                    for k_c, c in enumerate(clusters_sorted[:4]):
                        rel = math.degrees(math.atan2(c['cx'], c['cy']))
                        side = "PHẢI" if rel > 3 else ("TRÁI" if rel < -3 else "GIỮA")
                        print(f"   r = {c['r']/1000:5.3f} m   góc = {rel:+6.1f}° ({side})"
                              f"   rộng = {c['width']:5.0f} mm   {c['n']:3d} ô góc")
                        if k_c == 0:
                            if goc_mat_hien is None:
                                print("       xoay mặt = chưa đo được (giữ tấm phẳng, bỏ tay ra)")
                            else:
                                trang_thai = ("ỔN" if len(goc_mat_hist) >= 6
                                              and do_on_goc_mat <= 0.8 else "CHỜ")
                                print(f"       xoay mặt = {goc_mat_hien:+5.1f}°"
                                      f"   dao động ≈ ±{do_on_goc_mat:3.1f}°"
                                      f"   [{trang_thai}]")
                                if tam_mat_chuan is None:
                                    print(f"       tâm hình học = {tam_r_hien:5.0f} mm,"
                                          f" góc {tam_goc_hien:+5.1f}°"
                                          "   [CHƯA LẤY MỐC]")
                                else:
                                    tt_tam = ("TÂM ỔN" if lech_tam <= 5.0
                                              else ("LỆCH NHẸ" if lech_tam <= 10.0
                                                    else "DỊCH TÂM"))
                                    print(f"       tâm hình học = {tam_r_hien:5.0f} mm,"
                                          f" góc {tam_goc_hien:+5.1f}°"
                                          f"   lệch mốc = {lech_tam:4.1f} mm"
                                          f"   [{tt_tam}]")
            elif time.perf_counter() - t_last_print > 3.0:
                t_last_print = time.perf_counter()
                hz = 1.0 / max(dt, 1e-3)
                warn = "" if 4.6 <= hz <= 8.6 else "   <-- ngoài dải 5-8 Hz, chỉnh --duty"
                cb = f"   [{info['canh_bao']}]" if info['canh_bao'] else ""
                gt = (f" | ghép {100*sum(ghep_hist)/len(ghep_hist):3.0f}%"
                      if ghep_hist else "")
                print(f"quét {hz:4.1f} Hz | {len(pts):3d} điểm | {len(clusters):2d} vật | "
                      f"{len(det.tracks):2d} vết | {len(dyn_active)} ĐỘNG"
                      f" + {len(dyn) - len(dyn_active)} dấu mờ{gt}"
                      f" | cụt {n_cut()}{warn}{cb}")

            for tr in dyn_active:
                ghep_hist.append(1.0 if tr.last_matched else 0.0)

            payload_now = time.perf_counter()
            dyn_payload = [du_lieu_vet_dong(tr, t) for tr in dyn]
            active_payload = [tr for tr in dyn_payload if tr['active']]
            payload = {
                'seq': n_frame,
                't': t,
                'dt': dt,
                'scan_age_s': max(0.0, payload_now - t),
                'process_ms': max(0.0, (payload_now - process_started) * 1000.0),
                'ty_le_ghep': (sum(ghep_hist) / len(ghep_hist)) if ghep_hist else 1.0,
                'n_vat': len(clusters),
                'n_cut': n_cut(),
                'hz': 1.0 / max(dt, 1e-3),
                'max_range': CFG.max_range_mm / 1000.0,
                'fov_half': CFG.fov_half_deg,
                'lost_fade_s': max(float(CFG.lost_timeout_dyn_s), 0.1),
                'canh_bao': info['canh_bao'],
                'sensor_guard': sensor_guard,
                'sensor_moved': bool(info.get('sensor_moved', False)),
                'pose_rotation_deg': float(info.get('pose_rotation_deg', 0.0)),
                'pose_translation_mm': float(info.get('pose_translation_mm', 0.0)),
                'tracks': dyn_payload,
                'candidates': [{
                    'id': tr.id,
                    'x': tr.pos[0] / 1000.0,
                    'y': tr.pos[1] / 1000.0,
                    'vx': float(tr.x[2]) / 1000.0,
                    'vy': float(tr.x[3]) / 1000.0,
                    'speed': tr.speed / 1000.0,
                    'bearing': tr.bearing_deg,
                    'bearing_err': tr.bearing_sigma_deg,
                    'range': tr.range_mm / 1000.0,
                    'matched': bool(tr.last_matched),
                    'state': tr.state,
                } for tr in candidates],
                'debug': {
                    'points': ([[round(p[2] / 1000.0, 4),
                                 round(p[3] / 1000.0, 4)] for p in pts]
                               if WEB_DEBUG['co'] else []),
                    'tracks': [{
                        'id': tr.id,
                        'x': tr.pos[0] / 1000.0,
                        'y': tr.pos[1] / 1000.0,
                        'state': tr.state,
                        'gates': '+'.join(tr.gates),
                        'ev': tr.evidence_bins,
                        'd_anchor': round(tr.feat['d_anchor'], 1),
                        'd_radial': round(tr.feat['d_radial'], 1),
                        'straight': round(tr.feat['straight'], 3),
                        'speed': round(tr.speed / 1000.0, 3),
                    } for tr in det.tracks],
                },
                'stats': {
                    'n_dyn': len(active_payload),
                    'n_memory': len(dyn_payload),
                    'n_track': len(det.tracks),
                    'n_cluster': len(clusters),
                    'n_point': len(pts),
                    'avg_speed': (sum(tr['speed'] for tr in active_payload)
                                  / len(active_payload)) if active_payload else 0.0,
                },
            }
            broadcast(payload)

    except KeyboardInterrupt:
        print("\n[+] Dừng.")
    finally:
        if rec is not None:
            rec.close()
            print(f"[+] Đã ghi {n_frame} frame vào {record_path}")
            if record_intensity:
                pct = 100.0 * intensity_nonzero / max(intensity_total, 1)
                print(f"    Mẫu cường độ khác 0: {intensity_nonzero}/"
                      f"{intensity_total} ({pct:.1f}%)")
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description="Khối phân biệt vật cản động/tĩnh — YDLidar S2 Pro")
    ap.add_argument('--port', default=None, help='Cổng COM (bỏ trống để tự dò)')
    ap.add_argument('--baud', type=int, default=None,
                    help='Baud tới ESP32-S3 (bỏ trống để tự dò 921600/460800/115200)')
    ap.add_argument('--http-port', type=int, default=8770)
    nhom_ghi = ap.add_mutually_exclusive_group()
    nhom_ghi.add_argument('--record', default=None,
                          help='Ghi phiên quét dạng cũ: [góc, cự ly]')
    nhom_ghi.add_argument('--record-intensity', default=None,
                          help='Ghi thực nghiệm: [góc, cự ly, cường độ]')
    ap.add_argument('--replay', default=None, help='Phát lại từ file .jsonl')
    ap.add_argument('--loop', action='store_true', help='Lặp lại file phát lại vô hạn')
    ap.add_argument('--duty', type=int, default=None,
                    help='Duty PWM chân M-C, 0-100. DUTY NHỎ = QUAY NHANH')
    ap.add_argument('--sweep', action='store_true',
                    help='Đo tần số quét ở từng mức duty để tìm mức cho ra 8 Hz')
    ap.add_argument('--calib', action='store_true',
                    help='In góc/khoảng cách của các cụm gần nhất để kiểm chứng bằng thước')
    nhom_sigma = ap.add_mutually_exclusive_group()
    nhom_sigma.add_argument('--sigma-r-moi', dest='sigma_r_moi',
                            action='store_true', default=True,
                            help='Dùng mô hình nhiễu bán kính 0,50/sqrt(N), đây là mặc định')
    nhom_sigma.add_argument('--sigma-r-luy-thua', dest='sigma_r_moi',
                            action='store_false',
                            help='Dùng lại mô hình lũy thừa cũ để đối chứng A/B')
    ap.add_argument('--phan-hoi-nhanh', action='store_true',
                    help='Xác nhận nhanh sau hai bước G1 mạnh liên tiếp cùng hướng; '
                         'đường xác nhận thường bốn frame vẫn giữ nguyên')
    ap.add_argument('--range', type=float, default=None, dest='ban_kinh',
                    help='Bán kính sử dụng, tính bằng CENTIMET (mặc định 50). '
                         'Cự ly nhỏ nhất phần cứng đo được là 12 cm, nên --range 20 '
                         'chỉ còn vành làm việc 12-20 cm.')
    ap.add_argument('--bo-tia-nhieu', dest='bo_tia_nhieu', action='store_true',
                    help='Loại các tia bị thiết bị đánh dấu nhiễu kính hoặc '
                         'nhiễu nắng. Mặc định GIỮ, xem chú thích ở đầu file.')
    ap.add_argument('--khong-bac-cau', dest='khong_bac_cau', action='store_true',
                    help='Tắt hẳn việc dò và bắc cầu vùng mù (để thử loại trừ)')
    ap.add_argument('--full', action='store_true',
                    help='Hiện TOÀN BỘ 360° thay vì nửa hình quạt — dùng để '
                         'xem LiDAR đang quét về phía nào')
    ap.add_argument('--front', type=float, default=None,
                    help='Góc thô của LiDAR ứng với hướng chính diện '
                         '(chạy tim_huong.py để tìm)')
    ap.add_argument('--flip', action='store_true',
                    help='Lật chiều góc nếu trái/phải bị ngược')
    args = ap.parse_args()
    global BO_TIA_NHIEU, GIU_CUONG_DO
    BO_TIA_NHIEU = bool(args.bo_tia_nhieu)
    GIU_CUONG_DO = True

    CFG.dung_sigma_r_moi = bool(args.sigma_r_moi)
    if CFG.dung_sigma_r_moi:
        print("[+] σ bán kính tâm cụm = 0,50/sqrt(N) mm (mô hình mặc định).")
        print("    Mô hình tiếp tuyến và kiểm định NIS vẫn được giữ nguyên.")
    else:
        print("[ĐỐI CHỨNG] Đang dùng mô hình sigma R lũy thừa cũ.")
    CFG.fast_confirm = 1.0 if args.phan_hoi_nhanh else 0.0
    if CFG.fast_confirm >= 0.5:
        print("[THỬ NGHIỆM] Phản hồi nhanh: cần 2 bước G1 mạnh, ghép liên tiếp, cùng hướng.")
        print("               Nhánh yếu 4 frame vẫn giữ nguyên để chống báo động giả.")

    if args.ban_kinh is not None:
        k = CFG.scale_theo_ban_kinh(args.ban_kinh * 10.0)
        print(f"[+] Bán kính sử dụng = {args.ban_kinh:.0f} cm "
              f"(vành làm việc {CFG.min_range_mm/10:.0f}-{args.ban_kinh:.0f} cm)")
        print(f"    Ngưỡng khoảng cách co theo tỉ lệ {k:.2f}:  "
              f"G3 = {CFG.g3_radial_mm:.0f} mm, G4 = {CFG.g4_anchor_mm:.0f} mm")
        if args.ban_kinh < 25:
            print("    [!] Vành làm việc rất hẹp. Vật phải nằm trong khoảng đó mới thấy.")
    if args.khong_bac_cau:
        CFG.bac_cau_vung_mu = 0.0
        print("[+] ĐÃ TẮT dò và bắc cầu vùng mù.")
    if args.full:
        CFG.fov_half_deg = 180.0
        print("[+] Chế độ TOÀN CẢNH 360° — đặt tay quanh LiDAR để xem nó nằm ở đâu")
    if args.front is not None:
        CFG.fov_center_deg = float(args.front)
        print(f"[+] Hướng chính diện = góc thô {args.front:.0f}°")
    if args.flip:
        CFG.angle_sign = -1.0
    run(args)


if __name__ == '__main__':
    main()
