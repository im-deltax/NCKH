# NCKH — LiDAR, camera/pan-tilt và IFF

Kho mã vận hành của hệ thống nghiên cứu tích hợp LiDAR YDLidar S2 Pro, trạm IFF ESP32-C3, thẻ IFF RP2040 Zero, camera USB và cơ cấu pan-tilt Arduino Uno. LiDAR phát hiện vật chuyển động trong vùng, trạm hỏi thẻ IFF; kết quả BẠN giữ cơ cấu ở trạng thái chờ, kết quả THÙ cho phép camera nhận dạng và pan-tilt bám mục tiêu. Khối cảnh báo có thể gửi ảnh qua Telegram và cung cấp trang xem camera trong mạng nội bộ.

Gói giữ cấu trúc và thuật toán của bản đang chạy ở C. Các sửa đổi phục vụ công bố gồm bỏ ghi chú/chuỗi mô tả trong mã, tách khóa IFF sang tệp mẫu hoặc tệp riêng, thêm tham số cổng vào script khởi động và kiểm tra lỗi cài đặt. Bản nguồn ở C không được sửa. Đây là nguyên mẫu nghiên cứu; nhãn BẠN/THÙ là kết quả xử lý IFF của nguyên mẫu.

## Cấu trúc

```text
NCKH_GITHUB/
  README.md
  .gitignore
  requirements.txt
  CAI_DAT.ps1
  Lidar/
    CHAY_LIDAR.cmd
    chuong_trinh/
      lidar_test.py
      lidar_core_test.py
      radar_hud_test.html
      requirements.txt
    firmware/lidar_uart_bridge/lidar_uart_bridge.ino
  CameraPantilt/
    CHAY_CAMERA_PANTILT.ps1
    canh_bao_bi_mat.mau.json
    arduino_pantilt/arduino_pantilt.ino
    pantilt/
    mo_hinh/
      best.pt
      best_ov640_openvino_model/
        best.xml
        best.bin
        metadata.yaml
    log/.gitkeep
  IFF/
    tram_esp32c3/
      tram_esp32c3.ino
      iff_common.h
      iff_key.example.h
      trang_thai.h
      giao_dien.h
      font_viet.h
    the_rp2040/
      the_rp2040.ino
      iff_common.h
      iff_key.example.h
```

`lidar_test.py`, `lidar_core_test.py` và `radar_hud_test.html` là mã vận hành hiện tại, dù tên có chữ `test`. `pantilt/track.py` import trực tiếp `thuc_nghiem.py`, nên tệp này vẫn cần có để khởi động. Các mô-đun điều khiển, hình học, Kalman, nguồn LiDAR/IFF và cảnh báo được giữ nguyên. Không kèm bản thảo, MATLAB/Simulink, số liệu đo, đồ thị, công cụ phân tích, môi trường ảo hoặc cấu hình riêng.

## Phần cứng và nối dây

Các chân dưới đây được đối chiếu với firmware trong kho. Nguồn các khối phải nối chung GND. Không cấp 5 V vào NRF24L01; servo dùng nguồn riêng đủ dòng theo phần cứng thực tế.

### LiDAR và ESP32-S3

| Tín hiệu | Kết nối |
| --- | --- |
| S2 Pro 5 V | Nguồn 5 V riêng |
| S2 Pro TX | ESP32-S3 GPIO16 |
| S2 Pro M-C | ESP32-S3 GPIO4 |
| S2 Pro GND | GND nguồn và ESP32-S3 |
| ESP32-S3 GPIO43/GPIO44 | UART0 TX/RX qua cầu USB–UART CH343 trên bo |

Firmware nhận LiDAR ở 115200 baud, truyền lên PC ở 921600 baud. Chương trình Python mặc định dùng cùng tốc độ 921600. PWM M-C là 10 kHz, script đặt duty 40% và bán kính làm việc 70 cm. Dùng cổng USB–UART của bo tương ứng UART0; firmware không truyền dữ liệu qua USB CDC gốc.

### Camera và pan-tilt Arduino Uno

| Tín hiệu | Chân |
| --- | --- |
| Servo pan | D4 |
| Servo tilt | D3 |
| LED trên bo | D13 |
| Còi thụ động | D8 |
| Camera USB | Cổng USB máy tính |

Serial pan-tilt là 115200 baud. Không lấy nguồn hai servo từ chân 5 V của Uno. Giới hạn đang giữ trong mã là pan ±70°, tilt ±55°; các hằng hiệu chuẩn phù hợp với cơ cấu gốc. Khi đổi camera hoặc cơ cấu, phải hiệu chuẩn lại các tham số trong `pantilt/cauhinh.py` và firmware trước khi đánh giá độ chính xác.

