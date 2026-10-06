#include "iff_common.h"
#include "trang_thai.h"
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include "giao_dien.h"

#define PIN_SCK       4
#define PIN_MOSI      6

#define PIN_TFT_CS    7
#define PIN_TFT_DC    5
#define PIN_TFT_RST   3

#define PIN_MISO      10
#define PIN_CE        0
#define PIN_CSN       1

#define PIN_LED1      21
#define PIN_LED2      20

#define PIN_COI        8
#define COI_MUC_BAT    HIGH
#define COI_CHU_KY_MS  1100UL

#define DEN_CHO_NUA_CHU_KY_MS   400                             
#define DEN_BAN_CHU_KY_MS      2000UL                              
#define DEN_BAN_NHIP_MS         150                                   
#define DEN_BAN_SO_NHIP           3                                    

#define W   240
#define H   240
#define CX  120
#define CY  120


Adafruit_GC9A01A tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST);
RF24 radio(PIN_CE, PIN_CSN);
GiaoDienTram giaoDien(tft);

const uint64_t PIPE_ADDR_CHALLENGE = 0xE8E8F0F0A1LL;               
const uint64_t PIPE_ADDR_RESPONSE  = 0xE8E8F0F0B2LL;               

uint8_t Key_enc[16];
uint8_t Key_mac[16];
uint8_t Key_hop[16];

uint32_t txCounter = 0;
uint32_t lastValidCounter = 0;

#define NHIP_DONG_BO_MS    500UL
unsigned long tDongBoCuoi = 0;

bool tuHoi = false;
#define CHU_KY_TU_HOI_MS  2000UL
unsigned long tTuHoiCuoi = 0;

#define NHIP_KIEM_TRA_NRF_MS       500UL
#define SO_LAN_XAC_NHAN_MAT_NRF      3
#define SO_LAN_XAC_NHAN_CO_NRF       2
#define NRF_PA_LEVEL       RF24_PA_LOW                                              
unsigned long tKiemTraNrf = 0;
uint8_t soLanNrfLoi = 0;
uint8_t soLanNrfTot = 0;
bool nrfSanSang = false;

const char* tenLyDo(LyDo d) {
  switch (d) {
    case LD_FRIEND:   return "FRIEND";
    case LD_NO_TX:    return "NO_TX";
    case LD_NO_RESP:  return "NO_RESP";
    case LD_BAD_TYPE: return "BAD_TYPE";
    case LD_BAD_CNT:  return "BAD_CNT";
    case LD_REPLAY:   return "REPLAY";
    case LD_BAD_MAC:  return "BAD_MAC";
    default:          return "BAD_ID";
  }
}
const char* moTaLyDo(LyDo d) {
  switch (d) {
    case LD_NO_TX:    return "Không phát được";
    case LD_NO_RESP:  return "Không hồi âm";
    case LD_BAD_TYPE: return "Gói tin sai dạng";
    case LD_BAD_CNT:  return "Số đếm lệch";
    case LD_REPLAY:   return "Phát lại bản cũ";
    case LD_BAD_MAC:  return "Chữ ký sai";
    case LD_BAD_ID:   return "Sai mã thẻ";
    default:          return "";
  }
}
LyDo lyDoCuoi = LD_NO_RESP;
uint8_t statusCuoi = 0;
unsigned long dtCuoi = 0;
uint8_t soLanThuCuoi = 0;

TrangThai tt = TT_CHO;
unsigned long tVaoTrangThai = 0;
unsigned long tVeCuoi = 0;
bool canVeNen = true;                                             
bool canVeSoLieu = false;                                                    
bool dangXemMan = false;                                                    
#define CHU_KY_VE_MS  50                                                        

void datTrangThai(TrangThai moi) {
  if (tt == moi) return;
  tt = moi;
  tVaoTrangThai = millis();
  canVeNen = true;
}

void datDen(bool d1, bool d2) {
  digitalWrite(PIN_LED1, d1 ? HIGH : LOW);
  digitalWrite(PIN_LED2, d2 ? HIGH : LOW);
}

