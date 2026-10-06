#include "iff_common.h"

#define PIN_SCK   2
#define PIN_MOSI  3
#define PIN_MISO  4
#define PIN_CSN   5
#define PIN_CE    8

const int PIN_DEN[] = {6, 7, 9, 10, 11};                                          
const int SO_CHAN_DEN = 5;

#define LED_DOMINO_MS        120UL                                               
#define LED_HOI_DAP_GIU_MS   600UL                                        

unsigned long tLedHoiDap = 0;
bool dangBaoHoiDap = false;

uint8_t viTriDomino = 0;
unsigned long tDomino = 0;
bool dominoDaBatDau = false;

#define CHU_KY_BAO_SERIAL_MS  3000UL
unsigned long tBaoSerial = 0;

void baoTrangThaiSerial(const char *noiDung) {
  unsigned long bayGio = millis();
  if (bayGio - tBaoSerial >= CHU_KY_BAO_SERIAL_MS) {
    tBaoSerial = bayGio;
    Serial.println(noiDung);
  }
}

int32_t slotOffset = 0;
bool daDongBo = false;
unsigned long tDongBoCuoi = 0;

#define CHU_KY_DONG_BO_MS   60000UL
#define CUA_SO_DONG_BO_MS     400UL

RF24 radio(PIN_CE, PIN_CSN);

const uint64_t PIPE_ADDR_CHALLENGE = 0xE8E8F0F0A1LL;               
const uint64_t PIPE_ADDR_RESPONSE  = 0xE8E8F0F0B2LL;               

uint8_t Key_enc[16];
uint8_t Key_mac[16];
uint8_t Key_hop[16];

uint8_t myStatus = 0x01;

enum CheDoThuXacThuc : uint8_t {
  THU_DUNG = 0,
  THU_SAI_ID,
  THU_SAI_MAC,
  THU_PHAT_LAI,
  THU_IM_LANG
};
CheDoThuXacThuc cheDoThu = THU_DUNG;
ResponsePacket phanHoiDungTruoc;
bool coPhanHoiDungTruoc = false;
char lenhThu[8];
uint8_t lenhThuLen = 0;
bool yeuCauDongBoLai = false;

const char* tenCheDoThu() {
  switch (cheDoThu) {
    case THU_SAI_ID:   return "SAI_ID";
    case THU_SAI_MAC:  return "SAI_MAC";
    case THU_PHAT_LAI: return "PHAT_LAI";
    case THU_IM_LANG:  return "IM_LANG";
    default:           return "DUNG";
  }
}

void xuLyLenhThuXacThuc() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (lenhThuLen == 0) continue;
      lenhThu[lenhThuLen] = '\0';
      if (!strcmp(lenhThu, "R")) {
        yeuCauDongBoLai = true;
        Serial.println("[TAG] DANG DONG BO LAI...");
        lenhThuLen = 0;
        continue;
      }
      if      (!strcmp(lenhThu, "T0")) cheDoThu = THU_DUNG;
      else if (!strcmp(lenhThu, "T1")) cheDoThu = THU_SAI_ID;
      else if (!strcmp(lenhThu, "T2")) cheDoThu = THU_SAI_MAC;
      else if (!strcmp(lenhThu, "T3")) cheDoThu = THU_PHAT_LAI;
      else if (!strcmp(lenhThu, "T4")) cheDoThu = THU_IM_LANG;
      else {
        Serial.println("[TAG] Lenh thu sai. Dung T0..T4.");
        lenhThuLen = 0;
        continue;
      }
      Serial.printf("[TAG] CHE DO THU: %s\n", tenCheDoThu());
      lenhThuLen = 0;
    } else if (lenhThuLen < sizeof(lenhThu) - 1) {
      lenhThu[lenhThuLen++] = c;
    }
  }
}

uint32_t slotTheoTram() {
  return (uint32_t)((int32_t)currentSlotIndex() + slotOffset);
}

void datDen(bool bat) {
  for (int i = 0; i < SO_CHAN_DEN; i++) {
    digitalWrite(PIN_DEN[i], bat ? HIGH : LOW);
  }
}

void datMotDen(uint8_t viTri) {
  for (int i = 0; i < SO_CHAN_DEN; i++) {
    digitalWrite(PIN_DEN[i], i == viTri ? HIGH : LOW);
  }
}

void batDauDominoNrf() {
  viTriDomino = 0;
  tDomino = 0;
  dominoDaBatDau = false;
}

void capNhatDominoNrf() {
  unsigned long bayGio = millis();
  if (!dominoDaBatDau || bayGio - tDomino >= LED_DOMINO_MS) {
    datMotDen(viTriDomino);
    viTriDomino = (viTriDomino + 1) % SO_CHAN_DEN;
    tDomino = bayGio;
    dominoDaBatDau = true;
  }
}

void batDenHoiDap() {
  datDen(true);
  dangBaoHoiDap = true;
  tLedHoiDap = millis();
}

