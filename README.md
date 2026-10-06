# NCKH — LiDAR, camera/pan-tilt và IFF

Hệ thống nguyên mẫu kết hợp LiDAR phát hiện chuyển động, IFF xác thực thẻ và camera/pan-tilt bám mục tiêu. Kết quả IFF **BẠN** giữ cơ cấu chờ; **THÙ** cho phép camera bám. Hỗ trợ cảnh báo Telegram tùy chọn.

## Thành phần

- `Lidar/`: chương trình LiDAR, giao diện web và firmware ESP32-S3.
- `CameraPantilt/`: camera, điều khiển pan-tilt, mô hình và firmware Arduino Uno.
- `IFF/`: firmware trạm ESP32-C3 và thẻ RP2040 Zero.
- `CAI_DAT.ps1`, `requirements.txt`: cài môi trường Python.

## Phần cứng

| Khối | Thiết bị | Kết nối chính |
| --- | --- | --- |
| LiDAR | YDLidar S2 Pro + ESP32-S3 | TX → GPIO16; M-C → GPIO4; PC qua USB–UART |
| Pan-tilt | Camera USB + Arduino Uno | Servo pan D4, tilt D3; còi D8 |
| Trạm IFF | ESP32-C3 + NRF24L01 + GC9A01A | SPI SCK/MOSI/MISO: 4/6/10; NRF CE/CSN: 0/1; TFT CS/DC/RST: 7/5/3 |
| Thẻ IFF | RP2040 Zero + NRF24L01 | SPI SCK/MOSI/MISO: GP2/GP3/GP4; NRF CE/CSN: GP8/GP5 |

Nối chung GND, cấp NRF24L01 **3,3 V** và dùng nguồn riêng cho servo. Bật **USB CDC On Boot** trên ESP32-C3.

Nạp các tệp `.ino` bằng Arduino IDE, giữ tệp `.h` cùng thư mục. Cài thư viện: **Servo** cho Uno; **RF24, Crypto** cho hai bo IFF; thêm **Adafruit GFX, GC9A01A, BusIO** cho trạm. Core đã kiểm tra: ESP32 3.3.11, Arduino AVR 1.8.8, RP2040 của Earle Philhower 6.1.0.

## Cài đặt và chạy

Dùng **Windows, Python 3.12 x64** có lệnh `py`. Tải ZIP hoặc clone kho, mở PowerShell tại thư mục gốc:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\CAI_DAT.ps1
```

Xem cổng trong **Device Manager**. Cổng mẫu: LiDAR **COM9**, pan-tilt **COM13**, trạm IFF **COM18**, thẻ **COM15**; camera **1**. Đổi tham số bên dưới theo máy của bạn.

Dừng bản đang chạy ở C trước khi dùng chung camera/cổng COM. Khởi động trạm và thẻ IFF, rồi mở hai cửa sổ PowerShell tại thư mục gốc.

**Cửa sổ 1 — LiDAR:**

```powershell
.\Lidar\CHAY_LIDAR.cmd COM9
```

Mở giao diện tại <http://127.0.0.1:8770>, chờ có dữ liệu.

**Cửa sổ 2 — camera/pan-tilt và IFF:**

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\CameraPantilt\CHAY_CAMERA_PANTILT.ps1 -Port COM13 -Cam 1 -Iff COM18 -The COM15
```

**Dừng:** nhấn `q` trong cửa sổ camera, sau đó `Ctrl+C` ở cửa sổ LiDAR. Nếu cổng COM bị bận, đóng Serial Monitor hoặc chương trình đang giữ cổng.

## Khóa và cấu hình

- Hai bo IFF phải dùng **cùng khóa**. Kho có khóa mẫu công khai `iff_key.example.h`. Muốn dùng khóa riêng, tạo `iff_key.local.h` trong cả hai thư mục firmware và nạp lại **cả trạm lẫn thẻ**. Không tải khóa riêng lên GitHub.
- Telegram: sao chép `CameraPantilt/canh_bao_bi_mat.mau.json` thành `canh_bao_bi_mat.json` cùng thư mục, điền `bot_token` và `chat_id`. Không cấu hình thì bỏ qua Telegram; không công khai tệp riêng hoặc URL có khóa xem.
- Giữ nguyên các tệp trong `CameraPantilt/mo_hinh/` để chương trình tìm được mô hình.

Đã kiểm tra phần mềm và biên dịch firmware; **chưa kiểm thử phối hợp trên phần cứng**. Bản nguồn ở C được giữ nguyên. Phiên bản dùng cho báo cáo: [bao-cao-2026-10-06-phan-mem](https://github.com/im-deltax/NCKH/releases/tag/bao-cao-2026-10-06-phan-mem).

Mô hình dùng giấy phép AGPL-3.0 của Ultralytics; các thư viện giữ giấy phép tương ứng. Kho chưa có giấy phép riêng cho mã dự án.