void capNhatDen() {
  unsigned long t = millis();

  switch (tt) {
    case TT_CHO:
    case TT_DANG_HOI: {
      bool pha = ((t / DEN_CHO_NUA_CHU_KY_MS) % 2) == 0;
      datDen(pha, !pha);
      break;
    }

    case TT_BAN: {
      unsigned long dt = t - tVaoTrangThai;
      unsigned long u = dt % DEN_BAN_CHU_KY_MS;
      unsigned long doanChop = (unsigned long)DEN_BAN_SO_NHIP * 2UL * DEN_BAN_NHIP_MS;

      bool sang;
      if (u < doanChop) sang = ((u / DEN_BAN_NHIP_MS) % 2) == 0;                           
      else              sang = true;                                                  
      datDen(sang, sang);
      break;
    }

    default:
      datDen(false, false);
      break;
  }
}

void capNhatCoi() {
  if (tt != TT_THU) {
    digitalWrite(PIN_COI, COI_MUC_BAT == HIGH ? LOW : HIGH);
    return;
  }

  unsigned long pha = (millis() - tVaoTrangThai) % COI_CHU_KY_MS;
  bool bat = (pha < 130UL)
          || (pha >= 220UL && pha < 350UL)
          || (pha >= 440UL && pha < 650UL);
  digitalWrite(PIN_COI, bat ? COI_MUC_BAT
                            : (COI_MUC_BAT == HIGH ? LOW : HIGH));
}

void veMan() {
  unsigned long t = millis();
  if (!canVeNen && t - tVeCuoi < CHU_KY_VE_MS) return;
  tVeCuoi = t;
  giaoDien.draw(tt, t - tVaoTrangThai, t, canVeNen, canVeSoLieu,
                moTaLyDo(lyDoCuoi), dtCuoi, soLanThuCuoi);
  canVeNen = false;
  canVeSoLieu = false;
}

bool khoiDongNrf() {
  digitalWrite(PIN_TFT_CS, HIGH);
  digitalWrite(PIN_CSN, HIGH);
  digitalWrite(PIN_CE, LOW);
  delay(2);
  if (!radio.begin(&SPI)) return false;
  radio.setPALevel(NRF_PA_LEVEL);
  radio.setDataRate(RF24_250KBPS);
  radio.setPayloadSize(NRF_PAYLOAD_SIZE);
  radio.setRetries(3, 5);
  radio.setAutoAck(true);
  radio.setCRCLength(RF24_CRC_16);
  radio.stopListening();
  return radio.isChipConnected();
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_LED1, OUTPUT);
  pinMode(PIN_LED2, OUTPUT);
  datDen(false, false);
  pinMode(PIN_COI, OUTPUT);
  digitalWrite(PIN_COI, COI_MUC_BAT == HIGH ? LOW : HIGH);

  pinMode(PIN_TFT_CS, OUTPUT);
  pinMode(PIN_CSN, OUTPUT);
  pinMode(PIN_CE, OUTPUT);
  digitalWrite(PIN_TFT_CS, HIGH);
  digitalWrite(PIN_CSN, HIGH);
  digitalWrite(PIN_CE, LOW);

  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, -1);

  tft.begin();
  tft.setSPISpeed(26000000);
  tft.setRotation(0);
  giaoDien.boot();

  Serial.println("[STATION] Khoi dong tram mat dat IFF...");

  deriveKey(MASTER_KEY, "ENC", Key_enc);
  deriveKey(MASTER_KEY, "MAC", Key_mac);
  deriveKey(MASTER_KEY, "HOP", Key_hop);
  tuVanTay(Key_enc, Key_mac, Key_hop);

  if (!khoiDongNrf()) {
    Serial.println("[STATION] LOI: Khong tim thay module NRF24L01! Kiem tra day va nguon 3V3.");
    nrfSanSang = false;
    datTrangThai(TT_MAT_SONG);
    return;
  }
  nrfSanSang = true;
  soLanNrfLoi = 0;
  soLanNrfTot = 0;

  Serial.println("[STATION] San sang. Dang cho su kien tu LiDAR.");
  Serial.println("[STATION] Lenh: L1/L0 LiDAR, Q hoi IFF, A0/A1 tu hoi, S, Y, M0..M4 xem man");
  Serial.println("[STATION] Tra ve: R,<0|1>,<ms>,<ly_do>,<so_lan_thu>,<status>");
  Serial.println("========================================");

  datTrangThai(TT_CHO);
}

