#ifndef IFF_COMMON_H
#define IFF_COMMON_H


#include <Arduino.h>
#include <string.h>
#include <SPI.h>
#include <RF24.h>
#include <Crypto.h>
#include <SHA256.h>
#include <AES.h>
#include <esp_random.h>

#if __has_include("iff_key.local.h")
#include "iff_key.local.h"
#else
#include "iff_key.example.h"
#endif

static const uint8_t TAG_ID[4] = {0x01, 0x02, 0x03, 0x04};

#define NONCE_LEN      8
#define COUNTER_LEN    4
#define PLAINTEXT_LEN  5                           
#define MAC_LEN        8
#define KEY_LEN        16

#define MSG_TYPE_CHALLENGE  0x01
#define MSG_TYPE_RESPONSE   0x02
#define MSG_TYPE_SYNC       0x03

#define NRF_PAYLOAD_SIZE 32

#define SYNC_CHANNEL     76

struct ChallengePacket {
  uint8_t msgType;
  uint8_t nonce[NONCE_LEN];
  uint8_t txCounter[COUNTER_LEN];
  uint8_t reserved[NRF_PAYLOAD_SIZE - 1 - NONCE_LEN - COUNTER_LEN];
};

struct ResponsePacket {
  uint8_t msgType;
  uint8_t txCounter[COUNTER_LEN];
  uint8_t ciphertext[PLAINTEXT_LEN];
  uint8_t mac[MAC_LEN];
  uint8_t reserved[NRF_PAYLOAD_SIZE - 1 - COUNTER_LEN - PLAINTEXT_LEN - MAC_LEN];
};

struct SyncPacket {
  uint8_t msgType;
  uint8_t slotIndex[4];
  uint8_t reserved[NRF_PAYLOAD_SIZE - 1 - 4];
};

#define SLOT_DURATION_MS   200
#define CHANNEL_MIN        2
#define CHANNEL_MAX        119
#define CHANNEL_RANGE      (CHANNEL_MAX - CHANNEL_MIN + 1)

#define RESPONSE_TIMEOUT_MS   150
#define TX_RETRY_COUNT        3
#define CHANNEL_LISTEN_MS     180

inline void hmacSha256(const uint8_t* key, size_t keyLen,
                       const uint8_t* data, size_t dataLen, uint8_t* out32) {
  SHA256 sha;
  sha.resetHMAC(key, keyLen);
  sha.update(data, dataLen);
  sha.finalizeHMAC(key, keyLen, out32, 32);
}

inline void deriveKey(const uint8_t* masterKey, const char* label, uint8_t* outKey16) {
  uint8_t hmacResult[32];
  hmacSha256(masterKey, KEY_LEN, (const uint8_t*)label, strlen(label), hmacResult);
  memcpy(outKey16, hmacResult, 16);
}

inline void aesEncryptBlock(const uint8_t* key16, const uint8_t* in16, uint8_t* out16) {
  AES128 aes;
  aes.setKey(key16, 16);
  aes.encryptBlock(out16, in16);
}

inline void aesCtrCrypt(const uint8_t* key16, const uint8_t* nonce8,
                        const uint8_t* txCounter4, const uint8_t* input,
                        uint8_t* output, size_t len) {
  uint8_t ivBlock[16];
  memcpy(ivBlock, nonce8, 8);
  memcpy(ivBlock + 8, txCounter4, 4);
  ivBlock[12] = 0; ivBlock[13] = 0; ivBlock[14] = 0; ivBlock[15] = 0;

  uint8_t keystream[16];
  aesEncryptBlock(key16, ivBlock, keystream);

  for (size_t i = 0; i < len; i++) output[i] = input[i] ^ keystream[i];
}

inline void computeMAC(const uint8_t* key16, const uint8_t* data, size_t dataLen,
                       uint8_t* macOut) {
  size_t numBlocks = (dataLen / 16) + 1;
  size_t paddedLen = numBlocks * 16;
  uint8_t buf[64];
  memset(buf, 0, sizeof(buf));
  memcpy(buf, data, dataLen);
  uint8_t padValue = (uint8_t)(paddedLen - dataLen);
  for (size_t i = dataLen; i < paddedLen; i++) buf[i] = padValue;

  uint8_t iv[16];
  memset(iv, 0, 16);
  uint8_t block[16];
  uint8_t xorIn[16];

  for (size_t b = 0; b < numBlocks; b++) {
    for (int i = 0; i < 16; i++) xorIn[i] = buf[b * 16 + i] ^ iv[i];
    aesEncryptBlock(key16, xorIn, block);
    memcpy(iv, block, 16);
  }
  memcpy(macOut, iv, MAC_LEN);
}

inline bool constantTimeEqual(const uint8_t* a, const uint8_t* b, size_t len) {
  uint8_t diff = 0;
  for (size_t i = 0; i < len; i++) diff |= (a[i] ^ b[i]);
  return diff == 0;
}

inline uint8_t deriveResponseChannel(const uint8_t* hopKey16, const uint8_t* nonce8) {
  uint8_t hmacResult[32];
  hmacSha256(hopKey16, KEY_LEN, nonce8, NONCE_LEN, hmacResult);
  return CHANNEL_MIN + (hmacResult[0] % CHANNEL_RANGE);
}

inline uint32_t currentSlotIndex() {
  return (uint32_t)(millis() / SLOT_DURATION_MS);
}

inline uint8_t deriveControlChannel(const uint8_t* hopKey16, uint32_t slotIndex) {
  uint8_t slotBytes[4] = {
    (uint8_t)(slotIndex >> 24), (uint8_t)(slotIndex >> 16),
    (uint8_t)(slotIndex >> 8),  (uint8_t)(slotIndex)
  };
  uint8_t hmacResult[32];
  hmacSha256(hopKey16, KEY_LEN, slotBytes, 4, hmacResult);
  return CHANNEL_MIN + (hmacResult[0] % CHANNEL_RANGE);
}

inline uint32_t ngauNhien32() {
  return esp_random();
}

inline void tuVanTay(const uint8_t* enc, const uint8_t* mac, const uint8_t* hop) {
  Serial.printf("# Van tay khoa ENC %02X%02X%02X%02X  MAC %02X%02X%02X%02X  HOP %02X%02X%02X%02X\n",
                enc[0], enc[1], enc[2], enc[3],
                mac[0], mac[1], mac[2], mac[3],
                hop[0], hop[1], hop[2], hop[3]);
  Serial.printf("# Kenh dong bo %d, khe %lu ms, dai kenh %d..%d\n",
                SYNC_CHANNEL, (unsigned long)SLOT_DURATION_MS,
                CHANNEL_MIN, CHANNEL_MAX);
}

#endif
