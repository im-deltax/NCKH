#pragma once
#include <Adafruit_GC9A01A.h>
#include <math.h>
#include "trang_thai.h"
#include "font_viet.h"

class GiaoDienTram {
  Adafruit_GC9A01A &lcd;
  GFXcanvas16 frame;
  static constexpr uint16_t BG = 0x0020;
  static constexpr uint16_t WHITE = 0xEF9B;
  static constexpr uint16_t GREY = 0x7C2F;

  static uint16_t rgb(int r, int g, int b) {
    return ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3);
  }
  static uint16_t dim(uint16_t c, int k) {
    return rgb(((c >> 11) & 31) * 255 / 31 * k / 255,
               ((c >> 5) & 63) * 255 / 63 * k / 255,
               (c & 31) * 255 / 31 * k / 255);
  }
  static float rad(float a) { return a * 0.01745329252f; }
  static uint16_t accent(TrangThai s) {
    if (s == TT_BAN) return rgb(166, 255, 78);
    if (s == TT_THU) return rgb(255, 74, 39);
    if (s == TT_MAT_SONG) return rgb(255, 185, 49);
    return rgb(99, 225, 200);
  }
  static void text(Adafruit_GFX &g, const char *s, int x, int y,
                   const VnFont &f, uint16_t c) {
    int lo = 127, hi = -127;
    const char *p = s;
    while (*p) {
      const VnGlyph *a = vnFind(f, vnNext(p));
      int h = pgm_read_byte(&a->h);
      int yy = (int8_t)pgm_read_byte(&a->y);
      if (h) { if (yy < lo) lo = yy; if (yy+h > hi) hi = yy+h; }
    }
    if (hi < lo) return;
    vnText(g, s, x-vnWidth(s,f)/2, y-(lo+hi)/2, f, c);
  }
  static void arc(Adafruit_GFX &g, int cx, int cy, int r,
                  int start, int sweep, int thick, uint16_t color) {
    for (int d=0; d<thick; ++d) {
      int rr=r-d;
      int px=cx+lroundf(rr*cosf(rad(start))), py=cy+lroundf(rr*sinf(rad(start)));
      for (int k=3; k<=sweep+2; k+=3) {
        int end = k < sweep ? k : sweep;
        int x=cx+lroundf(rr*cosf(rad(start+end))), y=cy+lroundf(rr*sinf(rad(start+end)));
        g.drawLine(px,py,x,y,color); px=x; py=y;
      }
    }
  }
  static void panel(Adafruit_GFX &g, int x, int y, int w, int h, int cut,
                    uint16_t fill, uint16_t line) {
    g.fillRect(x+cut,y,w-2*cut,h,fill);
    g.fillRect(x,y+cut,w,h-2*cut,fill);
    g.fillTriangle(x,y+cut,x+cut,y,x+cut,y+cut,fill);
    g.fillTriangle(x+w-1,y+cut,x+w-1-cut,y,x+w-1-cut,y+cut,fill);
    g.fillTriangle(x,y+h-1-cut,x+cut,y+h-1,x+cut,y+h-1-cut,fill);
    g.fillTriangle(x+w-1,y+h-1-cut,x+w-1-cut,y+h-1,x+w-1-cut,y+h-1-cut,fill);
    int xx[8]={x+cut,x+w-1-cut,x+w-1,x+w-1,x+w-1-cut,x+cut,x,x};
    int yy[8]={y,y,y+cut,y+h-1-cut,y+h-1,y+h-1,y+h-1-cut,y+cut};
    for(int i=0;i<8;++i) g.drawLine(xx[i],yy[i],xx[(i+1)%8],yy[(i+1)%8],line);
  }
  void brackets(int x, int y, int w, int h, int len, uint16_t color) {
    for(int d=0;d<2;++d) {
      frame.drawFastHLine(x,y+d,len,color);
      frame.drawFastVLine(x+d,y,len,color);
      frame.drawFastHLine(x+w-len,y+d,len,color);
      frame.drawFastVLine(x+w-1-d,y,len,color);
      frame.drawFastHLine(x,y+h-1-d,len,color);
      frame.drawFastVLine(x+d,y+h-len,len,color);
      frame.drawFastHLine(x+w-len,y+h-1-d,len,color);
      frame.drawFastVLine(x+w-1-d,y+h-len,len,color);
    }
  }
  void scaffold(TrangThai s, unsigned long now) {
    uint16_t c=accent(s);
    frame.fillScreen(BG);
    for(int y=48;y<=184;y+=12)
      for(int x=36;x<=204;x+=12)
        if((x-120)*(x-120)+(y-120)*(y-120)<96*96)
          frame.drawPixel(x,y,dim(c,38));
    frame.drawCircle(120,120,119,dim(c,55));
    frame.drawCircle(120,120,116,dim(c,95));
    for(int a=0;a<360;a+=5) {
      int r=a%30==0 ? 105 : a%15==0 ? 109 : 112;
      frame.drawLine(120+lroundf(r*cosf(rad(a))),120+lroundf(r*sinf(rad(a))),
                     120+lroundf(114*cosf(rad(a))),120+lroundf(114*sinf(rad(a))),
                     dim(c,a%30==0 ? 170 : 60));
    }
    int phase=(now/140)%8;
    for(int side=0;side<2;++side)
      for(int i=0;i<8;++i)
        arc(frame,120,120,118,side*180+36+i*5,3,2,dim(c,i==phase?255:100));
    frame.fillRect(77,12,86,20,BG);
    text(frame,"TRẠM · IFF",120,23,vnNho,WHITE);
    const char *badge=s==TT_BAN ? "ĐỊNH DANH ĐỒNG MINH" : s==TT_THU ? "CẢNH BÁO MỤC TIÊU" :
                       s==TT_MAT_SONG ? "MẤT TÍN HIỆU NRF" :
                       s==TT_DANG_HOI ? "LIÊN KẾT IFF ĐANG MỞ" : "CHẾ ĐỘ CHỜ";
    panel(frame,51,36,138,21,5,dim(c,20),dim(c,80));
    text(frame,badge,120,46,vnNho,c);
  }
  void scope(unsigned long t, bool active, uint16_t c) {
    const int x=120,y=112,r=49;
    float a=(t%3000)*0.12f-90;
    for(int i=60;i>0;i-=3) {
      int k=8+(60-i)*2;
      frame.fillTriangle(x,y,x+lroundf(r*cosf(rad(a-i))),y+lroundf(r*sinf(rad(a-i))),
                          x+lroundf(r*cosf(rad(a-i+3))),y+lroundf(r*sinf(rad(a-i+3))),dim(c,k));
    }
    for(int rr=12;rr<=48;rr+=12) frame.drawCircle(x,y,rr,dim(c,65));
    for(int z=-36;z<=36;z+=12) {
      int reach=(int)sqrtf(49*49-z*z);
      frame.drawFastHLine(x-reach,y+z,reach*2+1,dim(c,z==0?85:20));
      frame.drawFastVLine(x+z,y-reach,reach*2+1,dim(c,z==0?85:20));
    }
    frame.drawLine(x,y,x+lroundf(r*cosf(rad(a))),y+lroundf(r*sinf(rad(a))),c);
    frame.fillCircle(x,y,2,WHITE);
    arc(frame,x,y,54,192,64,2,dim(c,160));
    arc(frame,x,y,54,12,64,2,dim(c,160));
    int m=active ? 3+(int)(2*sinf(t/180.0f)) : 4;
    brackets(59-m,76,122+2*m,74,9,dim(c,130));
    text(frame,"IFF",42,109,vnNho,dim(c,145));
    text(frame,"C3",198,109,vnNho,dim(c,145));
    text(frame,active?"ĐANG HỎI":"SẴN SÀNG",120,181,vnVua,WHITE);
    text(frame,active?"Đang xác thực thẻ":"Chờ nhận diện thẻ",120,204,vnNho,c);
    for(int i=0;i<5;++i) frame.fillRect(96+i*10,219,7,2,dim(c,((t/180)%5)==(unsigned)i?255:65));
  }
  void telemetry(uint16_t c, unsigned long ms, uint8_t tries) {
    frame.drawFastHLine(62,190,116,dim(c,80));
    frame.drawFastVLine(120,196,25,dim(c,70));
    text(frame,"TRỄ/ms",89,199,vnNho,GREY);
    text(frame,"THỬ",151,199,vnNho,GREY);
    char value[24];
    if(ms<=9999) snprintf(value,sizeof(value),"%lu",ms);
    else snprintf(value,sizeof(value),">9s");
    text(frame,value,88,215,vnSo,WHITE);
    snprintf(value,sizeof(value),"%u",(unsigned)tries);
    text(frame,value,151,215,vnSo,WHITE);
  }
  void friendState(unsigned long elapsed, unsigned long now,
                   unsigned long ms, uint8_t tries) {
    uint16_t c=accent(TT_BAN);
    float enter=elapsed<650 ? elapsed/650.0f : 1.0f;
    int spread=(int)((1.0f-enter)*15);
    int glow=145+(int)(45*sinf(now/520.0f));
    arc(frame,120,116,62,204,132,2,dim(c,glow));
    arc(frame,120,116,62,24,132,2,dim(c,glow));
    brackets(43-spread,70-spread,154+2*spread,93+2*spread,18,c);

    int top=66-spread/2, side=38+spread;
    int vx[6]={120,120+side,120+side-5,120,120-side+5,120-side};
    int vy[6]={top,top+14,top+58,top+82,top+58,top+14};
    for(int i=1;i<5;++i)
      frame.fillTriangle(vx[0],vy[0],vx[i],vy[i],vx[i+1],vy[i+1],dim(c,20));
    for(int d=0;d<3;++d)
      for(int i=0;i<6;++i)
        frame.drawLine(vx[i],vy[i]+d,vx[(i+1)%6],vy[(i+1)%6]+d,dim(c,d?145:255));

    float q=elapsed<520 ? elapsed/520.0f : 1.0f;
    float p1=q<0.42f ? q/0.42f : 1.0f;
    float p2=q<=0.42f ? 0.0f : (q-0.42f)/0.58f;
    for(int d=-2;d<=2;++d) {
      frame.drawLine(94,105+d,94+lroundf(17*p1),105+d+lroundf(18*p1),WHITE);
      if(p2>0) frame.drawLine(111,123+d,111+lroundf(37*p2),123+d-lroundf(42*p2),WHITE);
    }
    int scan=78+(now/34)%60;
    frame.drawFastHLine(83,scan,74,dim(c,45));
    for(int i=0;i<4;++i) {
      int h=5+(int)((sinf(now/170.0f+i)*0.5f+0.5f)*12);
      frame.fillRect(57+i*4,142-h,2,h,dim(c,125));
      frame.fillRect(169+i*4,142-h,2,h,dim(c,125));
    }
    panel(frame,77,151,86,28,6,dim(c,25),dim(c,95));
    text(frame,"BẠN",120,165,vnVua,c);
    text(frame,"Xác thực hợp lệ",120,184,vnNho,WHITE);
    telemetry(c,ms,tries);
  }
  void hostileState(unsigned long elapsed, unsigned long now, const char *reason,
                    unsigned long ms, uint8_t tries) {
    uint16_t c=accent(TT_THU);
    static const int8_t shake[12]={0,2,-2,1,-1,3,-2,1,0,-1,2,-3};
    int sx=elapsed<1000 ? shake[(now/45)%12] : shake[(now/85)%12]/2;
    int sy=elapsed<1000 ? shake[(now/55+4)%12] : 0;
    int pulse=(int)(4+3*(0.5f+0.5f*sinf(now/115.0f)));
    int top=63-pulse+sy, bottom=146+pulse+sy;
    int left=62-pulse+sx, right=178+pulse+sx;

    for(int halo=8;halo>=2;halo-=2)
      frame.drawTriangle(120+sx,top-halo,left-halo,bottom+halo,right+halo,bottom+halo,
                         dim(c,22+halo*4));
    frame.fillTriangle(120+sx,top,left,bottom,right,bottom,dim(c,24));
    for(int d=0;d<3;++d)
      frame.drawTriangle(120+sx,top+d,left+d,bottom-d,right-d,bottom-d,d?dim(c,180):c);
    frame.fillRoundRect(116+sx,88+sy,9,29,4,WHITE);
    frame.fillCircle(120+sx,130+sy,5,WHITE);

    int phase=(now/75)%9;
    for(int i=0;i<9;++i) {
      uint16_t k=dim(c,i==phase?255:65);
      int y=70+i*9;
      frame.drawFastHLine(35,y,12,k);
      frame.drawFastHLine(193,y,12,k);
    }
    int sweep=73+(now/24)%68;
    frame.drawFastHLine(54,sweep,132,dim(c,95));
    frame.drawFastHLine(59,sweep+1,122,dim(c,45));
    for(int i=0;i<11;++i) {
      int x=67+i*10;
      uint16_t stripe=dim(c,((i+now/120)%5)==0?255:90);
      frame.drawLine(x,58,x+6,52,stripe);
      frame.drawLine(x,158,x+6,152,stripe);
    }
    text(frame,"THÙ",120,163,vnVua,WHITE);
    text(frame,reason,120,183,vnNho,c);
    telemetry(c,ms,tries);
  }
  void offline(unsigned long now, uint16_t c) {
    arc(frame,120,113,49,206,126,2,dim(c,125));
    arc(frame,120,113,49,26,126,2,dim(c,125));
    brackets(62,77,116,73,13,dim(c,180));
    panel(frame,71,97,29,31,6,dim(c,22),c);
    panel(frame,141,97,29,31,6,dim(c,22),c);
    frame.drawFastHLine(80,107,11,c);
    frame.drawFastHLine(80,116,11,c);
    frame.drawFastHLine(150,107,11,c);
    frame.drawFastHLine(150,116,11,c);
    frame.drawFastHLine(100,112,11,dim(c,100));
    frame.drawFastHLine(130,112,11,dim(c,100));
    frame.drawLine(116,103,123,110,c);
    frame.drawLine(116,110,123,103,c);
    int dot=(now/120)%9;
    for(int i=0;i<9;++i) frame.fillRect(84+i*8,141,4,2,dim(c,dot==i?255:65));
    text(frame,"KHÔNG TÌM THẤY",120,174,vnVua,c);
    text(frame,"Tín hiệu mô-đun NRF",120,201,vnNho,WHITE);
    text(frame,"ĐANG TÌM KẾT NỐI",120,222,vnNho,dim(c,150));
  }
  void fallback(TrangThai s, const char *reason) {
    lcd.fillScreen(BG);
    text(lcd,"TRẠM · IFF",120,50,vnNho,WHITE);
    const char *title=s==TT_BAN?"BẠN":s==TT_THU?"THÙ":s==TT_CHO?"SẴN SÀNG":
                       s==TT_DANG_HOI?"ĐANG HỎI":"MẤT SÓNG";
    text(lcd,title,120,113,s==TT_BAN||s==TT_THU?vnLon:vnVua,accent(s));
    text(lcd,s==TT_THU?reason:"Giao diện tĩnh",120,168,vnNho,WHITE);
  }
public:
  explicit GiaoDienTram(Adafruit_GC9A01A &screen) : lcd(screen), frame(240,240) {}
  void boot() {
    lcd.fillScreen(BG);
    text(lcd,"IFF",120,101,vnLon,accent(TT_CHO));
    text(lcd,"Đang khởi động",120,155,vnNho,WHITE);
    if(!frame.getBuffer()) Serial.println("[UI] Thieu RAM: dung giao dien tinh.");
  }
  void draw(TrangThai s, unsigned long elapsed, unsigned long now,
            bool changed, bool updated, const char *reason, unsigned long ms, uint8_t tries) {
    if(!frame.getBuffer()) { if(changed||updated) fallback(s,reason); return; }
    scaffold(s,now);
    if(s==TT_CHO||s==TT_DANG_HOI) scope(now,s==TT_DANG_HOI,accent(s));
    else if(s==TT_MAT_SONG) offline(now,accent(s));
    else if(s==TT_BAN) friendState(elapsed,now,ms,tries);
    else hostileState(elapsed,now,reason,ms,tries);
    lcd.drawRGBBitmap(0,0,frame.getBuffer(),240,240);
  }
};
