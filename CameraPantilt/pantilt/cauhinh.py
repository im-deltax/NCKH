
import numpy as np

ANH_W, ANH_H = 640, 480

F_U = 860.6                                             
F_V = 860.6                                                    
C_U = ANH_W / 2.0                                        
C_V = ANH_H / 2.0


D_DE     = 0.095                                  
A_CAN    = 0.020                                                 
H_CAM    = 0.053                                     

PAN_MIN,  PAN_MAX  = -70.0, 70.0        
TILT_MIN, TILT_MAX = -55.0, 55.0                                              

SIGMA_U_PX = 3.60                                                        
SIGMA_V_PX = 3.76

SIGMA_THETA = np.degrees(SIGMA_U_PX / F_U)       
SIGMA_PHI   = np.degrees(SIGMA_V_PX / F_V)

SIGMA_A = 24.0                                                          

T_D = 0.1155                               
T_CAP = 0.0163          
OMEGA_C_MAX = 0.785 / T_D                                                     

SERVO_K = 1.0                                                          
SERVO_T = 0.0450                           
SERVO_L = 0.0955                   
KHE_HO_DEG = 0.95                                                              

DUNG_MO_HINH_SERVO = True

KP  = 5.0                 
KI  = 0.0
KD  = 0.15
KFF = 0.45

V_FF_MAX = 40.0            
TAU_FF   = 0.30         

N_LOC_VP = 15.0                              

DEADBAND_DEG = 1.00
OMEGA_MAX    = 120.0                                     

BIEN_CANH_BAO   = 1.5        
BIEN_THOI_GIAN_S = 2.5         

MODEL_PATH = "mo_hinh/best.pt"
BACKEND    = "openvino"
IMGSZ      = 640

CONF       = 0.35
CAM_INDEX  = 1

N_MAT_TOI_DA = 5


V_MUC_TIEU_MAX = 60.0              

TAU_TRUOT_S = 0.20

NGOAI_SUY_MAX_DEG = 10.0

T_VE_GOC_S = 1.5
GOC_NGHI_PAN = 0.0

GOC_NGHI_TILT = -13.0

RONG_O_HUONG_DEG = 15.0                                                    
SO_DIEM_QUET = 6                                                           
T_DUNG_QUET_S = 1.5                                                          

BUOC_QUET_DEG = 30.0
LE_QUET_DEG = 5.0                                                            

T_ON_DINH_S = 3.0

LIDAR_URL = "http://127.0.0.1:8770/stream"

LIDAR_D_M = 0.09

LIDAR_LECH_GOC_DEG = 8.388

LIDAR_DAO_DAU = True

LIDAR_CHENH_CAO_M = -0.062

LIDAR_HET_HAN_S = 0.8

LIDAR_TOC_DO_MIN = 0.05         

CHO_LIDAR_KICH_HOAT = True

T_VE_CHO_S = 3.0

NGU_KHI_CHO = True

QUET_TU_DAU = False

GIA_TOC_MAX = 400.0


K_KIEM_DINH_V = 2.0

NGUONG_GUI_DEG = 0.10

CONG_HOP_LE_PX = 140.0
CONG_NOI_PX    = 60.0

COM_PORT = "COM13"                                          
BAUD     = 115200
TAN_SO_DIEU_KHIEN = 50.0       

THU_MUC_LOG = "log"
GHI_LOG = True

IFF_PORT = "COM18"
IFF_BAUD = 115200

IFF_CHO_KHOI_DONG_S = 0.25

IFF_SO_LAN_HOI = 2

IFF_HAN_CHO_S = 0.8

IFF_HAN_NHO_S = 20.0

IFF_TRE_ROI_VUNG_S = 1.0

IFF_KE_THUA_S = 1.5

CANH_BAO_CFG = "canh_bao_bi_mat.json"

CONG_WEB = 8780
