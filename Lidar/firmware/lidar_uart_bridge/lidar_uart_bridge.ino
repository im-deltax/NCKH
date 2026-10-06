
#include <HardwareSerial.h>

HardwareSerial PC(0);
const int PC_RX = 44;
const int PC_TX = 43;

HardwareSerial LidarSerial(1);
const int RX_PIN    = 16;
const int MOTOR_PIN = 4;

const uint32_t LIDAR_BAUD  = 115200;                                  
const uint32_t PC_BAUD     = 921600;                                 
const int      PWM_FREQ_HZ = 10000;
const int      PWM_BITS    = 10;
const int      PWM_CHANNEL = 0;

int motorDutyPct = 100;                        

static uint8_t block[1024];
static char    cmd[16];
static uint8_t cmdLen = 0;

void applyDuty(int pct) {
  if (pct < 0)   pct = 0;
  if (pct > 100) pct = 100;
  motorDutyPct = pct;
  uint32_t val = (uint32_t)((1 << PWM_BITS) - 1) * pct / 100;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(MOTOR_PIN, val);
#else
  ledcWrite(PWM_CHANNEL, val);
#endif
}

void setup() {
  PC.begin(PC_BAUD, SERIAL_8N1, PC_RX, PC_TX);

#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(MOTOR_PIN, PWM_FREQ_HZ, PWM_BITS);
#else
  ledcSetup(PWM_CHANNEL, PWM_FREQ_HZ, PWM_BITS);
  ledcAttachPin(MOTOR_PIN, PWM_CHANNEL);
#endif
  applyDuty(motorDutyPct);

  LidarSerial.setRxBufferSize(8192);
  LidarSerial.begin(LIDAR_BAUD, SERIAL_8N1, RX_PIN, -1);
}

void loop() {
  int n = LidarSerial.available();
  if (n > 0) {
    if (n > (int)sizeof(block)) n = sizeof(block);
    int got = LidarSerial.readBytes(block, n);
    if (got > 0) PC.write(block, got);
  }

  while (PC.available()) {
    char c = PC.read();
    if (c == '\n' || c == '\r') {
      if (cmdLen > 1 && (cmd[0] == 'D' || cmd[0] == 'd')) {
        cmd[cmdLen] = 0;
        applyDuty(atoi(cmd + 1));
      }
      cmdLen = 0;
    } else if (cmdLen < sizeof(cmd) - 1) {
      cmd[cmdLen++] = c;
    }
  }
}
