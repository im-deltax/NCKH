





import csv
import html
import json
import queue
import secrets
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2


def doc_bi_mat(duong_dan):

    p = Path(duong_dan)
    if not p.exists():
        return None
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] Tep {p} sai dinh dang JSON: {e}", flush=True)
        return None
    if not str(cfg.get("khoa_xem", "")).strip():
        cfg["khoa_xem"] = secrets.token_urlsafe(16)
        try:
            p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            print(f"[i] Da sinh khoa xem camera moi va ghi vao {p.name}",
                  flush=True)
        except Exception:
            pass
    return cfg


def ip_mang_noi_bo():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class GuiTelegram:

    API = "https://api.telegram.org/bot{token}/{phuong_thuc}"

    def __init__(self, token, chat_id, han_cho_s=15.0):
        self.token = str(token).strip()
        self.chat_id = str(chat_id).strip()
        self.han_cho_s = float(han_cho_s)

    def _url(self, phuong_thuc):
        return self.API.format(token=self.token, phuong_thuc=phuong_thuc)

    def _goi(self, phuong_thuc, du_lieu, kieu):
        req = urllib.request.Request(self._url(phuong_thuc), data=du_lieu,
                                     headers={"Content-Type": kieu})
        try:
            with urllib.request.urlopen(req, timeout=self.han_cho_s) as r:
                kq = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                kq = json.loads(e.read().decode("utf-8"))
            except Exception:
                raise RuntimeError(f"HTTP {e.code}") from None
        if not kq.get("ok"):
            raise RuntimeError(kq.get("description", "Telegram tu choi"))
        return kq.get("result")

    def gui_chu(self, noi_dung):
        du_lieu = urllib.parse.urlencode({
            "chat_id": self.chat_id, "text": noi_dung,
            "parse_mode": "HTML", "disable_web_page_preview": "true",
        }).encode("utf-8")
        return self._goi("sendMessage", du_lieu,
                         "application/x-www-form-urlencoded")

    def gui_anh(self, jpeg, chu_thich):
        ranh = uuid.uuid4().hex
        phan = []
        for ten, gia_tri in (("chat_id", self.chat_id),
                             ("caption", chu_thich[:1024]),
                             ("parse_mode", "HTML")):
            phan.append(f"--{ranh}\r\nContent-Disposition: form-data; "
                        f"name=\"{ten}\"\r\n\r\n{gia_tri}\r\n".encode("utf-8"))
        phan.append(f"--{ranh}\r\nContent-Disposition: form-data; "
                    f"name=\"photo\"; filename=\"canh_bao.jpg\"\r\n"
                    f"Content-Type: image/jpeg\r\n\r\n".encode("utf-8"))
        phan.append(bytes(jpeg))
        phan.append(f"\r\n--{ranh}--\r\n".encode("utf-8"))
        return self._goi("sendPhoto", b"".join(phan),
                         f"multipart/form-data; boundary={ranh}")

    def lay_cap_nhat(self):
        return self._goi("getUpdates", b"", "application/x-www-form-urlencoded")


