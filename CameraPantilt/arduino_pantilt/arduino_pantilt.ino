
#include <Servo.h>

const int PIN_PAN  = 4;                                   
const int PIN_TILT = 3;                                    
const int PIN_LED  = 13;                                             
const int PIN_COI  = 8;                                 

const unsigned int COI_F_MIN = 600;         
const unsigned int COI_F_MAX = 1400;        
const unsigned long COI_CHU_KY_MS = 700;                            

bool coiBat = false;
unsigned long coiMocMs = 0;
unsigned long coiBipTat = 0;                                                  

void coiCapNhat() {
  unsigned long now = millis();

  if (coiBipTat) {                                                
    if (now >= coiBipTat) { noTone(PIN_COI); coiBipTat = 0; }
    return;
  }
  if (!coiBat) return;

  unsigned long pha = (now - coiMocMs) % COI_CHU_KY_MS;
  unsigned long nua = COI_CHU_KY_MS / 2;
  unsigned int f;
  if (pha < nua) f = COI_F_MIN + (COI_F_MAX - COI_F_MIN) * pha / nua;
  else           f = COI_F_MAX - (COI_F_MAX - COI_F_MIN) * (pha - nua) / nua;
  tone(PIN_COI, f);
}

void coiDat(bool bat) {
  coiBat = bat;
  coiBipTat = 0;
  if (bat) coiMocMs = millis();
  else     noTone(PIN_COI);
}

void coiBip(unsigned int f, unsigned long ms) {
  coiBat = false;
  tone(PIN_COI, f);
  coiBipTat = millis() + ms;
}

const int US_MIN = 500;             
const int US_MAX = 2500;            

const float DEG_SPAN_PAN  = 163.8;
const float DEG_SPAN_TILT = 180.0;

float panMin  = -81.0, panMax  =  81.0;
float tiltMin = -75.0, tiltMax =  75.0;                                 

const float MAX_STEP_DEG = 30.0;                             

const bool TILT_DAO_DAU = false;
const bool PAN_DAO_DAU  = false;

Servo sPan, sTilt;
float curPan = 0.0, curTilt = 0.0;
bool  enabled = false;

char    buf[48];
uint8_t bufLen = 0;

float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

int degToUs(float deg, bool dao, float span) {
  if (dao) deg = -deg;
  float u = (deg + span * 0.5) / span;
  u = u < 0.0 ? 0.0 : (u > 1.0 ? 1.0 : u);
  return (int)(US_MIN + u * (US_MAX - US_MIN));
}

float usToDeg(int us, bool dao, float span) {
  float d = (float)(us - US_MIN) / (US_MAX - US_MIN) * span - span * 0.5;
  return dao ? -d : d;
}

bool parse2f(char *s, float *a, float *b) {
  char *comma = strchr(s, ',');
  if (!comma) return false;
  *comma = '\0';
  *a = atof(s);
  *b = atof(comma + 1);
  return true;
}

bool parse4f(char *s, float *a, float *b, float *c, float *d) {
  char *p1 = strchr(s, ',');       if (!p1) return false; *p1 = '\0';
  char *p2 = strchr(p1 + 1, ',');  if (!p2) return false; *p2 = '\0';
  char *p3 = strchr(p2 + 1, ',');  if (!p3) return false; *p3 = '\0';
  *a = atof(s); *b = atof(p1 + 1); *c = atof(p2 + 1); *d = atof(p3 + 1);
  return true;
}

void applyAngles(float p, float t) {
  p = clampf(p, panMin,  panMax);
  t = clampf(t, tiltMin, tiltMax);

  if (fabs(p - curPan)  > MAX_STEP_DEG)
    p = curPan  + (p > curPan  ? MAX_STEP_DEG : -MAX_STEP_DEG);
  if (fabs(t - curTilt) > MAX_STEP_DEG)
    t = curTilt + (t > curTilt ? MAX_STEP_DEG : -MAX_STEP_DEG);

  curPan = p;  curTilt = t;
  if (enabled) {
    sPan.writeMicroseconds(degToUs(curPan, PAN_DAO_DAU, DEG_SPAN_PAN));
    sTilt.writeMicroseconds(degToUs(curTilt, TILT_DAO_DAU, DEG_SPAN_TILT));
  }
}

void enableServos(bool on) {
  enabled = on;
  if (on) {
    sPan.writeMicroseconds(degToUs(curPan, PAN_DAO_DAU, DEG_SPAN_PAN));
    sTilt.writeMicroseconds(degToUs(curTilt, TILT_DAO_DAU, DEG_SPAN_TILT));
  }
}