bool nrfCoSong() {
  if (!nrfSanSang) return false;
  if (radio.isChipConnected()) return true;
  delayMicroseconds(100);
  return radio.isChipConnected();
}

void capNhatTinhTrangNrf() {
  if (dangXemMan) return;
  unsigned long t = millis();
  if (t - tKiemTraNrf < NHIP_KIEM_TRA_NRF_MS) return;
  tKiemTraNrf = t;

  if (nrfSanSang) {
    if (radio.isChipConnected()) { soLanNrfLoi = 0; return; }
    if (++soLanNrfLoi < SO_LAN_XAC_NHAN_MAT_NRF) return;
    soLanNrfLoi = 0;
    soLanNrfTot = 0;
    nrfSanSang = false;
    Serial.println("[STATION] Mat lien lac voi module NRF24L01 (da xac nhan 3 lan).");
    datTrangThai(TT_MAT_SONG);
    return;
  }

  if (khoiDongNrf()) {
    if (++soLanNrfTot < SO_LAN_XAC_NHAN_CO_NRF) return;
    soLanNrfTot = 0;
    soLanNrfLoi = 0;
    nrfSanSang = true;
    Serial.println("[STATION] Da khoi phuc module NRF24L01 on dinh.");
    datTrangThai(TT_CHO);
  } else {
    soLanNrfTot = 0;
  }
}
void sendSyncBroadcast() {
  if (!nrfSanSang || tt == TT_MAT_SONG) return;
  uint32_t slot = currentSlotIndex();

  SyncPacket sync;
  memset(&sync, 0, sizeof(sync));
  sync.msgType = MSG_TYPE_SYNC;
  sync.slotIndex[0] = (slot >> 24) & 0xFF;
  sync.slotIndex[1] = (slot >> 16) & 0xFF;
  sync.slotIndex[2] = (slot >> 8)  & 0xFF;
  sync.slotIndex[3] =  slot        & 0xFF;

  radio.setChannel(SYNC_CHANNEL);
  radio.stopListening();
  radio.openWritingPipe(PIPE_ADDR_CHALLENGE);
  radio.write(&sync, sizeof(sync));
  tDongBoCuoi = millis();
}