TRANG_XEM = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Camera pan-tilt</title>
<style>
 :root{--nen:#0f1115;--the:#1a1d24;--chu:#e8eaef;--mo:#9aa1ad;--do:#ff4d4f;--xanh:#3ecf8e;--vang:#f5b041}
 *{box-sizing:border-box}
 body{margin:0;background:var(--nen);color:var(--chu);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 header{padding:12px 16px;display:flex;align-items:center;gap:10px}
 h1{font-size:17px;margin:0;font-weight:600}
 .cham{width:10px;height:10px;border-radius:50%;background:var(--mo)}
 main{padding:0 16px 24px;max-width:900px;margin:0 auto}
 .khung{background:#000;border-radius:10px;overflow:hidden}
 .khung img{display:block;width:100%;height:auto}
 .bang{margin-top:12px;background:var(--the);border-radius:10px;padding:12px 14px}
 .dong{display:flex;justify-content:space-between;gap:12px;padding:4px 0;border-bottom:1px solid #262a33}
 .dong:last-child{border-bottom:0}
 .nhan{color:var(--mo)}
 .tt{font-weight:600}
 .tt.BAM{color:var(--do)} .tt.BAN_NGHI{color:var(--xanh)} .tt.CHO_IFF,.tt.BAN_GIAO{color:var(--vang)}
 .nut{display:inline-block;margin-top:12px;padding:10px 14px;border-radius:8px;background:#2a2f3a;color:var(--chu);text-decoration:none}
 .loi{color:var(--vang);font-size:13px;margin-top:8px;min-height:1em}
</style></head><body>
<header><span class="cham" id="cham"></span><h1>Camera pan-tilt trực tiếp</h1></header>
<main>
 <div class="khung"><img id="hinh" src="stream?k=__KHOA__" alt="Luồng camera"></div>
 <div class="bang">
  <div class="dong"><span class="nhan">Trạng thái</span><span class="tt" id="tt">…</span></div>
  <div class="dong"><span class="nhan">IFF</span><span id="iff">…</span></div>
  <div class="dong"><span class="nhan">LiDAR</span><span id="ld">…</span></div>
  <div class="dong"><span class="nhan">Góc servo</span><span id="goc">…</span></div>
  <div class="dong"><span class="nhan">Cảnh báo gần nhất</span><span id="cb">chưa có</span></div>
 </div>
 <a class="nut" href="anh.jpg?k=__KHOA__" target="_blank">Mở ảnh chụp hiện tại</a>
 <div class="loi" id="loi"></div>
</main>
<script>
const K="__KHOA__";
const TEN={CHO:"Chờ",CHO_IFF:"Đang hỏi IFF",BAN_NGHI:"Bạn, camera nghỉ",BAN_GIAO:"Đang quay theo LiDAR",BAM:"ĐANG BÁM MỤC TIÊU THÙ",NGHI:"Về góc nghỉ"};
async function cap_nhat(){
 try{
  const r=await fetch("trang_thai.json?k="+K,{cache:"no-store"});
  const d=await r.json();
  const tt=document.getElementById("tt");
  tt.textContent=TEN[d.trang_thai]||d.trang_thai; tt.className="tt "+d.trang_thai;
  document.getElementById("iff").textContent=d.iff||"—";
  document.getElementById("ld").textContent=d.lidar||"—";
  document.getElementById("goc").textContent=d.goc||"—";
  document.getElementById("cb").textContent=d.canh_bao_cuoi||"chưa có";
  document.getElementById("cham").style.background=d.trang_thai==="BAM"?"var(--do)":"var(--xanh)";
  document.getElementById("loi").textContent="";
 }catch(e){document.getElementById("loi").textContent="Mất kết nối với laptop, đang thử lại…";
  document.getElementById("cham").style.background="var(--mo)";}
}
setInterval(cap_nhat,1000); cap_nhat();
document.addEventListener("visibilitychange",()=>{if(!document.hidden){
 const h=document.getElementById("hinh"); h.src="stream?k="+K+"&t="+Date.now();}});
</script></body></html>
"""


class MayChuXem:


    def __init__(self, cong, khoa, fps=12, chat_luong=70):
        self.cong = int(cong)
        self.khoa = str(khoa)
        self.chu_ky = 1.0 / max(1.0, float(fps))
        self.chat_luong = int(chat_luong)
        self._khung = None                                                
        self._so_khung = 0
        self._jpeg = None                                             
        self._so_jpeg = -1
        self._khoa_jpeg = threading.Lock()
        self.trang_thai = {}                                               
        self.dung = False
        self._srv = None

    def dat_khung(self, khung):
        self._khung = khung
        self._so_khung += 1

    def dat_trang_thai(self, tt):
        self.trang_thai = tt

    def jpeg_moi_nhat(self):
        with self._khoa_jpeg:
            if self._so_jpeg != self._so_khung and self._khung is not None:
                ok, buf = cv2.imencode(".jpg", self._khung,
                                       [cv2.IMWRITE_JPEG_QUALITY, self.chat_luong])
                if ok:
                    self._jpeg = buf.tobytes()
                    self._so_jpeg = self._so_khung
            return self._jpeg

    def bat_dau(self):
        may_chu = self

        class XuLy(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):                                        
                pass

            def _dung_khoa(self, q):
                k = q.get("k", [""])[0]
                return secrets.compare_digest(k.encode(), may_chu.khoa.encode())

            def _tra(self, ma, kieu, noi_dung):
                self.send_response(ma)
                self.send_header("Content-Type", kieu)
                self.send_header("Content-Length", str(len(noi_dung)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(noi_dung)

            def do_GET(self):
                url = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(url.query)
                if not self._dung_khoa(q):
                    self._tra(403, "text/plain; charset=utf-8",
                              "Sai hoặc thiếu khóa xem.".encode("utf-8"))
                    return
                duong = url.path.rstrip("/") or "/"
                if duong == "/":
                    trang = TRANG_XEM.replace("__KHOA__",
                                              urllib.parse.quote(may_chu.khoa))
                    self._tra(200, "text/html; charset=utf-8",
                              trang.encode("utf-8"))
                elif duong == "/trang_thai.json":
                    self._tra(200, "application/json; charset=utf-8",
                              json.dumps(may_chu.trang_thai,
                                         ensure_ascii=False).encode("utf-8"))
                elif duong == "/anh.jpg":
                    j = may_chu.jpeg_moi_nhat()
                    if j is None:
                        self._tra(503, "text/plain; charset=utf-8",
                                  "Chưa có khung hình.".encode("utf-8"))
                    else:
                        self._tra(200, "image/jpeg", j)
                elif duong == "/stream":
                    self._phat_mjpeg()
                else:
                    self._tra(404, "text/plain; charset=utf-8", b"404")

            def _phat_mjpeg(self):
                self.send_response(200)
                self.send_header("Content-Type",
                                 "multipart/x-mixed-replace; boundary=khung")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.end_headers()
                so_cuoi = -1
                try:
                    while not may_chu.dung:
                        t0 = time.perf_counter()
                        j = may_chu.jpeg_moi_nhat()
                        if j is not None and may_chu._so_jpeg != so_cuoi:
                            so_cuoi = may_chu._so_jpeg
                            self.wfile.write(
                                b"--khung\r\nContent-Type: image/jpeg\r\n"
                                + f"Content-Length: {len(j)}\r\n\r\n".encode()
                                + j + b"\r\n")
                            self.wfile.flush()
                        du = may_chu.chu_ky - (time.perf_counter() - t0)
                        if du > 0:
                            time.sleep(du)
                except (BrokenPipeError, ConnectionResetError,
                        ConnectionAbortedError, OSError):
                    pass                                               
                self.close_connection = True

        self._srv = ThreadingHTTPServer(("0.0.0.0", self.cong), XuLy)
        self._srv.daemon_threads = True
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()

    def dong(self):
        self.dung = True
        if self._srv is not None:
            try:
                self._srv.shutdown()
                self._srv.server_close()
            except Exception:
                pass


def ve_anh_canh_bao(khung, bbox, dong_chu):
    anh = khung.copy()
    if bbox is not None:
        x1, y1, x2, y2 = [int(z) for z in bbox]
        cv2.rectangle(anh, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(anh, "THU", (x1, max(18, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
    h = anh.shape[0]
    cao = 24 * len(dong_chu) + 10
    lop = anh.copy()
    cv2.rectangle(lop, (0, h - cao), (anh.shape[1], h), (0, 0, 0), -1)
    anh = cv2.addWeighted(lop, 0.55, anh, 0.45, 0.0)
    for i, s in enumerate(dong_chu):
        cv2.putText(anh, s, (10, h - cao + 26 + 24 * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return anh


def so_vn(x, chu_so=2):
    return f"{x:.{chu_so}f}".replace(".", ",")


class BoCanhBao:


    def __init__(self, cfg, cong_web=None):
        self.cfg = cfg
        self.khoang_nghi_s = float(cfg.get("khoang_nghi_giua_hai_tin_s", 20))
        self.bao_khi_roi = bool(cfg.get("bao_khi_muc_tieu_roi_vung", True))
        self.so_lan_thu = int(cfg.get("so_lan_thu_lai", 3))

        token = str(cfg.get("bot_token", "")).strip()
        chat = str(cfg.get("chat_id", "")).strip()
        self.tg = GuiTelegram(token, chat) if token and chat else None
        if self.tg is None:
            print("[!] Chua dien bot_token hoac chat_id. Chi bat trang xem "
                  "camera, khong gui Telegram.", flush=True)

        self.web = None
        self.link_xem = None
        cong = cong_web if cong_web is not None else cfg.get("cong_web", 8780)
        if cong and int(cong) > 0:
            try:
                self.web = MayChuXem(int(cong), cfg["khoa_xem"],
                                     cfg.get("fps_web", 12),
                                     cfg.get("chat_luong_jpeg", 70))
                self.web.bat_dau()
                ip = str(cfg.get("dia_chi_ip", "")).strip() or ip_mang_noi_bo()
                self.link_xem = (f"http://{ip}:{int(cong)}/?k="
                                 f"{urllib.parse.quote(cfg['khoa_xem'])}")
                print(f"[i] Trang xem camera: {self.link_xem}", flush=True)
            except OSError as e:
                print(f"[!] Khong mo duoc cong {cong} cho trang xem: {e}",
                      flush=True)
                self.web = None

        self._hang = queue.Queue(maxsize=8)
        self._da_bao = {}                                               
        self._t_tin_cuoi = -1e9
        self._dang_bam = None                                             
        self._t_mat = None
        self.so_tin_da_gui = 0
        self.su_kien = []
        self.tin_cuoi = ""
        self.loi_cuoi = ""
        self.dung = False
        threading.Thread(target=self._chay, daemon=True).start()

    def bao_thu(self, ma_vet, khung, bbox, thong_tin):

        t = time.monotonic()
        khoa = ma_vet if ma_vet is not None else "camera"
        self._t_mat = None
        if khoa in self._da_bao:
            self._dang_bam = khoa
            return False
        if t - self._t_tin_cuoi < self.khoang_nghi_s:
            return False
        if khung is None:
            return False
        self._da_bao[khoa] = t
        self._dang_bam = khoa
        self._t_tin_cuoi = t
        if len(self._da_bao) > 256:
            self._da_bao = dict(list(self._da_bao.items())[-64:])
        self._dat_viec(("thu", ma_vet, khung.copy(),
                        None if bbox is None else tuple(int(z) for z in bbox),
                        dict(thong_tin), datetime.now(), time.time()))
        return True

    def khong_bam(self):
        if self._dang_bam is None:
            return
        t = time.monotonic()
        if self._t_mat is None:
            self._t_mat = t
            return
        if t - self._t_mat >= 3.0:
            ma = self._dang_bam
            t_dau = self._da_bao.pop(ma, t)
            self._dang_bam = None
            self._t_mat = None
            if self.bao_khi_roi and self.tg is not None:
                self._dat_viec(("roi", ma, t - t_dau - 3.0))

    def mo_ta(self):
        if self.tg is None and self.web is None:
            return None
        phan = []
        if self.tg is not None:
            phan.append(f"TG {self.so_tin_da_gui} tin")
            if self.loi_cuoi:
                phan.append("LOI MANG")
        if self.web is not None:
            phan.append(f"web :{self.web.cong}")
        return "CANH BAO " + " ".join(phan)

    def cap_nhat_web(self, khung_hien_thi, trang_thai):
        if self.web is not None:
            if khung_hien_thi is not None:
                self.web.dat_khung(khung_hien_thi)
            trang_thai["canh_bao_cuoi"] = self.tin_cuoi
            self.web.dat_trang_thai(trang_thai)

    def dong(self):
        self.dung = True
        if self.web is not None:
            self.web.dong()

    def _dat_viec(self, viec):
        try:
            self._hang.put_nowait(viec)
        except queue.Full:
            try:
                self._hang.get_nowait()
                self._hang.put_nowait(viec)
            except Exception:
                pass

    def _chay(self):
        while not self.dung:
            try:
                viec = self._hang.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                if viec[0] == "thu":
                    t_dat = viec[-1]
                    kq = self._gui_thu(*viec[1:-1])
                    self._ghi_nhan("canh_bao", viec[1], t_dat, kq)
                elif viec[0] == "roi":
                    t_dat = time.time()
                    kq = self._gui_roi(*viec[1:])
                    self._ghi_nhan("roi_vung", viec[1], t_dat, kq)
            except Exception as e:                                            
                self.loi_cuoi = str(e)
                print(f"[!] Canh bao: loi khong mong doi: {e}", flush=True)

    def _ghi_nhan(self, loai, ma_vet, t_dat, kq):
        ok, kieu, so_lan, t_may_chu = kq if kq else (False, "", 0, None)
        self.su_kien.append({
            "loai": loai, "ma_vet": "" if ma_vet is None else ma_vet,
            "t_dat": t_dat, "t_xong": time.time(), "ok": int(bool(ok)),
            "kieu": kieu, "so_lan_goi": so_lan,
            "t_may_chu": "" if t_may_chu is None else t_may_chu,
            "loi": self.loi_cuoi,
        })

    def ghi_su_kien(self, duong_dan):
        cot = ["loai", "ma_vet", "t_dat", "t_xong", "ok", "kieu",
               "so_lan_goi", "t_may_chu", "loi"]
        with open(duong_dan, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cot)
            w.writeheader()
            for e in list(self.su_kien):
                w.writerow(e)

    def _thu_lai(self, ham, *a):
        for lan in range(self.so_lan_thu):
            try:
                kq = ham(*a)
                self.loi_cuoi = ""
                return True, lan + 1, kq
            except Exception as e:
                self.loi_cuoi = str(e)
                print(f"[!] Gui Telegram that bai lan {lan + 1}: {e}",
                      flush=True)
                time.sleep(2.0 * (lan + 1))
        return False, self.so_lan_thu, None

    def _gui_thu(self, ma_vet, khung, bbox, tt, luc):
        gio = luc.strftime("%H:%M:%S %d/%m/%Y")
        dong_anh = [f"XAM NHAP  {gio}"]
        dong = ["⚠️ <b>CẢNH BÁO: PHÁT HIỆN KẺ XÂM NHẬP</b>",
                f"Thời điểm: {gio}"]
        if tt.get("thu_nghiem"):
            dong.insert(0, "🧪 <b>TIN THỬ</b>")
        if self.link_xem:
            dong.append(f'<a href="{html.escape(self.link_xem)}">'
                        f"Xem camera trực tiếp</a>")
        chu = "\n".join(dong)
        self.tin_cuoi = gio

        print("[CANH BAO] Muc tieu THU"
              + (f" vet {ma_vet}" if ma_vet is not None else "")
              + ", dang gui Telegram...", flush=True)
        if self.tg is None:
            return (False, "khong_telegram", 0, None)
        anh = ve_anh_canh_bao(khung, bbox, dong_anh)
        ok, buf = cv2.imencode(".jpg", anh, [cv2.IMWRITE_JPEG_QUALITY, 85])
        so_lan = 0
        if ok:
            thanh, so_lan, kq = self._thu_lai(self.tg.gui_anh, buf.tobytes(), chu)
            if thanh:
                self.so_tin_da_gui += 1
                print("[CANH BAO] Da gui anh canh bao.", flush=True)
                return (True, "anh", so_lan, (kq or {}).get("date"))
        thanh, n2, kq = self._thu_lai(self.tg.gui_chu, chu)
        if thanh:
            self.so_tin_da_gui += 1
            print("[CANH BAO] Gui anh that bai, da gui tin chu thay the.",
                  flush=True)
        return (thanh, "chu", so_lan + n2, (kq or {}).get("date"))

    def _gui_roi(self, ma_vet, thoi_gian_s):
        ma = f"#{ma_vet} " if ma_vet not in (None, "camera") else ""
        chu = (f"Mục tiêu {ma}đã rời vùng quan sát sau khoảng "
               f"{max(0, round(thoi_gian_s))} giây bám. Hệ thống trở về trạng thái chờ.")
        thanh, so_lan, kq = self._thu_lai(self.tg.gui_chu, chu)
        if thanh:
            self.so_tin_da_gui += 1
        return (thanh, "chu", so_lan, (kq or {}).get("date"))


def tao_bo_canh_bao(duong_dan_cfg, cong_web=None):
    cfg = doc_bi_mat(duong_dan_cfg)
    if cfg is None:
        print(f"[!] Chua co {duong_dan_cfg}. Sao chep canh_bao_bi_mat.mau.json "
              f"thanh ten do va dien khoa bot. Tam chay khong canh bao.",
              flush=True)
        return None
    return BoCanhBao(cfg, cong_web)