void capNhatDenHoiDap() {
  if (dangBaoHoiDap && millis() - tLedHoiDap >= LED_HOI_DAP_GIU_MS) {
    dangBaoHoiDap = false;
    datDen(false);
  }
}

bool dongBoKheThoiGian(unsigned long gioi_han_ms) {
  radio.stopListening();
  radio.setChannel(SYNC_CHANNEL);
  radio.openReadingPipe(1, PIPE_ADDR_CHALLENGE);
  radio.startListening();

  unsigned long batDau = millis();
  unsigned long tKiemTraNrf = batDau;
  bool duoc = false;
  SyncPacket sync;

  while (gioi_han_ms == 0 || millis() - batDau < gioi_han_ms) {
    if (radio.available()) {
      radio.read(&sync, sizeof(sync));
      if (sync.msgType == MSG_TYPE_SYNC) {
        uint32_t slotTram = ((uint32_t)sync.slotIndex[0] << 24) |
                            ((uint32_t)sync.slotIndex[1] << 16) |
                            ((uint32_t)sync.slotIndex[2] << 8)  |
                            ((uint32_t)sync.slotIndex[3]);
        slotOffset = (int32_t)slotTram - (int32_t)currentSlotIndex();
        daDongBo = true;
        tDongBoCuoi = millis();
        duoc = true;
        Serial.printf("[TAG] Dong bo xong. Khe Tram=%lu, lech=%ld\n",
                      (unsigned long)slotTram, (long)slotOffset);
        break;
      }
    }
    if (millis() - tKiemTraNrf >= 250) {
      tKiemTraNrf = millis();
      if (!radio.isChipConnected()) {
        radio.stopListening();
        daDongBo = false;
        return false;
      }
    }
    if (gioi_han_ms == 0) {
      capNhatDominoNrf();
      baoTrangThaiSerial("[TAG] Trang thai: da thay NRF, dang cho Sync tu Tram...");
    }
    capNhatDenHoiDap();
  }

  radio.stopListening();
  if (!duoc && gioi_han_ms != 0) {
    tDongBoCuoi = millis();
  }
  return duoc;
}


void cauHinhNrf() {
  radio.setPALevel(RF24_PA_LOW);                                        
  radio.setDataRate(RF24_250KBPS);
  radio.setPayloadSize(NRF_PAYLOAD_SIZE);
  radio.setRetries(3, 5);
  radio.setAutoAck(true);
  radio.setCRCLength(RF24_CRC_16);
  radio.openReadingPipe(1, PIPE_ADDR_CHALLENGE);
}

void ketNoiNrfVaDongBo() {
  bool daBaoLoi = false;
  dangBaoHoiDap = false;
  batDauDominoNrf();
  unsigned long tThuNrf = millis() - 250UL;

  while (true) {
    if (millis() - tThuNrf >= 250UL) {
      tThuNrf = millis();
      if (radio.begin()) {
        cauHinhNrf();
        Serial.println("[TAG] Da tim thay NRF24L01. Domino tiep tuc den khi bat duoc Sync...");

        if (dongBoKheThoiGian(0)) {
          radio.openReadingPipe(1, PIPE_ADDR_CHALLENGE);
          datDen(false);
          Serial.println("[TAG] Da dong bo. San sang cho Challenge.");
          return;
        }
      }
    }

    if (!daBaoLoi) {
      Serial.println("[TAG] Chua co NRF hoac chua co tin hieu Tram. Nam LED chay domino.");
      daBaoLoi = true;
    }
    capNhatDominoNrf();
    baoTrangThaiSerial("[TAG] Trang thai: chua tim thay NRF24L01.");
    delay(2);
  }
}

void setup() {
  Serial.begin(115200);
  unsigned long batDauChoSerial = millis();
  while (!Serial && millis() - batDauChoSerial < 150UL) delay(5);
  delay(20);

  for (int i = 0; i < SO_CHAN_DEN; i++) pinMode(PIN_DEN[i], OUTPUT);
  datDen(false);

  SPI.setSCK(PIN_SCK);
  SPI.setTX(PIN_MOSI);
  SPI.setRX(PIN_MISO);
  SPI.begin();
  delay(100);
  Serial.println("[TAG] Khoi dong the bai IFF...");

  deriveKey(MASTER_KEY, "ENC", Key_enc);
  deriveKey(MASTER_KEY, "MAC", Key_mac);
  deriveKey(MASTER_KEY, "HOP", Key_hop);
  tuVanTay(Key_enc, Key_mac, Key_hop);

  ketNoiNrfVaDongBo();
  Serial.println("[TAG] San sang. LED tat khi cho; nam LED sang khi hoi-dap.");
}