### Trạm ESP32-C3, NRF24L01 và GC9A01A

| Tín hiệu | GPIO ESP32-C3 |
| --- | ---: |
| SPI SCK, dùng chung TFT/NRF | 4 |
| SPI MOSI, dùng chung TFT/NRF | 6 |
| NRF MISO | 10 |
| NRF CE / CSN | 0 / 1 |
| TFT CS / DC / RST | 7 / 5 / 3 |
| LED1 / LED2 | 21 / 20 |
| Còi active qua transistor | 8 |

GC9A01A là màn tròn 240 × 240. Bật **USB CDC On Boot** trên ESP32-C3 để giao tiếp PC qua USB gốc và tránh dùng UART0 đang nối LED. Còi active 5 V: GPIO8 qua điện trở 1 kΩ vào B của NPN; E xuống GND; C nối cực âm còi; cực dương nối 5 V. Nếu còi điện từ, thêm diode bảo vệ theo mạch thực tế.

### Thẻ RP2040 Zero và NRF24L01

| Tín hiệu | GPIO RP2040 |
| --- | ---: |
| NRF SCK / MOSI / MISO | GP2 / GP3 / GP4 |
| NRF CSN / CE | GP5 / GP8 |
| LED1–LED5 | GP6, GP7, GP9, GP10, GP11 |

Mỗi LED nối qua điện trở hạn dòng, cathode xuống GND. NRF dùng 3,3 V; đặt tụ 100 nF, 10 µF và 100 µF gần nguồn NRF theo bố trí nguyên mẫu. Nếu dùng bản PA+LNA, dùng nguồn 3,3 V riêng đủ dòng. Serial trạm và thẻ là 115200 baud.

## Cài đặt Python trên Windows

Cài Python **3.12 x64** có Python Launcher (`py`) và Git. Camera dùng backend DirectShow trên Windows. Có thể giải nén hoặc clone kho vào đường dẫn bất kỳ; các script tự tìm thư mục của mình.