void quetCham(Servo &sv, const char *ten) {
  Serial.print(F("QUET ")); Serial.println(ten);
  for (int us = 1500; us <= 1800; us += 5) { sv.writeMicroseconds(us); delay(20); }
  for (int us = 1800; us >= 1200; us -= 5) { sv.writeMicroseconds(us); delay(20); }
  for (int us = 1200; us <= 1500; us += 5) { sv.writeMicroseconds(us); delay(20); }
}

void sendOk() {
  Serial.print(F("OK "));
  Serial.println(millis());
}

void sendStatus() {
  Serial.print(F("ST p="));  Serial.print(curPan, 2);
  Serial.print(F(" t="));    Serial.print(curTilt, 2);
  Serial.print(F(" up="));   Serial.print(degToUs(curPan, PAN_DAO_DAU, DEG_SPAN_PAN));
  Serial.print(F(" ut="));   Serial.print(degToUs(curTilt, TILT_DAO_DAU, DEG_SPAN_TILT));
  Serial.print(F(" en="));   Serial.println(enabled ? 1 : 0);
}

void handleLine(char *s) {
  switch (s[0]) {

    case 'A': {
      float p, t;
      if (parse2f(s + 1, &p, &t)) { applyAngles(p, t); sendOk(); }
      else Serial.println(F("ER cu phap A"));
      break;
    }

    case 'U': {
      float up, ut;
      if (parse2f(s + 1, &up, &ut)) {
        int iu = constrain((int)up, US_MIN, US_MAX);
        int it = constrain((int)ut, US_MIN, US_MAX);
        if (enabled) {
          sPan.writeMicroseconds(iu);
          sTilt.writeMicroseconds(it);
        }
        curPan  = usToDeg(iu, PAN_DAO_DAU,  DEG_SPAN_PAN);
        curTilt = usToDeg(it, TILT_DAO_DAU, DEG_SPAN_TILT);
        sendOk();
      } else Serial.println(F("ER cu phap U"));
      break;
    }

    case 'H': applyAngles(0.0, 0.0); sendOk(); break;
    case 'E': enableServos(true);    sendOk(); break;
    case 'D': enableServos(false);   sendOk(); break;
    case 'S': sendStatus();                    break;

    case 'L':
      digitalWrite(PIN_LED, s[1] == '1' ? HIGH : LOW);
      sendOk();
      break;

    case 'B':                                                                   
      if      (s[1] == '1') coiDat(true);
      else if (s[1] == '2') coiBip(2000, 120);
      else                  coiDat(false);
      sendOk();
      break;

    case 'Z': {                                                                 
      float n = atof(s + 1);
      digitalWrite(PIN_LED, HIGH);
      applyAngles(curPan + n, curTilt);
      Serial.print(F("OK ")); Serial.print(millis());
      Serial.print(F(" STEP ")); Serial.println(n, 2);
      delay(400);
      digitalWrite(PIN_LED, LOW);
      break;
    }

    case 'Q': {                                                             
      if (s[1] == '1') quetCham(sTilt, "TILT chan 3");
      else             quetCham(sPan,  "PAN chan 4");
      sendOk();
      break;
    }

    case 'C': {
      float a, b, c, d;
      if (parse4f(s + 1, &a, &b, &c, &d)) {
        panMin = a; panMax = b; tiltMin = c; tiltMax = d;
        sendOk();
      } else Serial.println(F("ER cu phap C"));
      break;
    }

    default:
      Serial.println(F("ER lenh la"));
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_COI, OUTPUT);
  noTone(PIN_COI);
  delay(300);

  Serial.println(F("# Arduino Uno R3 pan-tilt san sang"));
  Serial.println(F("# Lenh: A<p>,<t>  U<us>,<us>  H  E  D  S  Z<n>  L<0|1>  B<0|1|2>  C<..>"));
  Serial.println(F("# Chan: pan=4 tilt=3 led=13"));
  Serial.println(F("# Q0 quet cham pan, Q1 quet cham tilt"));
  Serial.println(F("# B0 tat coi, B1 hu bao dong, B2 bip ngan. Coi o chan 8"));

  sPan.attach(PIN_PAN,   US_MIN, US_MAX);
  sTilt.attach(PIN_TILT, US_MIN, US_MAX);
  sPan.writeMicroseconds(degToUs(0.0, PAN_DAO_DAU,  DEG_SPAN_PAN));
  sTilt.writeMicroseconds(degToUs(0.0, TILT_DAO_DAU, DEG_SPAN_TILT));
  enabled = true;
  Serial.println(F("# Da gan hai servo, dang o goc 0"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufLen > 0) {
        buf[bufLen] = '\0';
        handleLine(buf);
        bufLen = 0;
      }
    } else if (bufLen < sizeof(buf) - 1) {
      buf[bufLen++] = c;
    }
  }
  coiCapNhat();
}