void handleChallenge(const ChallengePacket& challenge) {
  if (cheDoThu == THU_IM_LANG) {
    Serial.println("[TAG] THU IM_LANG: bo qua Challenge.");
    return;
  }

  batDenHoiDap();

  uint32_t recvCounter = ((uint32_t)challenge.txCounter[0] << 24) |
                          ((uint32_t)challenge.txCounter[1] << 16) |
                          ((uint32_t)challenge.txCounter[2] << 8)  |
                          ((uint32_t)challenge.txCounter[3]);

  Serial.printf("[TAG] Nhan Challenge, counter=%lu\n", (unsigned long)recvCounter);

  uint8_t plaintext[PLAINTEXT_LEN];
  memcpy(plaintext, TAG_ID, 4);
  plaintext[4] = myStatus;
  if (cheDoThu == THU_SAI_ID) plaintext[0] ^= 0x5A;

  uint8_t ciphertext[PLAINTEXT_LEN];
  aesCtrCrypt(Key_enc, challenge.nonce, challenge.txCounter, plaintext, ciphertext, PLAINTEXT_LEN);

  uint8_t macData[NONCE_LEN + COUNTER_LEN + PLAINTEXT_LEN];
  memcpy(macData, challenge.nonce, NONCE_LEN);
  memcpy(macData + NONCE_LEN, challenge.txCounter, COUNTER_LEN);
  memcpy(macData + NONCE_LEN + COUNTER_LEN, ciphertext, PLAINTEXT_LEN);

  uint8_t mac[MAC_LEN];
  computeMAC(Key_mac, macData, sizeof(macData), mac);
  if (cheDoThu == THU_SAI_MAC) mac[0] ^= 0xA5;

  ResponsePacket response;
  memset(&response, 0, sizeof(response));
  response.msgType = MSG_TYPE_RESPONSE;
  memcpy(response.txCounter, challenge.txCounter, COUNTER_LEN);
  memcpy(response.ciphertext, ciphertext, PLAINTEXT_LEN);
  memcpy(response.mac, mac, MAC_LEN);

  if (cheDoThu == THU_DUNG) {
    phanHoiDungTruoc = response;
    coPhanHoiDungTruoc = true;
  } else if (cheDoThu == THU_PHAT_LAI) {
    if (!coPhanHoiDungTruoc) {
      Serial.println("[TAG] THU PHAT_LAI: chua co goi dung truoc do, im lang.");
      return;
    }
    response = phanHoiDungTruoc;
  }

  uint8_t responseChannel = deriveResponseChannel(Key_hop, challenge.nonce);

  radio.stopListening();
  radio.setChannel(responseChannel);
  radio.openWritingPipe(PIPE_ADDR_RESPONSE);

  bool sent = false;
  for (uint8_t attempt = 0; attempt < TX_RETRY_COUNT && !sent; attempt++) {
    sent = radio.write(&response, sizeof(response));
    if (!sent) delayMicroseconds(500);
  }

  if (sent) {
    Serial.printf("[TAG] Da gui Response tren kenh %d\n", responseChannel);
  } else {
    Serial.println("[TAG] GUI RESPONSE THAT BAI (co the do nhieu/jamming).");
  }

  uint8_t ctrlChannel = deriveControlChannel(Key_hop, slotTheoTram());
  radio.setChannel(ctrlChannel);
  radio.startListening();
}

void loop() {
  xuLyLenhThuXacThuc();

  if (yeuCauDongBoLai) {
    yeuCauDongBoLai = false;
    bool ok = dongBoKheThoiGian(0);
    if (!ok) {
      ketNoiNrfVaDongBo();
    }
    radio.openReadingPipe(1, PIPE_ADDR_CHALLENGE);
    Serial.println("[TAG] DONG BO LAI: OK");
  }

  baoTrangThaiSerial("[TAG] Trang thai: DA DONG BO - san sang nhan Challenge.");

  if (!radio.isChipConnected()) {
    daDongBo = false;
    ketNoiNrfVaDongBo();
  }
  capNhatDenHoiDap();

  if (millis() - tDongBoCuoi > CHU_KY_DONG_BO_MS) {
    bool dongBoLai = dongBoKheThoiGian(CUA_SO_DONG_BO_MS);
    if (!dongBoLai && !radio.isChipConnected()) {
      ketNoiNrfVaDongBo();
    }
    radio.openReadingPipe(1, PIPE_ADDR_CHALLENGE);
  }

  uint32_t slot = slotTheoTram();
  uint8_t ctrlChannel = deriveControlChannel(Key_hop, slot);

  radio.setChannel(ctrlChannel);
  radio.startListening();

  unsigned long listenStart = millis();
  bool received = false;
  ChallengePacket challenge;

  while (millis() - listenStart < CHANNEL_LISTEN_MS) {
    if (slotTheoTram() != slot) break;

    if (radio.available()) {
      radio.read(&challenge, sizeof(challenge));
      if (challenge.msgType == MSG_TYPE_CHALLENGE) {
        received = true;
      }
      break;
    }
  }
  radio.stopListening();

  if (received) {
    handleChallenge(challenge);
  }
  capNhatDenHoiDap();
}