bool performIFFChallenge() {
  txCounter++;

  uint8_t nonce[NONCE_LEN];
  for (int i = 0; i < NONCE_LEN; i++) nonce[i] = (uint8_t)ngauNhien32();

  ChallengePacket challenge;
  memset(&challenge, 0, sizeof(challenge));
  challenge.msgType = MSG_TYPE_CHALLENGE;
  memcpy(challenge.nonce, nonce, NONCE_LEN);
  challenge.txCounter[0] = (txCounter >> 24) & 0xFF;
  challenge.txCounter[1] = (txCounter >> 16) & 0xFF;
  challenge.txCounter[2] = (txCounter >> 8)  & 0xFF;
  challenge.txCounter[3] =  txCounter        & 0xFF;

  uint8_t responseChannel = deriveResponseChannel(Key_hop, nonce);

  uint32_t slotGoc = currentSlotIndex();
  const int8_t lechKhe[] = {0, -1, 1};
  uint32_t slotDaGui = slotGoc;
  uint8_t ctrlChannel = deriveControlChannel(Key_hop, slotGoc);

  radio.stopListening();
  radio.openWritingPipe(PIPE_ADDR_CHALLENGE);

  bool gotAck = false;
  for (uint8_t k = 0; k < 3 && !gotAck; k++) {
    uint32_t slotThu = (uint32_t)((int32_t)slotGoc + lechKhe[k]);
    uint8_t kenhThu = deriveControlChannel(Key_hop, slotThu);
    radio.setChannel(kenhThu);
    for (uint8_t attempt = 0;
         attempt < TX_RETRY_COUNT && !gotAck; attempt++) {
      gotAck = radio.write(&challenge, sizeof(challenge));
      if (!gotAck) delay(3);
    }
    if (gotAck) {
      slotDaGui = slotThu;
      ctrlChannel = kenhThu;
    }
  }

  if (!gotAck) {
    Serial.printf("[STATION] KHONG the gui Challenge quanh khe %lu -> NO_TX.\n",
                  (unsigned long)slotGoc);
    lyDoCuoi = LD_NO_TX;
    return false;
  }
  Serial.printf("[STATION] Challenge gui thanh cong tren kenh %d (khe %lu, goc=%lu, counter=%lu)\n",
                ctrlChannel, (unsigned long)slotDaGui,
                (unsigned long)slotGoc, (unsigned long)txCounter);

  radio.setChannel(responseChannel);
  radio.openReadingPipe(1, PIPE_ADDR_RESPONSE);
  radio.startListening();

  unsigned long startWait = millis();
  bool gotResponse = false;
  ResponsePacket response;

  while (millis() - startWait < RESPONSE_TIMEOUT_MS) {
    if (radio.available()) {
      radio.read(&response, sizeof(response));
      gotResponse = true;
      break;
    }
  }
  radio.stopListening();

  if (!gotResponse) {
    Serial.println("[STATION] KHONG nhan duoc Response -> khong phan hoi.");
    lyDoCuoi = LD_NO_RESP;
    return false;
  }
  if (response.msgType != MSG_TYPE_RESPONSE) {
    Serial.println("[STATION] Sai dinh dang goi tin -> loai bo.");
    lyDoCuoi = LD_BAD_TYPE;
    return false;
  }

  uint32_t recvCounter = ((uint32_t)response.txCounter[0] << 24) |
                          ((uint32_t)response.txCounter[1] << 16) |
                          ((uint32_t)response.txCounter[2] << 8)  |
                          ((uint32_t)response.txCounter[3]);

  if (recvCounter != txCounter) {
    Serial.println("[STATION] Counter khong khop voi Challenge da gui -> loai bo.");
    lyDoCuoi = LD_BAD_CNT;
    return false;
  }
  if (recvCounter <= lastValidCounter) {
    Serial.println("[STATION] Counter <= gia tri hop le truoc do -> REPLAY, loai bo.");
    lyDoCuoi = LD_REPLAY;
    return false;
  }

  uint8_t macData[NONCE_LEN + COUNTER_LEN + PLAINTEXT_LEN];
  memcpy(macData, nonce, NONCE_LEN);
  memcpy(macData + NONCE_LEN, response.txCounter, COUNTER_LEN);
  memcpy(macData + NONCE_LEN + COUNTER_LEN, response.ciphertext, PLAINTEXT_LEN);

  uint8_t expectedMac[MAC_LEN];
  computeMAC(Key_mac, macData, sizeof(macData), expectedMac);

  if (!constantTimeEqual(expectedMac, response.mac, MAC_LEN)) {
    Serial.println("[STATION] MAC KHONG KHOP -> gia mao hoac sai khoa.");
    lyDoCuoi = LD_BAD_MAC;
    return false;
  }

  uint8_t plaintext[PLAINTEXT_LEN];
  aesCtrCrypt(Key_enc, nonce, response.txCounter, response.ciphertext, plaintext, PLAINTEXT_LEN);

  bool idMatch = (memcmp(plaintext, TAG_ID, 4) == 0);
  uint8_t status = plaintext[4];

  lastValidCounter = recvCounter;

  if (idMatch) {
    Serial.printf("[STATION] >>> FRIEND xac nhan. TagID hop le. Status=0x%02X\n", status);
    lyDoCuoi = LD_FRIEND;
    statusCuoi = status;
    return true;
  }
  Serial.println("[STATION] >>> MAC dung nhung ID khong khop.");
  lyDoCuoi = LD_BAD_ID;
  return false;
}