Mở PowerShell ở thư mục gốc kho:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\CAI_DAT.ps1
.\.venv\Scripts\python.exe -m pip check
```

Script tạo `.venv` trong chính kho, rồi cài `requirements.txt`. Các phiên bản trực tiếp được lấy từ môi trường vận hành đã kiểm tra: Ultralytics 8.4.140, OpenCV 5.0.0.93, NumPy 2.4.2, SciPy 1.17.1, pyserial 3.5, OpenVINO 2026.3.1, PyTorch 2.14.0 và torchvision 0.29.0. Cài đặt cần Internet và dung lượng cho PyTorch cùng các phụ thuộc. Thư viện phân tích/vẽ hình không được yêu cầu trực tiếp trong gói vận hành; trình quản lý gói vẫn có thể cài chúng theo phụ thuộc của Ultralytics.

Mô hình mặc định là `CameraPantilt/mo_hinh/best.pt`; backend mặc định OpenVINO dùng trọn bộ `best.xml`, `best.bin`, `metadata.yaml` trong thư mục `best_ov640_openvino_model`. Không đổi tên hoặc bỏ một tệp trong bộ này. Nếu đổi `--imgsz`, chương trình có thể xuất thêm mô hình OpenVINO tại lần chạy đầu. Khi chạy lệnh Python trực tiếp, đặt thư mục làm việc ở `CameraPantilt`; script khởi động đã làm việc này.

## Cài thư viện và nạp firmware

Mở từng `.ino` trong thư mục cùng tên, giữ các `.h` cạnh sketch. Các phiên bản sau có trên máy khi chuẩn bị gói; kết quả biên dịch được ghi trong mục kiểm tra bên dưới.

| Khối | Board/core | Thư viện |
| --- | --- | --- |
| LiDAR | ESP32S3 Dev Module, esp32:esp32 3.3.11 | HardwareSerial trong core |
| Pan-tilt | Arduino Uno, arduino:avr 1.8.8 | Servo 1.3.0 |
| Trạm IFF | ESP32C3 Dev Module, esp32:esp32 3.3.11; USB CDC On Boot bật | RF24 1.6.2, Crypto 0.4.0, Adafruit GFX 1.12.6, Adafruit GC9A01A 1.1.1, Adafruit BusIO 1.17.4 |
| Thẻ IFF | Waveshare RP2040 Zero, rp2040:rp2040 6.1.0 của Earle F. Philhower | RF24 1.6.2, Crypto 0.4.0 |

Chọn đúng cổng từng bo rồi nạp sketch tương ứng. Không mở Serial Monitor đồng thời với chương trình Python đang sử dụng cùng cổng.

## Khóa IFF và cấu hình riêng

Hai firmware dùng cùng khóa mẫu công khai trong `iff_key.example.h`, nên có thể biên dịch ngay mà không tạo thêm cấu hình. Khóa của bản nguồn C không được sao chép vào gói công bố. Muốn dùng khóa riêng, sao chép tệp mẫu thành `iff_key.local.h` trong **cả hai** thư mục sketch, điền cùng 16 byte ngẫu nhiên và nạp lại cả trạm lẫn thẻ. Firmware ưu tiên tệp `.local.h` khi có. Tệp riêng đã được `.gitignore` loại trừ. Không dùng khóa mẫu công khai khi cần xác thực bí mật.

**Trạm và thẻ phải dùng cùng khóa.** Nạp chỉ một phía bằng bản GitHub trong khi phía kia vẫn chạy khóa cũ sẽ gây lỗi xác thực. Để giữ hệ thống ở C, giữ firmware hiện đang nạp trên bo; trước khi thay firmware, lưu bản và khóa riêng ở ngoài kho để có thể khôi phục. Chạy Python ở D với firmware cũ không tự đổi khóa trong bo.

### Cảnh báo Telegram (tùy chọn)

```powershell
Copy-Item .\CameraPantilt\canh_bao_bi_mat.mau.json .\CameraPantilt\canh_bao_bi_mat.json
notepad .\CameraPantilt\canh_bao_bi_mat.json
```

Điền `bot_token` lấy từ BotFather và `chat_id` của cuộc trò chuyện nhận tin; bot phải có quyền gửi tin tại đó. `dia_chi_ip` có thể để trống để chương trình chọn IP nội bộ; `cong_web` mặc định 8780. `khoa_xem` trống sẽ được chương trình sinh và ghi vào tệp cấu hình riêng. Giữ bí mật URL có khóa xem. Không commit tệp này hoặc log chứa thông tin cảnh báo. Nếu thiếu tệp riêng, hệ thống vẫn chạy và bỏ qua cảnh báo Telegram.

## Cổng COM và thứ tự chạy

Kiểm tra cổng bằng Device Manager hoặc:

```powershell
.\.venv\Scripts\python.exe -m serial.tools.list_ports
```

Mẫu cổng của cơ cấu gốc: LiDAR COM9, pan-tilt COM13, trạm IFF COM18, thẻ COM15, camera index 1. Máy khác phải chọn cổng thực tế; không cần sửa mã nguồn để đổi cổng.

Trước khi chạy bản GitHub, dừng các chương trình ở C đang giữ camera, cổng COM hoặc cổng web. Khởi động trạm và thẻ IFF. Mở hai cửa sổ PowerShell từ thư mục gốc kho.

**Cửa sổ 1 — LiDAR và web:**

```powershell
.\Lidar\CHAY_LIDAR.cmd COM9
```

Chờ [giao diện LiDAR](http://127.0.0.1:8770) có dữ liệu, sau đó mở **cửa sổ 2 — camera, pan-tilt và IFF:**

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\CameraPantilt\CHAY_CAMERA_PANTILT.ps1 -Port COM13 -Cam 1 -Iff COM18 -The COM15
```

Gọi script không có tham số vẫn dùng các cổng mẫu trên. Camera mặc định chạy chế độ `PRED`, ghép SSE LiDAR tại `http://127.0.0.1:8770/stream`. Để chạy trực tiếp với tham số riêng từ thư mục gốc:

```powershell
Set-Location .\CameraPantilt
..\.venv\Scripts\python.exe -X utf8 -m pantilt.track --port COM13 --cam 1 --che-do PRED --lidar http://127.0.0.1:8770/stream --iff COM18 --the COM15 --canh-bao --ten CHAY_HE_THONG
```

Nhấn `b` trong cửa sổ **Pan-tilt tracking** để thẻ trả lời hợp lệ, `t` để thẻ im lặng. Đây là chế độ thử nhanh của thẻ, không thay thế kiểm thử xác thực. Trang camera khi bật cảnh báo dùng cổng 8780; chương trình in URL có khóa xem. Điện thoại cần cùng mạng nội bộ với PC.

## Dừng và xử lý lỗi

Nhấn `q` trong cửa sổ **Pan-tilt tracking** để kết thúc, đóng liên kết và ghi log. Sau đó nhấn `Ctrl+C` ở cửa sổ LiDAR; script CMD có thể đợi một phím trước khi đóng. Không rút nguồn hoặc tháo cáp khi cơ cấu đang chuyển động.