void hoiVaTraLoi(uint8_t so_lan) {
  if (!nrfSanSang || tt == TT_MAT_SONG) {
    Serial.println("R,0,0,NO_TX,0,0");
    return;
  }
  if (so_lan < 1) so_lan = 1;
  if (so_lan > 9) so_lan = 9;

  datTrangThai(TT_DANG_HOI);
  veMan();

  unsigned long t0 = millis();
  bool duoc = false;
  uint8_t da_thu = 0;

  for (uint8_t i = 0; i < so_lan && !duoc; i++) {
    da_thu++;
    sendSyncBroadcast();
    delay(8);
    duoc = performIFFChallenge();

    if (!duoc && (lyDoCuoi == LD_BAD_TYPE || lyDoCuoi == LD_BAD_CNT ||
                  lyDoCuoi == LD_REPLAY   || lyDoCuoi == LD_BAD_MAC ||
                  lyDoCuoi == LD_BAD_ID)) {
      break;
    }
  }

  dtCuoi = millis() - t0;
  soLanThuCuoi = da_thu;
  if (!duoc) statusCuoi = 0;

  TrangThai ketLuan;
  if (!duoc && !nrfCoSong()) {
    nrfSanSang = false;
    soLanNrfTot = 0;
    ketLuan = TT_MAT_SONG;
  }
  else                       ketLuan = duoc ? TT_BAN : TT_THU;

  if (ketLuan == tt) {
    if (ketLuan == TT_BAN || ketLuan == TT_THU) canVeSoLieu = true;
  } else {
    datTrangThai(ketLuan);
  }

  Serial.printf("R,%d,%lu,%s,%u,%u\n",
                duoc ? 1 : 0, dtCuoi, tenLyDo(lyDoCuoi), da_thu,
                duoc ? statusCuoi : 0);
}

void xuLyLenh(char *s) {
  if (s[0] != 'M') dangXemMan = false;
  switch (s[0]) {
    case 'L':                                                                   
      if (s[1] == '0') {
        datTrangThai(TT_CHO);
        Serial.println("OK,lidar=0");
      } else {
        Serial.println("OK,lidar=1");
        hoiVaTraLoi(1);
      }
      break;
    case 'Q': {                                                              
      uint8_t n = (s[1] >= '1' && s[1] <= '9') ? (uint8_t)(s[1] - '0') : 1;
      hoiVaTraLoi(n);
      break;
    }
    case 'A':
      tuHoi = (s[1] == '1');
      Serial.printf("OK,tu_hoi=%d\n", tuHoi ? 1 : 0);
      break;
    case 'S':
      Serial.printf("S,khe=%lu,tx=%lu,tu_hoi=%d,cho_ms=%d,thu=%d,nrf=%d\n",
                    (unsigned long)currentSlotIndex(),
                    (unsigned long)txCounter, tuHoi ? 1 : 0,
                    RESPONSE_TIMEOUT_MS, TX_RETRY_COUNT,
                     nrfSanSang ? 1 : 0);
      break;
    case 'Y':
      sendSyncBroadcast();
      Serial.println("OK,sync");
      break;
    case 'M':                                              
      dangXemMan = true;
      switch (s[1]) {
        case '1': datTrangThai(TT_MAT_SONG); break;
        case '2': datTrangThai(TT_DANG_HOI); break;
        case '3': dtCuoi = 42; soLanThuCuoi = 1; statusCuoi = 0x01;
                  datTrangThai(TT_BAN);      break;
        case '4': dtCuoi = 470; soLanThuCuoi = 3; lyDoCuoi = LD_NO_RESP;
                  datTrangThai(TT_THU);      break;
        default:  datTrangThai(TT_CHO);      break;
      }
      Serial.println("OK,man");
      break;
    default:
      Serial.println("ER,lenh la");
  }
}

char buf[24];
uint8_t bufLen = 0;

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufLen > 0) { buf[bufLen] = '\0'; xuLyLenh(buf); bufLen = 0; }
    } else if (bufLen < sizeof(buf) - 1) {
      buf[bufLen++] = c;
    }
  }

  capNhatTinhTrangNrf();

  if (nrfSanSang && tt != TT_MAT_SONG && millis() - tDongBoCuoi > NHIP_DONG_BO_MS) sendSyncBroadcast();

  if (tuHoi && nrfSanSang && tt != TT_MAT_SONG && millis() - tTuHoiCuoi > CHU_KY_TU_HOI_MS) {
    tTuHoiCuoi = millis();
    hoiVaTraLoi(1);
  }

  capNhatDen();
  capNhatCoi();
  veMan();

  delay(1);
}