Nếu không mở được cổng COM, kiểm tra Device Manager, cáp dữ liệu, driver và đóng Serial Monitor/chương trình khác đang giữ cổng. Nếu camera không mở, đóng ứng dụng đang dùng webcam và thử `-Cam 0` hoặc `-Cam 2`. Nếu không thấy mô hình, chạy qua script hoặc chuyển vào `CameraPantilt` trước khi gọi `python -m pantilt.track`. Nếu IFF báo `BAD_MAC`, kiểm tra hai bo đã nạp cùng khóa. Nếu thiếu thư viện, chạy lại cài đặt và xem lỗi đầu tiên; script dừng khi pip thất bại.

## Kiểm tra và phiên bản trích dẫn

Kiểm tra ngày 06/10/2026:

- 351 tệp nguồn/tài nguyên ở C giữ nguyên SHA-256; sao chép ban đầu khớp SHA-256 từng tệp được chọn.
- Rà 55 tệp nguồn; bỏ 3.148 ghi chú/chuỗi mô tả trong phần mã đưa lên kho. Cây cú pháp Python sau khi bỏ mô tả, token C/C++ ngoài phần tách khóa và token JavaScript vẫn giữ nguyên.
- 14 tệp Python qua kiểm tra cú pháp; script PowerShell qua parser; JavaScript qua kiểm tra cú pháp và đối chiếu token.
- Bốn firmware LiDAR, pan-tilt, trạm IFF và thẻ IFF đã biên dịch. Pan-tilt được kiểm tra với Servo 1.3.0. Môi trường ESP32-S3 trên máy thiếu driver gọi `xtensa-esp32s3-elf-g++`; kiểm tra sử dụng driver đúng đích `xtensa-esp32s3-elf-gcc-14.2.0` có sẵn cho các bước biên dịch/link, không sửa sketch hoặc core đã cài. Nếu máy mới gặp lỗi công cụ tương tự, cài lại đầy đủ core ESP32 và toolchain tương ứng.
- Pip giải được phụ thuộc từ chỉ mục; đã cài đủ thư viện trong môi trường Python 3.12 mới, tách khỏi môi trường bản C. `pip check` không phát hiện phụ thuộc lỗi. Các mô-đun và lệnh `--help` của gói D chạy được bằng môi trường mới.
- Mô hình PyTorch/OpenVINO đã nạp và suy luận CPU trên ảnh tổng hợp từ gói D bằng môi trường mới. HTTP của giao diện LiDAR và mô-đun camera nhận được gói SSE tổng hợp. Các kiểm tra này xác nhận tài nguyên và liên kết phần mềm, không đo độ chính xác nhận dạng hoặc khả năng bám phần cứng.
- Chưa thử phối hợp trên phần cứng: máy không nhận cổng COM tại thời điểm chuẩn bị gói. Chưa nạp firmware mới, chưa đo độ trễ, khả năng bám hoặc Telegram thực tế.

Khi nối phần cứng và dừng bản C, cần xác nhận lần lượt: LiDAR có dữ liệu; trạm/thẻ hỏi đáp BẠN; chế độ thẻ im lặng chuyển THÙ; camera/pan-tilt bám; vật rời vùng trở về chờ; cảnh báo Telegram gửi được nếu đã cấu hình; phím `q` và `Ctrl+C` giải phóng các liên kết. Không coi kiểm tra cú pháp hoặc ảnh tổng hợp là kết quả đo phần cứng.

Tag cục bộ cho bản chuẩn bị này: `bao-cao-2026-10-06-phan-mem`. Tag ghi rõ trạng thái kiểm thử phần mềm; chưa phải phiên bản đã xác nhận trên phần cứng.

Gói này chỉ chuẩn bị để công bố; chưa đẩy lên GitHub. Khi công bố, trích dẫn URL commit đầy đủ hoặc tag cố định, kèm trạng thái kiểm thử tương ứng. Không dùng link nhánh thay cho phiên bản cố định trong báo cáo. Nên dùng tag riêng cho bản đã xác nhận trên phần cứng, tránh gán trạng thái đó cho bản chỉ kiểm tra phần mềm.

## Giấy phép và mô hình

Metadata mô hình ghi giấy phép AGPL-3.0 của Ultralytics; xem [thông tin giấy phép Ultralytics](https://ultralytics.com/license). Các thư viện ngoài giữ giấy phép của tác giả tương ứng. Kho chưa bổ sung giấy phép riêng cho phần mã của dự án; trước khi công bố, chủ sở hữu cần xác định quyền phân phối mã, mô hình và dữ liệu huấn luyện liên quan.
