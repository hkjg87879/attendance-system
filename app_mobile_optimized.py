import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time, timedelta
import os
import hashlib
import pytz
from streamlit_option_menu import option_menu
import altair as alt
import calendar
import json
import math
import base64
import hmac
import hashlib as _hashlib
import time as time_module
from dateutil.relativedelta import relativedelta
import subprocess
import sys
import numpy as np
from PIL import Image
import io

# Import face recognition module
try:
    from face_recognition_module import extract_face_encoding, verify_face_match, FACE_RECOGNITION_AVAILABLE
    import face_recognition  # 导入原始库以直接使用
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# --- 系统配置 ---
COMPANY_NAME = "企业考勤管理系统"
DB_FILE = 'attendance.db'
EXPECTED_START_TIME = time(9, 0, 0)
EXPECTED_END_TIME = time(18, 0, 0)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
QR_SECRET_KEY = "attendance_qr_secret_2024"

# 页面配置
st.set_page_config(
    page_title=COMPANY_NAME,
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 移动端检测 ---
def is_mobile():
    return st.session_state.get('is_mobile', False)


# --- 自定义CSS样式 ---
def load_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {display: none;}
        [data-testid="stAppDeployButton"] {display: none !important;}

        [data-testid="stSidebar"] {
            background: #0F172A;
            color: #ffffff;
        }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        [data-testid="stSidebar"] .stButton > button {
            background-color: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255,255,255,0.2);
        }
        button[kind="secondary"][aria-label="Collapse sidebar"],
        button[kind="secondary"][aria-label="Expand sidebar"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebar"] button[kind="secondary"],
        button[data-testid="baseButton-header"] {
            z-index: 1000000 !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            position: relative !important;
            width: auto !important;
            height: auto !important;
        }
        .login-container {
            background: transparent;
            padding: 2.2rem 2rem 1.6rem;
            border-radius: 16px;
            box-shadow: none;
            border: none;
            max-width: 520px;
            margin: auto;
            color: #111827;
            position: relative;
            z-index: 2;
        }
        .login-bg {
            position: fixed;
            inset: 0;
            background:
                linear-gradient(135deg, rgba(8,132,248,0.10) 0%, rgba(7,154,245,0.06) 50%, rgba(255,255,255,0.0) 100%),
                url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 400'><g fill='%2394A3B8' fill-opacity='0.32'><rect x='20' y='190' width='140' height='210'/><rect x='180' y='140' width='160' height='260'/><rect x='360' y='210' width='110' height='190'/><rect x='490' y='120' width='170' height='280'/><rect x='690' y='170' width='140' height='230'/><rect x='850' y='130' width='120' height='270'/><rect x='990' y='200' width='160' height='200'/></g></svg>");
            background-repeat: no-repeat;
            background-position: center bottom;
            background-size: 1400px auto;
            z-index: 1;
            pointer-events: none;
        }
        .login-title {
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 0.3rem;
            white-space: nowrap;
        }
        .register-inline {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 13px;
            color: #6B7280;
            white-space: nowrap;
        }
        .register-inline a {
            color: #6B7280;
            text-decoration: none;
            font-weight: 400;
        }
        .register-inline a:hover { color: #EF4444; }
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border: none;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 6px 12px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1a56db;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            font-size: 1rem;
            color: #4b5563;
            font-weight: 500;
        }
        .stButton > button {
            background-color: #0D6EFD;
            color: #ffffff;
            border: 1px solid #0D6EFD;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: 600;
            transition: background-color 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #0B5ED7;
            border-color: #0B5ED7;
            box-shadow: 0 6px 12px rgba(13,110,253,0.2);
        }

        /* ===== 退出登录红色按钮（修复版）===== */
        /* 使用 :has() 选择器定位 logout-btn-marker 后的按钮 */
        [data-testid="stMarkdown"]:has(.logout-btn-marker) + div button,
        [data-testid="stMarkdown"]:has(.logout-btn-marker) + [data-testid="stButton"] button {
            background-color: #dc3545 !important;
            border-color: #dc3545 !important;
            color: #ffffff !important;
        }
        [data-testid="stMarkdown"]:has(.logout-btn-marker) + div button:hover,
        [data-testid="stMarkdown"]:has(.logout-btn-marker) + [data-testid="stButton"] button:hover {
            background-color: #bb2d3b !important;
            border-color: #b02a37 !important;
            box-shadow: 0 6px 12px rgba(220,53,69,0.3) !important;
        }
        /* 兼容旧方式 */
        .logout-button-container .stButton > button {
            background-color: #dc3545 !important;
            border-color: #dc3545 !important;
        }
        .logout-button-container .stButton > button:hover {
            background-color: #bb2d3b !important;
            border-color: #b02a37 !important;
        }

        .dataframe {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            width: 100%;
        }
        .stForm {
            background: #ffffff;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.06);
        }
        .stTextInput, .stPassword, .stDateInput, .stNumberInput { width: 100%; }
        .stTextInput [data-baseweb="input"],
        .stPassword [data-baseweb="input"],
        .stDateInput [data-baseweb="input"],
        .stNumberInput [data-baseweb="input"] {
            width: 100%;
            border: 1px solid #D1D5DB;
            border-radius: 10px;
            box-shadow: none;
        }
        .stTextInput input, .stPassword input, .stDateInput input, .stNumberInput input {
            border: none !important;
            height: 50px;
            padding: 10px 12px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }
        .stPassword input { padding-right: 44px; }
        .stPassword [data-baseweb="endEnhancer"] {
            min-width: 36px;
            max-width: 36px;
            justify-content: center;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-normal { background-color: #d1fae5; color: #065f46; }
        .status-late { background-color: #fee2e2; color: #991b1b; }
        .status-early { background-color: #fff3cd; color: #856404; }
        .status-late-early { background-color: #fef3c7; color: #92400e; }
        .status-pending { background-color: #fef3c7; color: #92400e; }
        .status-approved { background-color: #d1fae5; color: #065f46; }
        .status-rejected { background-color: #fee2e2; color: #991b1b; }
        .app-header {
            position: sticky;
            top: 0;
            z-index: 10;
            background: #FFFFFF;
            border-bottom: 1px solid #E5E7EB;
            padding: 12px 24px;
            border-radius: 12px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .app-header .title { font-size: 20px; font-weight: 700; color: #111827; }
        .app-header .sub { font-size: 14px; color: #6B7280; }

        /* ===== 打卡方式按钮 - 统一方块，两行文字 ===== */
        .method-btn-row .stButton > button {
            height: 64px !important;
            min-height: 64px !important;
            max-height: 64px !important;
            padding: 8px 4px !important;          /* 增加上下内边距 */
            font-size: 14px !important;           /* 稍大一点的字号 */
            line-height: 1.4 !important;
            white-space: pre-line !important;      /* 允许换行 */
            overflow: visible !important;          /* 防止文字被裁切 */
            text-overflow: clip !important;
            display: flex !important;
            flex-direction: column !important;     /* 垂直排列 */
            align-items: center !important;
            justify-content: center !important;
            word-break: break-word !important;
            text-align: center !important;
        }
        /* 选中状态高亮 */
        .method-btn-active .stButton > button {
            background-color: #0884F8 !important;
            border-color: #0884F8 !important;
            box-shadow: 0 4px 12px rgba(8,132,248,0.3) !important;
        }
        .method-btn-normal .stButton > button {
            background-color: #ffffff !important;
            color: #374151 !important;
            border-color: #D1D5DB !important;
        }
        .method-btn-normal .stButton > button:hover {
            background-color: #EFF6FF !important;
            border-color: #0D6EFD !important;
            color: #0D6EFD !important;
        }

        /* GPS状态指示 */
        .gps-status-ok { color: #065f46; background: #d1fae5; padding: 8px 16px; border-radius: 8px; }
        .gps-status-warning { color: #92400e; background: #fef3c7; padding: 8px 16px; border-radius: 8px; }
        .gps-status-error { color: #991b1b; background: #fee2e2; padding: 8px 16px; border-radius: 8px; }
        /* 人脸识别样式 */
        .face-container {
            border: 2px dashed #D1D5DB;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            background: #F9FAFB;
        }
        /* 二维码样式 */
        .qr-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: white;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
        }
        @media (max-width: 768px) {
            .app-header { flex-direction: column; gap: 8px; padding: 10px 16px; border-radius: 8px; }
            .app-header .title { font-size: 18px; }
            .app-header .sub { font-size: 12px; }
            [data-testid="column"] { display: block !important; width: 100% !important; margin-bottom: 8px; }
            .dataframe { font-size: 12px; overflow-x: auto; }
            input, textarea, select { font-size: 16px !important; }
            .stButton > button { padding: 12px 16px !important; min-height: 44px !important; font-size: 15px !important; border-radius: 8px !important; }
            .login-container { padding: 1.5rem 1.2rem; max-width: 100%; margin: 0 16px; }
            .metric-value { font-size: 1.8rem; }
            .metric-label { font-size: 0.9rem; }
            .stForm { padding: 16px; border-radius: 12px; }
        }
        @media (max-width: 480px) {
            .app-header .title { font-size: 16px; }
            .app-header .sub { font-size: 11px; }
            .metric-value { font-size: 1.5rem; }
            .metric-label { font-size: 0.85rem; }
            .stButton > button { font-size: 13px; padding: 10px 12px !important; min-height: 40px !important; }
            .login-title { font-size: 22px; }
            .login-container { padding: 1.2rem 1rem; }
            .stForm { padding: 12px; }
            .status-badge { font-size: 10px; padding: 3px 8px; }
            h1 { font-size: 1.3em !important; }
            h2 { font-size: 1.1em !important; }
            h3 { font-size: 1em !important; }
        }
        </style>
    """, unsafe_allow_html=True)


load_css()


# ==================== 数据库初始化 ====================

def init_db_if_not_exists():
    """初始化数据库"""
    if not os.path.exists(DB_FILE):
        try:
            import init_db
            init_db.init_db()
        except ImportError:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            init_script = os.path.join(script_dir, 'init_db.py')
            if os.path.exists(init_script):
                try:
                    subprocess.run([sys.executable, init_script], check=True)
                except Exception as e:
                    print(f"数据库初始化失败: {e}")
            else:
                print("找不到 init_db.py，无法初始化数据库")
        except Exception as e:
            print(f"数据库初始化失败: {e}")

    _migrate_db()


def _migrate_db():
    """数据库迁移：为已有数据库添加新功能所需的字段和表"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            # 1. attendance 表扩展字段
            existing_att_cols = [row[1] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()]
            att_new_cols = {
                "checkin_method": "TEXT DEFAULT 'manual'",
                "latitude": "REAL",
                "longitude": "REAL",
                "location_name": "TEXT",
                "face_verified": "INTEGER DEFAULT 0",
                "checkout_method": "TEXT DEFAULT 'manual'",
                "checkout_latitude": "REAL",
                "checkout_longitude": "REAL",
            }
            for col_name, col_def in att_new_cols.items():
                if col_name not in existing_att_cols:
                    conn.execute(f"ALTER TABLE attendance ADD COLUMN {col_name} {col_def}")

            # 2. 办公地点表（GPS围栏配置）
            conn.execute('''CREATE TABLE IF NOT EXISTS office_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                radius_meters INTEGER DEFAULT 200,
                wifi_ssid TEXT,
                address TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )''')
            # 为已有 office_locations 添加 sort_order 列
            existing_office_cols = [row[1] for row in conn.execute("PRAGMA table_info(office_locations)").fetchall()]
            if 'sort_order' not in existing_office_cols:
                conn.execute("ALTER TABLE office_locations ADD COLUMN sort_order INTEGER DEFAULT 0")
                conn.execute("UPDATE office_locations SET sort_order = id")

            # 3. 人脸特征表
            conn.execute('''CREATE TABLE IF NOT EXISTS face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                face_data TEXT,
                registered_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            
            # 为 attendance 表添加 face_score 字段（如果不存在）
            existing_att_cols = [row[1] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()]
            if 'face_score' not in existing_att_cols:
                conn.execute("ALTER TABLE attendance ADD COLUMN face_score REAL")

            # 4. 二维码打卡表
            conn.execute('''CREATE TABLE IF NOT EXISTS qr_checkin_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                checkin_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

            # 5. users 表添加 sort_order
            existing_user_cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
            if 'sort_order' not in existing_user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN sort_order INTEGER DEFAULT 0")
                conn.execute("UPDATE users SET sort_order = id")

            conn.commit()
    except Exception as e:
        print(f"数据库迁移警告: {e}")


init_db_if_not_exists()


# ==================== 工具函数 ====================

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_office_locations():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query(
                "SELECT * FROM office_locations WHERE is_active = 1 ORDER BY sort_order, id", conn)
        return df
    except Exception:
        return pd.DataFrame()


def check_location_in_office(lat, lon):
    locations = get_office_locations()
    if locations.empty:
        return None, 99999
    best_location = None
    min_dist = float('inf')
    for _, loc in locations.iterrows():
        dist = haversine_distance(lat, lon, loc['latitude'], loc['longitude'])
        if dist < min_dist:
            min_dist = dist
            best_location = loc
    if best_location is not None and min_dist <= best_location['radius_meters']:
        return best_location['name'], min_dist
    return None, min_dist


def generate_qr_token(user_id, checkin_type):
    timestamp = int(time_module.time())
    payload = f"{user_id}:{checkin_type}:{timestamp}"
    signature = hmac.new(QR_SECRET_KEY.encode(), payload.encode(), _hashlib.sha256).hexdigest()[:16]
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()
    return token, timestamp


def verify_qr_token(token, max_age_seconds=60):
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.rsplit(':', 1)
        if len(parts) != 2:
            return None, None, "令牌格式错误"
        payload, signature = parts
        expected_sig = hmac.new(QR_SECRET_KEY.encode(), payload.encode(), _hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(signature, expected_sig):
            return None, None, "令牌签名无效"
        p_parts = payload.split(':')
        if len(p_parts) != 3:
            return None, None, "令牌数据错误"
        user_id, checkin_type, timestamp = int(p_parts[0]), p_parts[1], int(p_parts[2])
        if int(time_module.time()) - timestamp > max_age_seconds:
            return None, None, "令牌已过期（超过60秒）"
        return user_id, checkin_type, None
    except Exception as e:
        return None, None, f"令牌解析失败: {e}"


def generate_qr_image_html(token):
    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;padding:20px;">
        <div id="qrcode_{token[:8]}"></div>
        <p style="margin-top:12px;font-size:12px;color:#6B7280;">二维码60秒后失效，请尽快扫描</p>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <script>
    (function(){{
        var el = document.getElementById('qrcode_{token[:8]}');
        if(el && typeof QRCode !== 'undefined'){{
            new QRCode(el, {{
                text: '{token}',
                width: 200,
                height: 200,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.M
            }});
        }}
    }})();
    </script>
    """


# ==================== 数据库操作函数 ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username, password):
    try:
        admin_user = st.secrets.get("ADMIN_USER")
        admin_pass = st.secrets.get("ADMIN_PASSWORD")
        if admin_user and admin_pass and username == admin_user and password == admin_pass:
            return {
                'id': -1, 'username': admin_user, 'name': '超级管理员',
                'role': 'admin', 'department': '管理部',
                'department_id': None, 'email': '', 'phone': ''
            }
    except Exception:
        pass
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute('''
                SELECT u.*, d.name as department 
                FROM users u 
                LEFT JOIN departments d ON u.department_id = d.id 
                WHERE u.username = ?
            ''', (username,)).fetchone()
            if user and user['password'] == hash_password(password):
                return dict(user)
    except Exception:
        pass
    return None


def log_action(user_id, action, detail='', ip=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO logs (user_id, action, detail, ip, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, action, detail, ip, datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
    except Exception:
        pass


def register_user(username, password, name, department_id=None, email=None, phone=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            if exists:
                return False, "用户名已存在"
            # 获取当前最大 sort_order
            max_order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) FROM users").fetchone()[0]
            conn.execute(
                "INSERT INTO users (username, password, role, name, department_id, email, phone, hire_date, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (username, hash_password(password), "employee", name, department_id, email, phone,
                 datetime.now(BEIJING_TZ).strftime("%Y-%m-%d"), max_order + 1),
            )
            conn.commit()
        return True, "注册成功，请使用新账号登录"
    except Exception as e:
        return False, f"注册失败: {e}"


def update_user(user_id, username, name, department_id, role, email=None, phone=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                UPDATE users 
                SET username=?, name=?, department_id=?, role=?, email=?, phone=?
                WHERE id=?
            """, (username, name, department_id, role, email, phone, user_id))
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, f"更新失败: {e}"


def delete_user(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM leaves WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM overtime WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM logs WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM face_encodings WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        return False, f"删除失败: {e}"


def get_attendance_status(user_id, date_str):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            record = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?',
                                  (user_id, date_str)).fetchone()
            return dict(record) if record else None
    except Exception:
        return None


def clock_in(user_id, date_str, time_str, method='manual', latitude=None, longitude=None,
             location_name=None, face_verified=0, face_score=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            existing = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?',
                                    (user_id, date_str)).fetchone()
            if existing:
                return False, "今日已打卡"
            check_in_dt = datetime.strptime(time_str, "%H:%M:%S").time()
            status = "正常" if check_in_dt <= EXPECTED_START_TIME else "迟到"
            conn.execute('''INSERT INTO attendance 
                (user_id, date, check_in, status, checkin_method, latitude, longitude, location_name, face_verified, face_score) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (user_id, date_str, time_str, status, method, latitude, longitude, location_name, face_verified, face_score))
            conn.commit()
        method_label = {'manual': '手动', 'face': '人脸识别', 'gps': 'GPS 定位',
                        'qr': '扫码'}.get(method, method)
        score_info = f" 相似度:{face_score:.2%}" if face_score else ""
        log_action(user_id, '上班打卡',
                   f'方式:{method_label} 时间:{time_str} 状态:{status} 地点:{location_name or "未知"}{score_info}')
        return True, f"打卡成功（{method_label}）" if status == "正常" else f"已记录迟到（{method_label}）"
    except Exception as e:
        return False, f"打卡失败：{e}"


def clock_out(user_id, date_str, time_str, method='manual', latitude=None, longitude=None, face_score=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            record = conn.execute('SELECT check_in, status FROM attendance WHERE user_id = ? AND date = ?',
                                  (user_id, date_str)).fetchone()
            if not record:
                return False, "请先完成上班打卡"
            conn.execute('''UPDATE attendance 
                SET check_out=?, checkout_method=?, checkout_latitude=?, checkout_longitude=?, face_score=?
                WHERE user_id=? AND date=?''',
                         (time_str, method, latitude, longitude, face_score, user_id, date_str))
            check_out_time = datetime.strptime(time_str, "%H:%M:%S").time()
            current_status = record[1]
            new_status = current_status
            if check_out_time < EXPECTED_END_TIME:
                new_status = "迟到早退" if current_status == "迟到" else "早退"
            if new_status != current_status:
                conn.execute('UPDATE attendance SET status = ? WHERE user_id = ? AND date = ?',
                             (new_status, user_id, date_str))
            conn.commit()
        method_label = {'manual': '手动', 'face': '人脸识别', 'gps': 'GPS 定位',
                        'qr': '扫码'}.get(method, method)
        score_info = f" 相似度:{face_score:.2%}" if face_score else ""
        log_action(user_id, '下班打卡', f'方式:{method_label} 时间:{time_str}{score_info}')
        return True, "下班打卡成功"
    except Exception as e:
        return False, f"下班打卡失败: {e}"


def get_all_attendance():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            # 检查新列是否存在
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()]
            has_new_cols = 'checkin_method' in existing_cols

            if has_new_cols:
                query = """
                    SELECT a.id, u.name, d.name as department, a.date, a.check_in, a.check_out, 
                           a.status, a.checkin_method, a.location_name, a.face_verified
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    LEFT JOIN departments d ON u.department_id = d.id
                    ORDER BY a.date DESC, a.check_in ASC
                """
            else:
                query = """
                    SELECT a.id, u.name, d.name as department, a.date, a.check_in, a.check_out, a.status
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    LEFT JOIN departments d ON u.department_id = d.id
                    ORDER BY a.date DESC, a.check_in ASC
                """
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return pd.DataFrame()


def get_departments():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query("SELECT id, name, description FROM departments ORDER BY name", conn)
        return df
    except Exception:
        return pd.DataFrame()


def get_attendance_rules():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query("SELECT * FROM attendance_rules WHERE is_active = 1", conn)
        return df
    except Exception:
        return pd.DataFrame()


def calculate_work_hours(check_in_str, check_out_str):
    if not check_in_str or not check_out_str:
        return 0
    try:
        check_in = datetime.strptime(check_in_str, "%H:%M:%S")
        check_out = datetime.strptime(check_out_str, "%H:%M:%S")
        hours = (check_out - check_in).total_seconds() / 3600
        lunch_start = datetime.strptime("12:00:00", "%H:%M:%S")
        lunch_end = datetime.strptime("13:30:00", "%H:%M:%S")
        if check_in < lunch_end and check_out > lunch_start:
            hours -= 1.5
        return max(0, round(hours, 2))
    except Exception:
        return 0


def apply_leave(user_id, leave_type, start_date, end_date, reason):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        created_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO leaves (user_id, leave_type, start_date, end_date, days, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, leave_type, start_date, end_date, days, reason, created_at))
            conn.commit()
        log_action(user_id, '申请请假', f'{leave_type} {start_date}~{end_date} 共{days}天')
        return True, "请假申请提交成功"
    except Exception as e:
        return False, f"提交失败: {str(e)}"


def get_leave_applications(user_id=None, status=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            query = """
                SELECT l.*, u.name as applicant_name, d.name as department_name, 
                       u2.name as approver_name
                FROM leaves l
                JOIN users u ON l.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                LEFT JOIN users u2 ON l.approved_by = u2.id
            """
            params = []
            conditions = []
            if user_id:
                conditions.append("l.user_id = ?")
                params.append(user_id)
            if status:
                conditions.append("l.status = ?")
                params.append(status)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY l.created_at DESC"
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception:
        return pd.DataFrame()


def apply_overtime(user_id, date, hours, reason):
    try:
        created_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO overtime (user_id, date, hours, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, date, hours, reason, created_at))
            conn.commit()
        log_action(user_id, '申请加班', f'{date} 加班{hours}小时')
        return True, "加班申请提交成功"
    except Exception as e:
        return False, f"提交失败: {str(e)}"


def get_overtime_applications(user_id=None, status=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            query = """
                SELECT o.*, u.name as applicant_name, d.name as department_name,
                       u2.name as approver_name
                FROM overtime o
                JOIN users u ON o.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                LEFT JOIN users u2 ON o.approved_by = u2.id
            """
            params = []
            conditions = []
            if user_id:
                conditions.append("o.user_id = ?")
                params.append(user_id)
            if status:
                conditions.append("o.status = ?")
                params.append(status)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY o.created_at DESC"
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception:
        return pd.DataFrame()


def approve_overtime(overtime_id, approver_id, action):
    try:
        status = 'approved' if action == 'approve' else 'rejected'
        now = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                UPDATE overtime SET status = ?, approved_by = ?, approved_at = ?
                WHERE id = ?
            """, (status, approver_id, now, overtime_id))
            conn.commit()
        log_action(approver_id, '审批加班', f'加班申请 {overtime_id} 状态 {status}')
        return True
    except Exception:
        return False


def get_monthly_attendance_stats(year, month):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            query = """
                SELECT 
                    u.id, u.name, u.department_id, d.name as department_name,
                    COUNT(a.id) as attendance_days,
                    SUM(CASE WHEN a.status IN ('正常') THEN 1 ELSE 0 END) as normal_days,
                    SUM(CASE WHEN a.status IN ('迟到','迟到早退') THEN 1 ELSE 0 END) as late_days,
                    SUM(CASE WHEN a.status IN ('早退','迟到早退') THEN 1 ELSE 0 END) as early_leave_days,
                    SUM(CASE WHEN a.status = '缺勤' THEN 1 ELSE 0 END) as absent_days
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                LEFT JOIN attendance a ON u.id = a.user_id 
                    AND strftime('%Y', a.date) = ? 
                    AND strftime('%m', a.date) = ?
                WHERE u.role = 'employee'
                GROUP BY u.id, u.name, u.department_id, d.name
                ORDER BY d.name, u.name
            """
            df = pd.read_sql_query(query, conn, params=(str(year), f"{month:02d}"))
        return df
    except Exception:
        return pd.DataFrame()


def get_attendance_trend(days=30):
    try:
        end_date = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        start_date = (datetime.now(BEIJING_TZ) - timedelta(days=days)).strftime("%Y-%m-%d")
        with sqlite3.connect(DB_FILE) as conn:
            query = """
                SELECT 
                    date,
                    COUNT(*) as total_attendance,
                    SUM(CASE WHEN status IN ('正常') THEN 1 ELSE 0 END) as normal_count,
                    SUM(CASE WHEN status IN ('迟到','迟到早退') THEN 1 ELSE 0 END) as late_count,
                    SUM(CASE WHEN status IN ('早退','迟到早退') THEN 1 ELSE 0 END) as early_leave_count
                FROM attendance
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        return df
    except Exception:
        return pd.DataFrame()


def get_logs(user_id=None, limit=100):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            query = """
                SELECT l.*, u.name as user_name
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.created_at DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    except Exception:
        return pd.DataFrame()


def update_attendance_record(record_id, check_in=None, check_out=None, status=None, notes=None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            updates = []
            params = []
            if check_in is not None:
                updates.append("check_in = ?"); params.append(check_in)
            if check_out is not None:
                updates.append("check_out = ?"); params.append(check_out)
            if status is not None:
                updates.append("status = ?"); params.append(status)
            if notes is not None:
                updates.append("notes = ?"); params.append(notes)
            if updates:
                query = f"UPDATE attendance SET {', '.join(updates)} WHERE id = ?"
                params.append(record_id)
                conn.execute(query, params)
                conn.commit()
        return True
    except Exception:
        return False


def get_month_calendar_data(user_id, year, month):
    try:
        start_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day}"
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query("""
                SELECT date, status
                FROM attendance
                WHERE user_id = ? AND date BETWEEN ? AND ?
            """, conn, params=(user_id, start_date, end_date))
        return df
    except Exception:
        return pd.DataFrame()


def save_face_data(user_id, face_data_json):
    try:
        now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_FILE) as conn:
            existing = conn.execute("SELECT id FROM face_encodings WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                conn.execute("UPDATE face_encodings SET face_data=?, registered_at=? WHERE user_id=?",
                             (face_data_json, now, user_id))
            else:
                conn.execute("INSERT INTO face_encodings (user_id, face_data, registered_at) VALUES (?,?,?)",
                             (user_id, face_data_json, now))
            conn.commit()
        return True
    except Exception:
        return False


def has_face_registered(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute("SELECT id FROM face_encodings WHERE user_id = ? AND face_data IS NOT NULL",
                               (user_id,)).fetchone()
        return row is not None
    except Exception:
        return False


def extract_face_encoding_from_image(image_data):
    """从图像数据中提取人脸特征向量"""
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    try:
        # 处理不同类型的输入数据
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Base64 编码的图片
            base64_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif isinstance(image_data, str):
            # 文件路径
            image = Image.open(image_data)
        elif hasattr(image_data, 'seek') and hasattr(image_data, 'read'):
            # UploadedFile 或文件对象 - 关键修复！
            # 重置文件指针到开头
            image_data.seek(0)
            # 读取字节
            image_bytes = image_data.read()
            # 使用 PIL 打开
            image = Image.open(io.BytesIO(image_bytes))
            # 重置原始文件指针（可能后续还需要）
            image_data.seek(0)
        else:
            # 已经是 PIL Image 对象
            image = image_data
        
        # 转换为 RGB（确保）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_array = np.array(image)
        
        # 确保是 3 通道
        if len(image_array.shape) == 2:
            # 灰度图转换为 RGB
            image_array = np.stack([image_array] * 3, axis=-1)
        elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
            # RGBA 转换为 RGB
            image_array = image_array[:, :, :3]
        
        # 首先尝试 HOG 模型（快速）
        face_locations = face_recognition.face_locations(image_array, model='hog')
        
        # 如果 HOG 失败，尝试 CNN 模型（更准确，但更慢）
        if not face_locations:
            print(f"HOG 未检测到人脸，尝试 CNN 模型...")
            print(f"  图像尺寸：{image_array.shape}")
            print(f"  图像数据类型：{image_array.dtype}")
            print(f"  像素范围：{image_array.min()}-{image_array.max()}")
            face_locations = face_recognition.face_locations(image_array, model='cnn')
        
        if not face_locations:
            return None
        
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if face_encodings:
            return face_encodings[0].tolist()
        
        return None
        
    except Exception as e:
        print(f"提取人脸特征失败：{e}")
        import traceback
        traceback.print_exc()
        return None


def verify_face_match(known_encoding, current_image_data, tolerance=0.6):
    """验证当前人脸是否与注册的人脸匹配"""
    if not FACE_RECOGNITION_AVAILABLE:
        return False, 0.0
    
    try:
        current_encoding = extract_face_encoding_from_image(current_image_data)
        
        if current_encoding is None:
            return False, 0.0
        
        known_array = np.array(known_encoding)
        current_array = np.array(current_encoding)
        
        distance = np.linalg.norm(known_array - current_array)
        similarity = 1.0 / (1.0 + distance)
        is_match = distance <= tolerance
        
        return is_match, similarity
        
    except Exception as e:
        print(f"人脸比对失败：{e}")
        return False, 0.0


def get_user_face_encoding(user_id):
    """从数据库获取用户的人脸特征向量"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute(
                "SELECT face_data FROM face_encodings WHERE user_id = ? AND face_data IS NOT NULL",
                (user_id,)
            ).fetchone()
            
            if row and row[0]:
                face_data = json.loads(row[0])
                # 返回 face_encoding 字段，而不是整个 JSON 对象
                return face_data.get('face_encoding')
            return None
    except Exception:
        return None


def reorder_users(user_id_order_list):
    """批量更新用户排序（传入 [(user_id, new_sort_order), ...]）"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            for uid, order in user_id_order_list:
                conn.execute("UPDATE users SET sort_order = ? WHERE id = ?", (order, uid))
            conn.commit()
        return True
    except Exception:
        return False


def reorder_offices(office_id_order_list):
    """批量更新办公地点排序"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            for oid, order in office_id_order_list:
                conn.execute("UPDATE office_locations SET sort_order = ? WHERE id = ?", (order, oid))
            conn.commit()
        return True
    except Exception:
        return False


def auto_reorder_users():
    """自动按姓名拼音序重排用户sort_order"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT id FROM users ORDER BY name, id").fetchall()
            for i, (uid,) in enumerate(users, 1):
                conn.execute("UPDATE users SET sort_order = ? WHERE id = ?", (i, uid))
            conn.commit()
        return True
    except Exception:
        return False


def auto_reorder_offices():
    """自动按名称重排办公地点sort_order"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            offices = conn.execute("SELECT id FROM office_locations WHERE is_active=1 ORDER BY name, id").fetchall()
            for i, (oid,) in enumerate(offices, 1):
                conn.execute("UPDATE office_locations SET sort_order = ? WHERE id = ?", (i, oid))
            conn.commit()
        return True
    except Exception:
        return False


# ==================== UI 辅助函数 ====================

def metric_card(label, value, col):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)


def status_badge(status):
    color_map = {
        '正常': 'status-normal', '迟到': 'status-late', '早退': 'status-early',
        '迟到早退': 'status-late-early', '待审批': 'status-pending',
        '已批准': 'status-approved', '已拒绝': 'status-rejected'
    }
    css_class = color_map.get(status, '')
    return f'<span class="status-badge {css_class}">{status}</span>'


def get_late_status_from_final(final_status):
    return '迟到' if final_status in ['迟到', '迟到早退'] else '正常'


def get_early_status_from_final(final_status):
    return '早退' if final_status in ['早退', '迟到早退'] else '正常'


def method_label_cn(method):
    return {'manual': '手动打卡', 'face': '人脸识别', 'gps': 'GPS 定位',
            'qr': '扫码打卡'}.get(method or 'manual', method or '手动打卡')


# ==================== 打卡方式组件 ====================

def render_gps_checkin(user, today_str, now_time_str, record, checkin_type='in'):
    st.markdown("#### 📍 GPS定位打卡")
    st.info("点击下方按钮获取您的位置，系统将自动验证是否在公司/允许区域内。")

    gps_html = """
    <div id="gps-container" style="padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">
        <button onclick="getLocation()" 
            style="background:#0D6EFD;color:white;border:none;border-radius:8px;padding:10px 20px;
                   font-size:14px;cursor:pointer;width:100%;margin-bottom:12px;">
            📍 获取当前位置
        </button>
        <div id="gps-result" style="font-size:13px;color:#374151;"></div>
        <input type="hidden" id="lat-input" value="">
        <input type="hidden" id="lng-input" value="">
    </div>
    <script>
    function getLocation() {
        var btn = event.target;
        btn.textContent = '⏳ 定位中...';
        btn.disabled = true;
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    var lat = pos.coords.latitude.toFixed(6);
                    var lng = pos.coords.longitude.toFixed(6);
                    var acc = Math.round(pos.coords.accuracy);
                    document.getElementById('lat-input').value = lat;
                    document.getElementById('lng-input').value = lng;
                    document.getElementById('gps-result').innerHTML = 
                        '<div style="color:#065f46;background:#d1fae5;padding:8px;border-radius:6px;">' +
                        '✅ 定位成功！<br>纬度: ' + lat + '<br>经度: ' + lng + 
                        '<br>精度: ±' + acc + '米</div>' +
                        '<div style="margin-top:8px;font-size:12px;color:#6B7280;">请复制坐标填入下方输入框完成打卡</div>';
                    btn.textContent = '✅ 定位完成';
                },
                function(err) {
                    var msgs = {1:'已拒绝位置权限，请在浏览器设置中允许', 
                                2:'无法获取位置信息', 3:'获取位置超时，请重试'};
                    document.getElementById('gps-result').innerHTML = 
                        '<div style="color:#991b1b;background:#fee2e2;padding:8px;border-radius:6px;">' +
                        '❌ ' + (msgs[err.code] || err.message) + '</div>';
                    btn.textContent = '📍 重新获取位置';
                    btn.disabled = false;
                },
                {enableHighAccuracy: true, timeout: 15000, maximumAge: 0}
            );
        } else {
            document.getElementById('gps-result').innerHTML = 
                '<div style="color:#991b1b;background:#fee2e2;padding:8px;border-radius:6px;">' +
                '❌ 您的浏览器不支持GPS定位</div>';
            btn.textContent = '📍 获取当前位置';
        }
    }
    </script>
    """
    st.components.v1.html(gps_html, height=200)

    st.markdown("**获取到位置后，请在下方输入坐标：**")
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("纬度 (Latitude)", value=0.0, format="%.6f", key=f"gps_lat_{checkin_type}")
    with col2:
        lng_input = st.number_input("经度 (Longitude)", value=0.0, format="%.6f", key=f"gps_lng_{checkin_type}")

    offices = get_office_locations()
    if offices.empty:
        st.warning("⚠️ 管理员尚未配置办公地点，GPS打卡将记录坐标但不做范围限制")
        allow_any_location = True
    else:
        st.markdown("**已配置办公地点：**")
        for _, loc in offices.iterrows():
            st.markdown(f"- {loc['name']} (范围: {loc['radius_meters']}米)")
        allow_any_location = False

    btn_label = "📍 GPS 上班打卡" if checkin_type == 'in' else "📍 GPS 下班打卡"
    if st.button(btn_label, key=f"gps_btn_{checkin_type}"):
        if lat_input == 0.0 and lng_input == 0.0:
            st.error("请先获取并填入您的位置坐标")
            return
    
        location_name = None
        if not allow_any_location:
            location_name, distance = check_location_in_office(lat_input, lng_input)
            if location_name is None:
                _, min_dist = check_location_in_office(lat_input, lng_input)
                st.error(f"❌ 您不在公司范围内（距最近地点约 {min_dist:.0f} 米）")
                return
            st.success(f"✅ 已验证位置：{location_name}（距离 {distance:.0f} 米）")
        else:
            location_name = f"GPS({lat_input:.4f},{lng_input:.4f})"
    
        if checkin_type == 'in':
            success, msg = clock_in(user['id'], today_str, now_time_str,
                                    method='gps', latitude=lat_input, longitude=lng_input,
                                    location_name=location_name)
        else:
            success, msg = clock_out(user['id'], today_str, now_time_str,
                                     method='gps', latitude=lat_input, longitude=lng_input)
        if success:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ {msg}")


def render_face_checkin(user, today_str, now_time_str, record, checkin_type='in'):
    st.markdown("#### 👤 人脸识别打卡")
    
    has_face = has_face_registered(user['id'])
    if not has_face:
        st.warning("⚠️ 您尚未注册人脸，请先在「个人中心」完成人脸注册")
        if st.button("前往注册人脸", key="goto_face_reg"):
            st.session_state.goto_face_register = True
            st.rerun()
        return
    
    # 获取用户已注册的人脸特征向量
    saved_encoding = get_user_face_encoding(user['id'])
    if not saved_encoding:
        st.error("❌ 未找到您的人脸特征数据，请重新注册")
        return
    
    st.markdown("请使用摄像头拍摄照片进行人脸识别")
    
    # 使用 Streamlit 的原生摄像头
    if 'face_verified' not in st.session_state:
        st.session_state.face_verified = False
    if 'face_similarity' not in st.session_state:
        st.session_state.face_similarity = 0.0
    
    # 摄像头输入
    img_file_buffer = st.camera_input("📸 拍摄照片进行人脸识别")
    
    if img_file_buffer is not None:
        with st.spinner(' 正在识别人脸，请稍候...'):
            # 读取图像
            image = Image.open(img_file_buffer)
            
            # 提取当前人脸特征
            current_encoding = extract_face_encoding_from_image(image)
            
            if current_encoding is None:
                st.error("❌ 未检测到人脸，请确保：\n- 光线充足\n- 正对摄像头\n- 面部无遮挡")
                return
            
            # 使用已注册的编码进行比对
            is_match, similarity = verify_face_match(saved_encoding, image, tolerance=0.6)
            
            if is_match:
                st.success(f"✅ 人脸识别成功！相似度：{similarity:.2%}")
                st.session_state.face_verified = True
                st.session_state.face_similarity = similarity
            else:
                st.error(f"❌ 人脸识别失败！相似度：{similarity:.2%}（需要≥60%）")
                st.info("💡 请确保：\n- 与注册时是同一人\n- 光线条件良好\n- 拍摄角度正确")
                st.session_state.face_verified = False
    
    # 打卡确认
    col1, col2 = st.columns(2)
    with col1:
        face_confirmed = st.checkbox("✅ 已验证成功（识别成功后勾选）",
                                     key=f"face_confirm_{checkin_type}")
    with col2:
        btn_label = "👤 确认上班打卡" if checkin_type == 'in' else "👤 确认下班打卡"
        if st.button(btn_label, key=f"face_btn_{checkin_type}", 
                     disabled=not (face_confirmed and st.session_state.face_verified)):
            if st.session_state.face_verified:
                if checkin_type == 'in':
                    success, msg = clock_in(user['id'], today_str, now_time_str,
                                            method='face', face_verified=1, 
                                            face_score=st.session_state.face_similarity)
                else:
                    success, msg = clock_out(user['id'], today_str, now_time_str, 
                                             method='face',
                                             face_score=st.session_state.face_similarity)
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state.face_verified = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("请先进行人脸识别验证")


def render_qr_checkin(user, today_str, now_time_str, record, checkin_type='in'):
    st.markdown("#### 📱 扫码打卡")
    st.info("管理员生成二维码后，员工用手机扫码完成打卡；或员工自行生成令牌，在另一台设备扫码验证。")

    tab_scan, tab_generate = st.tabs(["扫码打卡（输入令牌）", "生成个人令牌"])

    with tab_generate:
        st.markdown("生成您的打卡令牌（60秒有效），让管理员或同事用扫码设备扫描：")
        if st.button("🔄 生成打卡令牌", key=f"gen_qr_{checkin_type}", use_container_width=True):
            token, ts = generate_qr_token(user['id'], checkin_type)
            st.session_state[f'qr_token_{checkin_type}'] = token
            st.session_state[f'qr_ts_{checkin_type}'] = ts
            st.rerun()

        if st.session_state.get(f'qr_token_{checkin_type}'):
            token = st.session_state[f'qr_token_{checkin_type}']
            ts = st.session_state.get(f'qr_ts_{checkin_type}', 0)
            elapsed = int(time_module.time()) - ts
            remaining = 60 - elapsed
            if remaining > 0:
                st.success(f"令牌有效期剩余：**{remaining}秒**")
                st.code(token, language=None)
                st.markdown(generate_qr_image_html(token), unsafe_allow_html=True)
            else:
                st.error("令牌已过期，请重新生成")
                del st.session_state[f'qr_token_{checkin_type}']

    with tab_scan:
        st.markdown("请输入管理员生成的打卡令牌：")
        input_token = st.text_input("打卡令牌", placeholder="粘贴令牌字符串", key=f"qr_input_{checkin_type}")
        btn_label = "✅ 验证并上班打卡" if checkin_type == 'in' else "✅ 验证并下班打卡"
        if st.button(btn_label, key=f"qr_verify_{checkin_type}"):
            if not input_token.strip():
                st.error("请输入令牌")
            else:
                token_user_id, token_type, err = verify_qr_token(input_token.strip())
                if err:
                    st.error(f"❌ {err}")
                elif token_user_id != user['id']:
                    st.error("❌ 令牌不属于当前登录用户")
                elif token_type != checkin_type:
                    st.error(f"❌ 令牌类型不匹配（应为{'上班' if checkin_type == 'in' else '下班'}打卡令牌）")
                else:
                    if checkin_type == 'in':
                        success, msg = clock_in(user['id'], today_str, now_time_str, method='qr')
                    else:
                        success, msg = clock_out(user['id'], today_str, now_time_str, method='qr')
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")




def render_checkin_panel(user, today_str, now_time_str, record, checkin_type='in'):
    """统一打卡面板 - 按钮优化为方块两行文字"""
    title = "⏰ 上班打卡" if checkin_type == 'in' else "🌙 下班打卡"
    rule_time = "09:00" if checkin_type == 'in' else "18:00"

    st.markdown(f"""
    <div style="padding:16px;border-radius:10px;
        background:{'#e3f2fd' if checkin_type == 'in' else '#f3e5f5'};
        border:1px solid {'#90caf9' if checkin_type == 'in' else '#ce93d8'};
        margin-bottom:12px;">
        <h4 style="margin:0 0 4px 0;">{title}</h4>
        <p style="margin:0;font-size:14px;">规定时间: {rule_time}</p>
    </div>
    """, unsafe_allow_html=True)

    if checkin_type == 'in' and record:
        st.markdown(f"✅ 已打卡: **{record['check_in']}** （{method_label_cn(record.get('checkin_method', 'manual'))}）")
        late_status = get_late_status_from_final(record['status'])
        st.markdown(f"状态: {status_badge(late_status)}", unsafe_allow_html=True)
        return

    if checkin_type == 'out':
        if not record:
            st.markdown("🚫 请先完成上班打卡")
            return
        if record.get('check_out'):
            st.markdown(f"✅ 已打卡：**{record['check_out']}** （{method_label_cn(record.get('checkout_method', 'manual'))}）")
            early_status = get_early_status_from_final(record['status'])
            st.markdown(f"状态：{status_badge(early_status)}", unsafe_allow_html=True)
            return

    # 显示打卡方式选择按钮
    method_key = f"checkin_method_{checkin_type}"
    if method_key not in st.session_state:
        st.session_state[method_key] = 'manual'

    method_options = [
        ('manual', '手动打卡'),
        ('face',   '人脸识别'),
        ('gps',    'GPS 定位'),
        ('qr',     '扫码打卡'),
    ]

    st.markdown("**选择打卡方式：**")
    cols = st.columns(4)
    for i, (mkey, label) in enumerate(method_options):
        is_active = st.session_state[method_key] == mkey
        with cols[i]:
            if st.button(label, key=f"method_{mkey}_{checkin_type}", use_container_width=True):
                st.session_state[method_key] = mkey
                st.rerun()

    selected_method = st.session_state[method_key]
    st.markdown("---")

    # 根据选择显示对应的打卡界面
    if selected_method == 'manual':
        # 手动打卡直接显示简单按钮
        btn_label = "🖊️ 上班打卡" if checkin_type == 'in' else "🖊️ 下班打卡"
        if st.button(btn_label, key=f"manual_btn_{checkin_type}"):
            if checkin_type == 'in':
                success, msg = clock_in(user['id'], today_str, now_time_str, method='manual')
            else:
                success, msg = clock_out(user['id'], today_str, now_time_str, method='manual')
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")
    elif selected_method == 'face':
        render_face_checkin(user, today_str, now_time_str, record, checkin_type)
    elif selected_method == 'gps':
        render_gps_checkin(user, today_str, now_time_str, record, checkin_type)
    elif selected_method == 'qr':
        render_qr_checkin(user, today_str, now_time_str, record, checkin_type)


# ==================== 人脸注册组件 ====================

def render_face_registration(user):
    st.markdown("### 👤 人脸识别注册")

    has_face = has_face_registered(user['id'])
    if has_face:
        st.success("✅ 您已完成人脸注册，可使用人脸识别打卡")
        if st.button("🔄 重新注册人脸", key="re_register_face"):
            st.session_state.show_face_reg = True
        if not st.session_state.get('show_face_reg', False):
            return
    else:
        st.info("请注册您的人脸信息，注册后即可使用人脸识别打卡。")
        st.session_state.show_face_reg = True

    if st.session_state.get('show_face_reg', False):
        st.markdown("### 👤 人脸注册 - 请拍摄/上传 3 张照片")
        st.info("💡 您可以选择以下任一方式：上传已有照片，或使用摄像头拍摄")
        
        uploaded_files = []
        
        # 方式 1：使用摄像头拍摄（支持连续拍摄 3 张）
        st.markdown("#### 📸 方式 1：使用摄像头拍摄（建议 3 张）")
        
        # 初始化 session_state 用于存储拍摄的照片和最后一次拍摄时间
        if 'captured_photos' not in st.session_state:
            st.session_state.captured_photos = []
        if 'last_photo_time' not in st.session_state:
            st.session_state.last_photo_time = 0
        
        # 摄像头控制区域
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            # 摄像头组件 - 使用较小的尺寸
            img_file_buffer = st.camera_input(
                "📷 启动摄像头",
                help="请调整摄像头角度，确保脸部完整出现在画面中。每次点击都会拍摄一张新照片！"
            )
        
        with col2:
            if st.button("🗑️ 清空已拍", key="clear_photos", help="清空已拍摄的照片，重新开始"):
                st.session_state.captured_photos = []
                st.session_state.last_photo_time = 0
                st.rerun()
        
        with col3:
            photo_count = len(st.session_state.captured_photos)
            st.metric("目标", f"{min(photo_count, 3)}/3")
        
        # 处理拍摄的照片 - 使用时间戳防止重复添加
        if img_file_buffer is not None:
            current_time = time_module.time()
            # 只有距离上次拍摄超过 0.5 秒才添加，防止重复
            if current_time - st.session_state.last_photo_time > 0.5:
                # 保存拍摄的照片
                st.session_state.captured_photos.append(img_file_buffer)
                st.session_state.last_photo_time = current_time
                st.success(f"✅ 已拍摄第 {len(st.session_state.captured_photos)} 张")
                
                # 强制刷新页面以更新计数器
                if len(st.session_state.captured_photos) < 3:
                    time_module.sleep(0.3)
                    st.rerun()
        
        # 显示已拍摄的所有照片（统一在这里显示）
        if st.session_state.captured_photos:
            st.success(f"✅ 已拍摄 {len(st.session_state.captured_photos)} 张照片")
            st.markdown("**已拍摄的照片：**")
            cols = st.columns(min(3, len(st.session_state.captured_photos)))
            for i, photo in enumerate(st.session_state.captured_photos[:3]):
                with cols[i]:
                    image = Image.open(photo)
                    st.image(image, caption=f"照片 {i+1}", use_container_width=True)
            
            if len(st.session_state.captured_photos) < 3:
                st.info(f"💡 建议拍摄 3 张不同角度的照片：正面、左侧、右侧（已拍摄 {len(st.session_state.captured_photos)} 张）")
            else:
                st.success("✅ 已拍摄 3 张照片，请点击下方按钮保存")
        
        # 方式 2：上传已有照片（如果不想用摄像头）
        st.markdown("---")
        st.markdown("#### 📁 方式 2：上传已有照片（如果摄像头不方便）")
        uploaded_files_from_upload = st.file_uploader(
            "点击这里选择 3 张照片",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key="face_upload",
            help="选择 3 张清晰的人脸照片"
        )
        
        # 优先使用拍摄的照片，如果没有拍摄则使用上传的照片
        if st.session_state.captured_photos:
            uploaded_files = st.session_state.captured_photos[:3]
        elif uploaded_files_from_upload:
            uploaded_files = uploaded_files_from_upload
            # 只显示上传的照片预览（拍摄的照片已经在上面显示过了）
            if uploaded_files and not st.session_state.captured_photos:
                st.markdown("**已上传的照片：**")
                cols = st.columns(min(3, len(uploaded_files)))
                for i, uploaded_file in enumerate(uploaded_files[:3]):
                    with cols[i]:
                        image = Image.open(uploaded_file)
                        st.image(image, caption=f"照片 {i+1}", use_container_width=True)
        
        # 处理按钮
        if uploaded_files and len(uploaded_files) >= 1:
            if len(uploaded_files) >= 3:
                st.success(f"✅ 已准备 {len(uploaded_files)} 张照片")
            else:
                st.info(f"ℹ️ 已准备 {len(uploaded_files)} 张照片（建议 3 张，最少 1 张）")
            
            # 提取特征并保存
            if st.button("💾 提取特征并保存", key="save_face",
                        use_container_width=True, type="primary"):
                with st.spinner('正在处理人脸特征，请稍候...'):
                    encodings = []
                    for idx, uploaded_file in enumerate(uploaded_files[:3]):
                        # 关键修复：每次都重新打开照片，避免被 st.image() 影响
                        # 先不显示照片，先提取特征
                        try:
                            # 重置文件指针并读取
                            uploaded_file.seek(0)
                            image_bytes = uploaded_file.read()
                            
                            # 使用 PIL 打开
                            image = Image.open(io.BytesIO(image_bytes))
                            
                            # 转换为 RGB
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            
                            # 转换为 numpy 数组
                            image_array = np.array(image)
                            
                            # 调试信息
                            st.write(f"\n**处理照片 {idx+1}:**")
                            st.write(f"- 文件名：{uploaded_file.name}")
                            st.write(f"- 字节数：{len(image_bytes)}")
                            st.write(f"- 图像尺寸：{image.size}")
                            st.write(f"- 图像模式：{image.mode}")
                            st.write(f"- Numpy 形状：{image_array.shape}")
                            st.write(f"- 像素范围：{image_array.min()}-{image_array.max()}")
                            
                            # 直接在这里进行人脸检测
                            st.write(f"\n🔍 开始人脸检测...")
                            face_locations = face_recognition.face_locations(image_array, model='hog')
                            
                            if not face_locations:
                                st.write(f"⚠️ HOG 未检测到，尝试 CNN...")
                                face_locations = face_recognition.face_locations(image_array, model='cnn')
                            
                            if face_locations:
                                st.write(f"✅ 检测到 {len(face_locations)} 张人脸")
                                face_encodings = face_recognition.face_encodings(image_array, face_locations)
                                if face_encodings:
                                    encodings.append(face_encodings[0].tolist())
                                    st.write(f"✅ 照片{idx+1} 特征提取成功")
                                else:
                                    st.write(f"❌ 无法提取特征")
                            else:
                                st.write(f"❌ 未检测到人脸")
                            
                            # 最后再显示照片
                            st.image(image, caption=f"照片 {idx+1}", width=300)
                            
                        except Exception as e:
                            st.error(f"❌ 处理照片 {idx+1} 失败：{e}")
                            import traceback
                            traceback.print_exc()
                    
                    if len(encodings) >= 1:
                        # 计算平均特征向量
                        if len(encodings) > 1:
                            avg_encoding = np.mean(encodings, axis=0).tolist()
                            st.info(f"📊 使用 {len(encodings)} 张照片的平均特征")
                        else:
                            avg_encoding = encodings[0]
                            st.warning("⚠️ 只有 1 张照片检测到人脸，建议再拍摄 2 张")
                        
                        # 保存特征向量和元数据
                        face_data = {
                            "user_id": user['id'],
                            "registered_at": datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'),
                            "method": "camera_or_upload",
                            "status": "registered",
                            "face_encoding": avg_encoding,
                            "encoding_dimension": 128,
                            "photos_count": len(encodings)
                        }
                        
                        if save_face_data(user['id'], json.dumps(face_data)):
                            st.success("✅ 人脸注册成功！下次可使用人脸识别打卡。")
                            log_action(user['id'], '人脸注册', '完成人脸信息采集')
                            
                            # 显示成功信息，不自动刷新
                            st.balloons()
                            st.info("💡 您可以继续拍摄其他照片，或者切换到其他菜单")
                            
                            # 清空已拍摄的照片
                            st.session_state.captured_photos = []
                            # 不再自动刷新
                        else:
                            st.error("❌ 保存失败，请重试")
                    else:
                        st.error("❌ 无法从照片中提取人脸特征，请确保：\n\n"
                                "**拍摄技巧：**\n"
                                "- 📷 **调整摄像头角度**：摄像头应该正对脸部，不要从上往下拍\n"
                                "- 💡 **光线充足**：面向窗户或灯光，确保脸部明亮\n"
                                "- 😊 **面部完整**：确保整张脸都在画面中，不要只拍到局部\n"
                                "- 👓 **摘掉遮挡物**：摘掉口罩、墨镜、帽子\n"
                                "- 📏 **距离适中**：不要离摄像头太近或太远（建议 30-50cm）\n\n"
                                "**建议：** 使用前置摄像头或手机拍摄，效果更好！\n\n"
                                "🔧 **诊断工具：** 如果多次尝试仍失败，可以运行 `test_face_detection_debug.py` 脚本进行详细诊断")
        elif uploaded_files:
            st.warning(f"⚠️ 请至少上传/拍摄 1 张照片")
        else:
            st.info("👆 请使用摄像头拍摄或点击上方按钮选择照片")


# ==================== 主程序逻辑 ====================

if 'user' not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="login-bg"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-container">
            <div class="login-title">企业考勤管理系统</div>
        </div>
        """, unsafe_allow_html=True)

        departments = get_departments()
        dept_options = departments['name'].tolist() if not departments.empty else []
        dept_map = {row['name']: row['id'] for _, row in departments.iterrows()} if not departments.empty else {}

        action = st.query_params.get("action", "login")
        show_register = action == "register"

        if not show_register:
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登 录", use_container_width=True)
                if submitted:
                    user = verify_login(username, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"欢迎回来, {user['name']}")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
            st.markdown("<div class='register-inline'>还没有账号？<a href='?action=register'>点击注册</a></div>",
                        unsafe_allow_html=True)
        else:
            with st.form("register_form"):
                reg_username = st.text_input("用户名", placeholder="请输入用户名", key="reg_username")
                reg_name = st.text_input("姓名", placeholder="请输入姓名", key="reg_name")
                reg_password = st.text_input("密码", type="password", placeholder="请输入密码", key="reg_password")
                reg_password2 = st.text_input("确认密码", type="password", placeholder="请再次输入密码", key="reg_password2")
                reg_dept = st.selectbox("部门", dept_options, index=0) if dept_options else None
                reg_email = st.text_input("邮箱", placeholder="选填", key="reg_email")
                reg_phone = st.text_input("手机号", placeholder="选填", key="reg_phone")
                reg_submit = st.form_submit_button("注 册", use_container_width=True)
                if reg_submit:
                    if not reg_username or not reg_name or not reg_password or not reg_password2:
                        st.error("请填写完整")
                    elif reg_password != reg_password2:
                        st.error("两次输入的密码不一致")
                    else:
                        dept_id = dept_map.get(reg_dept) if reg_dept else None
                        ok, msg = register_user(reg_username, reg_password, reg_name, dept_id, reg_email, reg_phone)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
            st.markdown("<div class='register-inline'><a href='?action=login'>返回登录</a></div>",
                        unsafe_allow_html=True)

else:
    user = st.session_state.user

    employee_options = ["工作台", "我的考勤", "请假申请", "加班申请", "个人中心"]
    employee_icons = ["briefcase", "calendar-check", "calendar-plus", "clock", "person"]
    admin_options = ["控制台", "考勤报表", "员工管理", "请假审批", "加班审批", "统计报表", "系统设置"]
    admin_icons = ["speedometer2", "table", "people", "calendar-check", "clock-history", "bar-chart", "gear"]

    if user['role'] == 'admin':
        options = employee_options[:2] + admin_options + [employee_options[-1]]
        icons = employee_icons[:2] + admin_icons + [employee_icons[-1]]
    else:
        options = employee_options
        icons = employee_icons

    now_beijing = datetime.now(BEIJING_TZ)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    chinese_weekday = weekdays[now_beijing.weekday()]

    st.markdown(f"""
    <div class="app-header">
        <div class="title">{COMPANY_NAME}</div>
        <div class="sub">{now_beijing.strftime("%Y年%m月%d日")} {chinese_weekday} {now_beijing.strftime("%H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

    selected_top = option_menu(
        menu_title=None,
        options=options,
        icons=icons,
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {"padding": "6px", "background-color": "transparent"},
            "icon": {"color": "#079AF5", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "padding": "8px 16px", "border-radius": "8px", "color": "#111827"},
            "nav-link-selected": {"background-color": "#0884F8", "color": "white"},
        },
        key="top_menu"
    )
    selected = selected_top

    # ========== 工作台 ==========
    if selected == "工作台":
        now_beijing = datetime.now(BEIJING_TZ)
        current_hour = now_beijing.hour
        current_time_str = now_beijing.strftime("%H:%M:%S")

        if 5 <= current_hour < 12:
            greeting = "早安"
        elif 12 <= current_hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"

        st.title(f"👋 {greeting}, {user['name']}")
        st.markdown("✨ 新的一天，继续加油！")

        today_str = now_beijing.strftime("%Y-%m-%d")
        now_time_str = now_beijing.strftime("%H:%M:%S")
        record = get_attendance_status(user['id'], today_str)

        if record:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("上班时间", record.get('check_in', '--'))
            with col_s2:
                st.metric("下班时间", record.get('check_out', '--') or '--')
            with col_s3:
                st.metric("打卡状态", record.get('status', '--'))

        st.markdown("### 🕒 打卡签到")
        col1, col2 = st.columns(2)
        with col1:
            render_checkin_panel(user, today_str, now_time_str, record, checkin_type='in')
        with col2:
            render_checkin_panel(user, today_str, now_time_str, record, checkin_type='out')

        with st.expander("ℹ️ 打卡方式说明"):
            st.markdown("""
            | 方式 | 说明 | 适用场景 |
            |------|------|---------|
            | 🖊️ 手动打卡 | 一键打卡，无需验证 | 默认方式 |
            | 👤 人脸识别 | 摄像头拍照验证身份 | 办公室，防代打 |
            | 📍 GPS 定位 | 验证是否在公司范围内 | 出差/外勤员工 |
            | 📱 扫码打卡 | 动态令牌，60 秒有效 | 防截图代打 |
                        
            > 首次使用人脸识别，请先在「个人中心」完成人脸注册。
            """)

    # ========== 我的考勤 ==========
    elif selected == "我的考勤":
        st.title("📊 我的考勤记录")

        with st.expander("📅 考勤日历", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("年份",
                                    list(range(datetime.now(BEIJING_TZ).year - 1, datetime.now(BEIJING_TZ).year + 2)),
                                    index=1, key='cal_year')
            with col2:
                month = st.selectbox("月份", list(range(1, 13)), index=datetime.now(BEIJING_TZ).month - 1,
                                     key='cal_month')
            cal_data = get_month_calendar_data(user['id'], year, month)
            cal = calendar.monthcalendar(year, month)
            cal_df = pd.DataFrame(cal, columns=['周一', '周二', '周三', '周四', '周五', '周六', '周日'])
            for i, week in enumerate(cal):
                for j, day in enumerate(week):
                    if day != 0:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        status_row = cal_data[cal_data['date'] == date_str]
                        if not status_row.empty:
                            cal_df.iloc[i, j] = f"{day} ({status_row.iloc[0]['status']})"
                        else:
                            cal_df.iloc[i, j] = f"{day} (未打卡)"
            st.dataframe(cal_df, use_container_width=True, hide_index=True)

        try:
            with sqlite3.connect(DB_FILE) as conn:
                history = pd.read_sql_query(
                    """SELECT date, check_in, check_out, status, checkin_method, location_name, face_verified 
                       FROM attendance WHERE user_id = ? ORDER BY date DESC""",
                    conn, params=(user['id'],))
        except Exception:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    history = pd.read_sql_query(
                        "SELECT date, check_in, check_out, status FROM attendance WHERE user_id = ? ORDER BY date DESC",
                        conn, params=(user['id'],))
            except Exception:
                history = pd.DataFrame()

        total_days = len(history)
        normal_days = len(history[history['status'] == '正常']) if not history.empty else 0
        late_days = len(history[history['status'].isin(['迟到', '迟到早退'])]) if not history.empty else 0
        early_days = len(history[history['status'].isin(['早退', '迟到早退'])]) if not history.empty else 0

        col1, col2 = st.columns(2)
        metric_card("总出勤天数", total_days, col1)
        metric_card("正常出勤", normal_days, col2)
        col3, col4 = st.columns(2)
        metric_card("迟到次数", late_days, col3)
        metric_card("早退次数", early_days, col4)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("⏰ 上班打卡记录")
            if not history.empty:
                in_df = history.copy()
                in_df['迟到状态'] = in_df['status'].apply(get_late_status_from_final)
                if 'checkin_method' in in_df.columns:
                    in_df['打卡方式'] = in_df['checkin_method'].apply(method_label_cn)
                else:
                    in_df['打卡方式'] = '手动打卡'
                if 'face_verified' in in_df.columns:
                    in_df['人脸验证'] = in_df['face_verified'].apply(lambda x: '✅' if x == 1 else '—')
                else:
                    in_df['人脸验证'] = '—'
                in_display = in_df[['date', 'check_in', '迟到状态', '打卡方式', '人脸验证']].copy()
                in_display.columns = ['日期', '上班时间', '状态', '方式', '人脸']
                in_display['状态'] = in_display['状态'].apply(lambda x: status_badge(x))
                st.write(in_display.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("暂无上班打卡记录")

        with col_right:
            st.subheader("🌙 下班打卡记录")
            if not history.empty:
                out_df = history[history['check_out'].notna()][['date', 'check_out', 'status']].copy()
                if not out_df.empty:
                    out_df['早退状态'] = out_df['status'].apply(get_early_status_from_final)
                    out_display = out_df[['date', 'check_out', '早退状态']].copy()
                    out_display.columns = ['日期', '下班时间', '状态']
                    out_display['状态'] = out_display['状态'].apply(lambda x: status_badge(x))
                    st.write(out_display.to_html(escape=False, index=False), unsafe_allow_html=True)
                else:
                    st.info("暂无下班打卡记录")
            else:
                st.info("暂无下班打卡记录")

    # ========== 请假申请 ==========
    elif selected == "请假申请":
        st.title("📝 请假申请")
        with st.form("leave_application_form"):
            col1, col2 = st.columns(2)
            with col1:
                leave_type = st.selectbox("请假类型", ["事假", "病假", "年假", "调休", "婚假", "产假", "丧假", "其他"])
            with col2:
                pass
            reason = st.text_area("请假事由", placeholder="请详细说明请假原因...", height=80)
            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("开始日期", min_value=datetime.now(BEIJING_TZ).date())
            with col4:
                end_date = st.date_input("结束日期", min_value=datetime.now(BEIJING_TZ).date())
            submitted = st.form_submit_button("提交申请", type="primary", use_container_width=True)
            if submitted:
                if end_date < start_date:
                    st.error("结束日期不能早于开始日期")
                else:
                    success, msg = apply_leave(user['id'], leave_type,
                                               start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), reason)
                    if success:
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("我的请假记录")
        my_leaves = get_leave_applications(user_id=user['id'])
        if not my_leaves.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            my_leaves = my_leaves.copy()
            my_leaves["status"] = my_leaves["status"].map(status_map).fillna(my_leaves["status"])
            display_df = my_leaves[['leave_type', 'start_date', 'end_date', 'days', 'reason', 'status']].rename(columns={
                'leave_type': '请假类型', 'start_date': '开始日期', 'end_date': '结束日期',
                'days': '天数', 'reason': '事由', 'status': '状态'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无请假记录")

    # ========== 加班申请 ==========
    elif selected == "加班申请":
        st.title("⏰ 加班申请")
        with st.form("overtime_application_form"):
            col1, col2 = st.columns(2)
            with col1:
                overtime_date = st.date_input("加班日期", min_value=datetime.now(BEIJING_TZ).date())
            with col2:
                hours = st.number_input("加班时长(小时)", min_value=0.5, max_value=24.0, value=1.0, step=0.5)
            reason = st.text_area("加班事由", placeholder="请说明加班原因...", height=80)
            submitted = st.form_submit_button("提交申请", type="primary", use_container_width=True)
            if submitted:
                if hours <= 0:
                    st.error("加班时长必须大于0")
                else:
                    success, msg = apply_overtime(user['id'], overtime_date.strftime("%Y-%m-%d"), hours, reason)
                    if success:
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("我的加班记录")
        my_overtime = get_overtime_applications(user_id=user['id'])
        if not my_overtime.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            my_overtime = my_overtime.copy()
            my_overtime["status"] = my_overtime["status"].map(status_map).fillna(my_overtime["status"])
            display_df = my_overtime[['date', 'hours', 'reason', 'status']].rename(columns={
                'date': '加班日期', 'hours': '时长(小时)', 'reason': '事由', 'status': '状态'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无加班记录")

    # ========== 管理员控制台 ==========
    elif selected == "控制台" and user['role'] == 'admin':
        try:
            st.title("🖥️ 管理员控制台")
            all_data = get_all_attendance()
            today_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
            today_data = all_data[all_data['date'] == today_str] if not all_data.empty else pd.DataFrame()

            with sqlite3.connect(DB_FILE) as conn:
                total_employees = conn.execute("SELECT COUNT(*) FROM users WHERE role='employee'").fetchone()[0]

            checked_in = len(today_data)
            late_count = len(today_data[today_data['status'].isin(['迟到', '迟到早退'])]) if not today_data.empty else 0
            early_count = len(today_data[today_data['status'].isin(['早退', '迟到早退'])]) if not today_data.empty else 0

            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            metric_card("总员工数", total_employees, col1)
            metric_card("今日实到", checked_in, col2)
            metric_card("今日迟到", late_count, col3)
            metric_card("今日早退", early_count, col4)

            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("今日考勤状态分布")
                if not today_data.empty:
                    status_counts = today_data['status'].value_counts().reset_index()
                    status_counts.columns = ['status', 'count']
                    base = alt.Chart(status_counts).encode(theta=alt.Theta("count", stack=True))
                    pie = base.mark_arc(outerRadius=120).encode(
                        color=alt.Color("status"),
                        order=alt.Order("status", sort="descending"),
                        tooltip=["status", "count"]
                    )
                    text = base.mark_text(radius=140).encode(
                        text="count",
                        order=alt.Order("status", sort="descending"),
                        color=alt.value("black")
                    )
                    st.altair_chart(pie + text, use_container_width=True)
                else:
                    st.info("今日暂无数据")

            with col_chart2:
                st.subheader("打卡方式分布")
                if not today_data.empty and 'checkin_method' in today_data.columns:
                    method_counts = today_data['checkin_method'].fillna('manual').value_counts().reset_index()
                    method_counts.columns = ['method', 'count']
                    method_counts['method_cn'] = method_counts['method'].apply(method_label_cn)
                    bar = alt.Chart(method_counts).mark_bar().encode(
                        x=alt.X('method_cn:N', title='打卡方式'),
                        y=alt.Y('count:Q', title='人数'),
                        color=alt.Color('method_cn:N'),
                        tooltip=['method_cn', 'count']
                    ).properties(height=280)
                    st.altair_chart(bar, use_container_width=True)
                else:
                    st.info("今日暂无打卡数据")
        except Exception as e:
            st.error(f"控制台发生错误: {e}")

    # ========== 考勤报表 ==========
    elif selected == "考勤报表" and user['role'] == 'admin':
        try:
            st.title("📋 考勤数据报表")
            all_data = get_all_attendance()

            if all_data.empty:
                st.info("暂无考勤数据")
            else:
                with st.expander("🔍 数据筛选", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        dept_options_filter = all_data['department'].dropna().unique().tolist()
                        dept_filter = st.multiselect("筛选部门", options=dept_options_filter,
                                                     default=dept_options_filter)
                    with col2:
                        status_options_filter = all_data['status'].dropna().unique().tolist()
                        status_filter = st.multiselect("筛选状态", options=status_options_filter,
                                                       default=status_options_filter)

                filtered_data = all_data[
                    all_data['department'].isin(dept_filter) & all_data['status'].isin(status_filter)]

                display_df = filtered_data.copy()
                if 'checkin_method' in display_df.columns:
                    display_df['checkin_method'] = display_df['checkin_method'].apply(method_label_cn)
                if 'face_verified' in display_df.columns:
                    display_df['face_verified'] = display_df['face_verified'].apply(lambda x: '✅' if x == 1 else '—')

                rename_map = {
                    "id": "ID", "name": "姓名", "department": "部门",
                    "date": "日期", "check_in": "上班时间", "check_out": "下班时间",
                    "status": "状态"
                }
                if 'checkin_method' in display_df.columns:
                    rename_map["checkin_method"] = "打卡方式"
                if 'location_name' in display_df.columns:
                    rename_map["location_name"] = "打卡地点"
                if 'face_verified' in display_df.columns:
                    rename_map["face_verified"] = "人脸验证"

                st.dataframe(display_df.rename(columns=rename_map), use_container_width=True, hide_index=True)

                st.download_button(
                    label="📥 导出 CSV",
                    data=filtered_data.to_csv(index=False).encode('utf-8'),
                    file_name=f'attendance_report_{datetime.now(BEIJING_TZ).strftime("%Y%m%d")}.csv',
                    mime='text/csv', type="primary", use_container_width=True
                )
        except Exception as e:
            st.error(f"报表发生错误: {e}")

    # ========== 员工管理（移除了排序控件和手动编号）==========
    elif selected == "员工管理" and user['role'] == 'admin':
        st.title("👥 员工管理")

        with st.expander("➕ 新增员工"):
            with st.form("add_employee_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_username = st.text_input("用户名", key="new_user_username")
                    new_name = st.text_input("姓名", key="new_user_name")
                    new_password = st.text_input("密码", type="password", key="new_user_pwd")
                with col2:
                    departments = get_departments()
                    dept_options = departments['name'].tolist() if not departments.empty else []
                    dept_map = {row['name']: row['id'] for _, row in departments.iterrows()} if not departments.empty else {}
                    new_dept = st.selectbox("部门", dept_options, key="new_user_dept")
                    new_role = st.selectbox("角色", ["employee", "admin"], key="new_user_role")
                submitted = st.form_submit_button("新增", use_container_width=True, type="primary")
                if submitted:
                    if not new_username or not new_name or not new_password:
                        st.error("请填写完整信息")
                    else:
                        dept_id = dept_map.get(new_dept)
                        ok, msg = register_user(new_username, new_password, new_name, dept_id)
                        if ok:
                            with sqlite3.connect(DB_FILE) as conn:
                                conn.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, new_username))
                                conn.commit()
                            st.success("员工添加成功")
                            log_action(user['id'], '新增员工', f'用户名 {new_username}')
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown("#### 📋 员工列表")

        try:
            with sqlite3.connect(DB_FILE) as conn:
                # 按角色（admin在前）和id升序排序
                users_df = pd.read_sql_query(
                    """SELECT u.id, u.username, u.name, u.role, u.department_id, d.name as department, 
                              u.email, u.phone,
                              (SELECT COUNT(*) FROM face_encodings fe WHERE fe.user_id = u.id) as has_face
                       FROM users u LEFT JOIN departments d ON u.department_id = d.id
                       ORDER BY u.role, u.id""", conn)
        except Exception as e:
            st.error(f"加载员工数据失败: {e}")
            users_df = pd.DataFrame()

        if not users_df.empty:
            # 添加连续序号（行号）
            users_df.insert(0, '序号', range(1, len(users_df) + 1))
            users_df['人脸注册'] = users_df['has_face'].apply(lambda x: '✅ 已注册' if x > 0 else '❌ 未注册')

            # 显示时只保留序号、用户名、姓名、部门、角色、邮箱、电话、人脸注册
            users_display = users_df[['序号', 'username', 'name', 'department', 'role', 'email', 'phone', '人脸注册']].rename(columns={
                "username": "用户名", "name": "姓名", "department": "部门",
                "role": "角色", "email": "邮箱", "phone": "电话"
            })
            st.dataframe(users_display, use_container_width=True, hide_index=True)

            st.subheader("🔧 管理操作")
            departments = get_departments()
            dept_options = departments['name'].tolist() if not departments.empty else []
            dept_map = {row['name']: row['id'] for _, row in departments.iterrows()} if not departments.empty else {}
            # 选项显示序号、姓名、用户名，但不显示数据库ID
            emp_options = {f"{row['序号']}. {row['name']} ({row['username']})": row['id'] for _, row in users_df.iterrows()}
            selected_emp_label = st.selectbox("选择员工进行编辑或删除", ["请选择..."] + list(emp_options.keys()))

            if selected_emp_label != "请选择...":
                emp_id = emp_options[selected_emp_label]
                emp_data = users_df[users_df['id'] == emp_id].iloc[0]

                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_username = st.text_input("用户名", value=emp_data['username'])
                        edit_name = st.text_input("姓名", value=emp_data['name'])
                        edit_role = st.selectbox("角色", ["employee", "admin"],
                                                 index=["employee", "admin"].index(emp_data['role']) if emp_data['role'] in ["employee", "admin"] else 0)
                    with col2:
                        dept_idx = 0
                        if emp_data['department'] in dept_options:
                            dept_idx = dept_options.index(emp_data['department'])
                        edit_dept = st.selectbox("部门", dept_options, index=dept_idx, key="edit_dept_select")
                        edit_email = st.text_input("邮箱", value=emp_data['email'] if pd.notna(emp_data['email']) and emp_data['email'] else "")
                        edit_phone = st.text_input("电话", value=emp_data['phone'] if pd.notna(emp_data['phone']) and emp_data['phone'] else "")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("保存修改", use_container_width=True, type="primary"):
                            dept_id = dept_map.get(edit_dept)
                            ok, msg = update_user(emp_id, edit_username, edit_name, dept_id, edit_role, edit_email, edit_phone)
                            if ok:
                                st.success(msg)
                                log_action(user['id'], '编辑员工', f'用户ID {emp_id}')
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_cancel:
                        if st.form_submit_button("取消", use_container_width=True):
                            pass

                if st.button("🗑️ 删除该员工（含人脸数据）", type="primary", use_container_width=True):
                    ok, msg = delete_user(emp_id)
                    if ok:
                        st.success(msg)
                        log_action(user['id'], '删除员工', f'用户ID {emp_id}')
                        st.rerun()
                    else:
                        st.error(msg)

    # ========== 请假审批 ==========
    elif selected == "请假审批" and user['role'] == 'admin':
        st.title("✅ 请假审批")
        pending_leaves = get_leave_applications(status='pending')
        if not pending_leaves.empty:
            st.subheader("待审批的请假申请")
            for idx, row in pending_leaves.iterrows():
                with st.expander(f"{row['applicant_name']} - {row['leave_type']} ({row['start_date']} 至 {row['end_date']})"):
                    st.markdown(f"""
                    **申请人**: {row['applicant_name']} ({row['department_name']})  
                    **请假类型**: {row['leave_type']}  
                    **时间**: {row['start_date']} 至 {row['end_date']} (共 {row['days']} 天)  
                    **事由**: {row['reason']}  
                    **申请时间**: {row['created_at']}
                    """)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ 批准", key=f"approve_leave_{row['id']}", use_container_width=True, type="primary"):
                            try:
                                with sqlite3.connect(DB_FILE) as conn:
                                    conn.execute("UPDATE leaves SET status='approved', approved_by=?, approved_at=? WHERE id=?",
                                                 (user['id'], datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"), row['id']))
                                    conn.commit()
                                log_action(user['id'], '审批请假', f'批准请假 {row["id"]}')
                                st.success(f"已批准 {row['applicant_name']} 的请假申请")
                                st.rerun()
                            except Exception as e:
                                st.error(f"操作失败: {e}")
                    with col2:
                        if st.button("❌ 拒绝", key=f"reject_leave_{row['id']}", use_container_width=True):
                            try:
                                with sqlite3.connect(DB_FILE) as conn:
                                    conn.execute("UPDATE leaves SET status='rejected', approved_by=?, approved_at=? WHERE id=?",
                                                 (user['id'], datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"), row['id']))
                                    conn.commit()
                                log_action(user['id'], '审批请假', f'拒绝请假 {row["id"]}')
                                st.warning(f"已拒绝 {row['applicant_name']} 的请假申请")
                                st.rerun()
                            except Exception as e:
                                st.error(f"操作失败: {e}")
        else:
            st.info("暂无待审批的请假申请")

        st.markdown("---")
        st.subheader("审批历史")
        all_leaves = get_leave_applications()
        if not all_leaves.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            all_leaves = all_leaves.copy()
            all_leaves["status"] = all_leaves["status"].map(status_map).fillna(all_leaves["status"])
            st.dataframe(all_leaves[['applicant_name', 'leave_type', 'start_date', 'end_date', 'status', 'approver_name']].rename(columns={
                "applicant_name": "申请人", "leave_type": "请假类型",
                "start_date": "开始日期", "end_date": "结束日期",
                "status": "状态", "approver_name": "审批人"
            }), use_container_width=True, hide_index=True)

    # ========== 加班审批 ==========
    elif selected == "加班审批" and user['role'] == 'admin':
        st.title("⏰ 加班审批")
        pending_overtime = get_overtime_applications(status='pending')
        if not pending_overtime.empty:
            st.subheader("待审批的加班申请")
            for idx, row in pending_overtime.iterrows():
                with st.expander(f"{row['applicant_name']} - {row['date']} 加班 {row['hours']}小时"):
                    st.markdown(f"""
                    **申请人**: {row['applicant_name']} ({row['department_name']})  
                    **加班日期**: {row['date']}  
                    **加班时长**: {row['hours']} 小时  
                    **事由**: {row['reason']}  
                    **申请时间**: {row['created_at']}
                    """)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ 批准", key=f"approve_overtime_{row['id']}", use_container_width=True, type="primary"):
                            if approve_overtime(row['id'], user['id'], 'approve'):
                                st.success(f"已批准 {row['applicant_name']} 的加班申请")
                                st.rerun()
                    with col2:
                        if st.button("❌ 拒绝", key=f"reject_overtime_{row['id']}", use_container_width=True):
                            if approve_overtime(row['id'], user['id'], 'reject'):
                                st.warning(f"已拒绝 {row['applicant_name']} 的加班申请")
                                st.rerun()
        else:
            st.info("暂无待审批的加班申请")

        st.markdown("---")
        st.subheader("审批历史")
        all_overtime = get_overtime_applications()
        if not all_overtime.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            all_overtime = all_overtime.copy()
            all_overtime["status"] = all_overtime["status"].map(status_map).fillna(all_overtime["status"])
            st.dataframe(all_overtime[['applicant_name', 'date', 'hours', 'reason', 'status', 'approver_name']].rename(columns={
                "applicant_name": "申请人", "date": "加班日期", "hours": "时长(小时)",
                "reason": "事由", "status": "状态", "approver_name": "审批人"
            }), use_container_width=True, hide_index=True)

    # ========== 统计报表 ==========
    elif selected == "统计报表" and user['role'] == 'admin':
        st.title("📈 统计报表")
        tab1, tab2, tab3 = st.tabs(["月度统计", "趋势分析", "打卡方式统计"])

        with tab1:
            st.subheader("月度考勤统计")
            current_year = datetime.now(BEIJING_TZ).year
            current_month = datetime.now(BEIJING_TZ).month
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("选择年份", list(range(current_year - 1, current_year + 2)), index=1, key='stat_year')
            with col2:
                month = st.selectbox("选择月份", list(range(1, 13)), index=current_month - 1, key='stat_month')
            monthly_stats = get_monthly_attendance_stats(year, month)
            if not monthly_stats.empty:
                st.dataframe(monthly_stats.rename(columns={
                    "id": "ID", "name": "姓名", "department_id": "部门ID",
                    "department_name": "部门", "attendance_days": "出勤天数",
                    "normal_days": "正常天数", "late_days": "迟到次数",
                    "early_leave_days": "早退次数", "absent_days": "缺勤次数"
                }), use_container_width=True, hide_index=True)
                st.download_button(label="📥 导出月度报表",
                                   data=monthly_stats.to_csv(index=False).encode('utf-8'),
                                   file_name=f'monthly_{year}_{month:02d}.csv',
                                   mime='text/csv', use_container_width=True)
            else:
                st.info("该月份暂无数据")

        with tab2:
            st.subheader("考勤趋势")
            trend_data = get_attendance_trend(30)
            if not trend_data.empty:
                trend_data['date'] = pd.to_datetime(trend_data['date'])
                line = alt.Chart(trend_data).mark_line().encode(
                    x='date:T', y='total_attendance:Q',
                    tooltip=['date', 'total_attendance', 'normal_count', 'late_count', 'early_leave_count']
                ).properties(title='每日出勤人数')
                st.altair_chart(line, use_container_width=True)
            else:
                st.info("暂无趋势数据")

        with tab3:
            st.subheader("打卡方式统计")
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()]
                    if 'checkin_method' in existing_cols:
                        # 检查是否有 face_verified 列
                        has_face_verified = 'face_verified' in existing_cols
                        if has_face_verified:
                            query = """
                                SELECT 
                                    COALESCE(checkin_method, 'manual') as method,
                                    COUNT(*) as count,
                                    SUM(COALESCE(face_verified, 0)) as face_verified_count
                                FROM attendance
                                GROUP BY COALESCE(checkin_method, 'manual')
                                ORDER BY count DESC
                            """
                        else:
                            query = """
                                SELECT 
                                    COALESCE(checkin_method, 'manual') as method,
                                    COUNT(*) as count
                                FROM attendance
                                GROUP BY COALESCE(checkin_method, 'manual')
                                ORDER BY count DESC
                            """
                        method_stats = pd.read_sql_query(query, conn)
                    else:
                        method_stats = pd.DataFrame()

                if not method_stats.empty:
                    method_stats['method_cn'] = method_stats['method'].apply(method_label_cn)
                    bar = alt.Chart(method_stats).mark_bar().encode(
                        x=alt.X('method_cn:N', title='打卡方式'),
                        y=alt.Y('count:Q', title='打卡次数'),
                        color=alt.Color('method_cn:N'),
                        tooltip=['method_cn', 'count']
                    ).properties(title='各打卡方式使用次数', height=300)
                    st.altair_chart(bar, use_container_width=True)

                    # 根据是否有 face_verified_count 决定显示哪些列
                    if 'face_verified_count' in method_stats.columns:
                        display_df = method_stats[['method_cn', 'count', 'face_verified_count']].rename(columns={
                            'method_cn': '打卡方式', 'count': '使用次数', 'face_verified_count': '人脸验证次数'
                        })
                    else:
                        display_df = method_stats[['method_cn', 'count']].rename(columns={
                            'method_cn': '打卡方式', 'count': '使用次数'
                        })
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("暂无打卡方式统计数据")
            except Exception as e:
                st.error(f"统计失败: {e}")

    # ========== 系统设置（移除了办公地点的排序控件）==========
    elif selected == "系统设置" and user['role'] == 'admin':
        st.title("⚙️ 系统设置")
        tab1, tab2, tab3, tab4 = st.tabs(["考勤规则", "办公地点", "系统信息", "操作日志"])

        with tab1:
            st.subheader("考勤规则设置")
            rules = get_attendance_rules()
            if not rules.empty:
                st.dataframe(rules[['rule_name', 'start_time', 'end_time', 'late_threshold',
                                    'early_leave_threshold', 'work_hours_per_day']].rename(columns={
                    "rule_name": "规则名称", "start_time": "上班时间", "end_time": "下班时间",
                    "late_threshold": "迟到阈值(分钟)", "early_leave_threshold": "早退阈值(分钟)",
                    "work_hours_per_day": "每日标准工时(小时)"
                }), use_container_width=True, hide_index=True)
            with st.expander("修改规则"):
                with st.form("new_rule_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        rule_name = st.text_input("规则名称")
                        start_time = st.time_input("上班时间", EXPECTED_START_TIME)
                        late_threshold = st.number_input("迟到阈值(分钟)", min_value=0, value=15)
                    with col2:
                        end_time = st.time_input("下班时间", EXPECTED_END_TIME)
                        early_leave_threshold = st.number_input("早退阈值(分钟)", min_value=0, value=15)
                        work_hours = st.number_input("每日标准工时(小时)", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
                    if st.form_submit_button("保存规则", use_container_width=True, type="primary"):
                        try:
                            with sqlite3.connect(DB_FILE) as conn:
                                conn.execute("UPDATE attendance_rules SET is_active = 0")
                                conn.execute("""
                                    INSERT INTO attendance_rules 
                                    (rule_name, start_time, end_time, late_threshold, early_leave_threshold, work_hours_per_day, is_active, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (rule_name, start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"),
                                      late_threshold, early_leave_threshold, work_hours, 1,
                                      datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                            log_action(user['id'], '修改考勤规则', f'新规则: {rule_name}')
                            st.success("考勤规则已保存")
                            st.rerun()
                        except Exception as e:
                            st.error(f"保存失败: {e}")

        with tab2:
            st.subheader("📍 办公地点管理（GPS围栏配置）")
            st.info("配置公司办公地点的经纬度和允许打卡范围，出差员工在范围外打卡将收到提示。")

            offices = get_office_locations()
            if not offices.empty:
                # 按 sort_order, id 排序
                offices = offices.sort_values(['sort_order', 'id']).reset_index(drop=True)
                # 添加连续序号
                offices.insert(0, '序号', range(1, len(offices) + 1))

                st.markdown("**当前配置的办公地点：**")
                # 显示时不显示数据库ID列
                display_offices = offices[['序号', 'name', 'latitude', 'longitude',
                                           'radius_meters', 'wifi_ssid', 'address']].rename(columns={
                    'name': '名称', 'latitude': '纬度', 'longitude': '经度',
                    'radius_meters': '允许范围(米)', 'wifi_ssid': 'WiFi名称', 'address': '地址'
                })
                st.dataframe(display_offices, use_container_width=True, hide_index=True)

                # 删除地点（选项显示序号+名称）
                del_options = ["不删除"] + [f"{r['序号']}. {r['name']}" for _, r in offices.iterrows()]
                del_choice = st.selectbox("删除地点", del_options)
                if del_choice != "不删除" and st.button("🗑️ 确认删除该地点", key="del_office"):
                    # 根据序号找到对应的id
                    selected_idx = int(del_choice.split('.')[0])
                    office_id = offices.loc[offices['序号'] == selected_idx, 'id'].iloc[0]
                    try:
                        with sqlite3.connect(DB_FILE) as conn:
                            conn.execute("UPDATE office_locations SET is_active = 0 WHERE id = ?", (office_id,))
                            conn.commit()
                        st.success("地点已删除")
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败: {e}")
            else:
                st.warning("尚未配置任何办公地点，GPS打卡将不做范围限制。")

            st.markdown("---")
            st.markdown("**添加新办公地点：**")
            with st.form("add_office_form"):
                col1, col2 = st.columns(2)
                with col1:
                    office_name = st.text_input("地点名称", placeholder="如：总部大楼、上海分公司")
                    office_lat = st.number_input("纬度", value=39.9042, format="%.6f", help="可在地图APP中查询")
                    office_radius = st.number_input("允许打卡范围(米)", min_value=50, max_value=2000, value=200)
                with col2:
                    office_address = st.text_input("详细地址", placeholder="如：北京市朝阳区XX路XX号")
                    office_lng = st.number_input("经度", value=116.4074, format="%.6f")
                    office_wifi = st.text_input("公司WiFi名称(SSID)", placeholder="选填，用于WiFi打卡验证")

                st.markdown("💡 提示：可在 [高德地图坐标拾取](https://lbs.amap.com/tools/picker) 中搜索地址获取精确经纬度")

                if st.form_submit_button("➕ 添加办公地点", use_container_width=True, type="primary"):
                    if not office_name:
                        st.error("请填写地点名称")
                    elif office_lat == 0.0 and office_lng == 0.0:
                        st.error("请填写正确的经纬度坐标")
                    else:
                        try:
                            with sqlite3.connect(DB_FILE) as conn:
                                # 获取当前最大sort_order
                                max_sort = conn.execute(
                                    "SELECT COALESCE(MAX(sort_order), 0) FROM office_locations WHERE is_active=1"
                                ).fetchone()[0]
                                conn.execute("""
                                    INSERT INTO office_locations 
                                    (name, latitude, longitude, radius_meters, wifi_ssid, address, is_active, sort_order, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                                """, (office_name, office_lat, office_lng, office_radius,
                                      office_wifi or None, office_address,
                                      max_sort + 1,
                                      datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                            log_action(user['id'], '添加办公地点', f'{office_name} ({office_lat},{office_lng})')
                            st.success(f"✅ 已添加办公地点：{office_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"添加失败: {e}")

        with tab3:
            st.subheader("系统信息")
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
                    leave_count = conn.execute("SELECT COUNT(*) FROM leaves").fetchone()[0]
                    overtime_count = conn.execute("SELECT COUNT(*) FROM overtime").fetchone()[0]
                    log_count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
                    face_count = conn.execute("SELECT COUNT(*) FROM face_encodings WHERE face_data IS NOT NULL").fetchone()[0]
                    office_count = conn.execute("SELECT COUNT(*) FROM office_locations WHERE is_active=1").fetchone()[0]

                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <p><strong>系统版本:</strong> 3.1.0（全功能修复版）</p>
                    <p><strong>用户数量:</strong> {user_count}</p>
                    <p><strong>考勤记录数:</strong> {attendance_count}</p>
                    <p><strong>人脸注册人数:</strong> {face_count}</p>
                    <p><strong>办公地点数:</strong> {office_count}</p>
                    <p><strong>请假记录数:</strong> {leave_count}</p>
                    <p><strong>加班记录数:</strong> {overtime_count}</p>
                    <p><strong>操作日志数:</strong> {log_count}</p>
                    <p><strong>数据库文件:</strong> {DB_FILE}</p>
                    <p><strong>最后更新时间:</strong> {datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("数据库备份")
                if st.button("下载数据库备份", use_container_width=True):
                    with open(DB_FILE, 'rb') as f:
                        st.download_button(
                            label="点击下载",
                            data=f,
                            file_name=f"backup_{datetime.now(BEIJING_TZ).strftime('%Y%m%d_%H%M%S')}.db",
                            mime='application/octet-stream',
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"系统信息读取失败: {e}")

        with tab4:
            st.subheader("操作日志")
            logs = get_logs(limit=200)
            if not logs.empty:
                st.dataframe(logs.rename(columns={
                    'user_name': '用户名', 'action': '操作', 'detail': '详情',
                    'ip': 'IP', 'created_at': '时间'
                })[['时间', '用户名', '操作', '详情']], use_container_width=True, hide_index=True)
            else:
                st.info("暂无日志记录")

    # ========== 个人中心（退出登录红色按钮）==========
    elif selected == "个人中心":
        st.title("👤 个人中心")

        tab1, tab2 = st.tabs(["基本信息", "人脸注册"])

        with tab1:
            st.markdown("### 基本信息")
            has_face = has_face_registered(user['id'])
            st.markdown(f"""
            <div style="background-color: white; padding: 16px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
                <p><strong>姓名:</strong> {user['name']}</p>
                <p><strong>工号:</strong> {user['username']}</p>
                <p><strong>部门:</strong> {user.get('department', '未分配')}</p>
                <p><strong>角色:</strong> {user['role']}</p>
                <p><strong>人脸注册:</strong> {'✅ 已注册' if has_face else '❌ 未注册，请在「人脸注册」标签页完成注册'}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ 修改姓名", use_container_width=True):
                    st.session_state.show_name_form = True
                    st.session_state.show_password_form = False
                    st.rerun()
            with col2:
                if st.button("🔑 修改密码", use_container_width=True):
                    st.session_state.show_password_form = True
                    st.session_state.show_name_form = False
                    st.rerun()

            if st.session_state.get('show_name_form', False):
                st.markdown("### 修改姓名")
                with st.form("change_name_form"):
                    new_name = st.text_input("新姓名", value=user['name'], placeholder="请输入新姓名")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button("保存", use_container_width=True, type="primary")
                    with col_cancel:
                        if st.form_submit_button("取消", use_container_width=True):
                            st.session_state.show_name_form = False
                            st.rerun()
                    if submitted:
                        if new_name and new_name != user['name']:
                            try:
                                with sqlite3.connect(DB_FILE) as conn:
                                    conn.execute("UPDATE users SET name = ? WHERE id = ?", (new_name, user['id']))
                                    conn.commit()
                                st.session_state.user['name'] = new_name
                                log_action(user['id'], '修改姓名', f'姓名改为 {new_name}')
                                st.success("姓名已更新")
                                st.session_state.show_name_form = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失败: {e}")
                        else:
                            st.warning("姓名未改变或为空")

            if st.session_state.get('show_password_form', False):
                st.markdown("### 修改密码")
                with st.form("change_password_form"):
                    old_pwd = st.text_input("当前密码", type="password", placeholder="请输入当前密码")
                    new_pwd = st.text_input("新密码", type="password", placeholder="请输入新密码")
                    confirm_pwd = st.text_input("确认新密码", type="password", placeholder="请再次输入密码")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button("保存", use_container_width=True, type="primary")
                    with col_cancel:
                        if st.form_submit_button("取消", use_container_width=True):
                            st.session_state.show_password_form = False
                            st.rerun()
                    if submitted:
                        if not old_pwd or not new_pwd or not confirm_pwd:
                            st.error("请填写完整")
                        elif new_pwd != confirm_pwd:
                            st.error("两次输入的新密码不一致")
                        else:
                            try:
                                with sqlite3.connect(DB_FILE) as conn:
                                    stored = conn.execute("SELECT password FROM users WHERE id = ?", (user['id'],)).fetchone()
                                    if stored and stored[0] == hash_password(old_pwd):
                                        conn.execute("UPDATE users SET password = ? WHERE id = ?",
                                                     (hash_password(new_pwd), user['id']))
                                        conn.commit()
                                        log_action(user['id'], '修改密码')
                                        st.success("密码已更新，请使用新密码登录")
                                        st.session_state.show_password_form = False
                                        st.rerun()
                                    else:
                                        st.error("当前密码不正确")
                            except Exception as e:
                                st.error(f"修改失败: {e}")

            st.markdown("---")
            # 退出登录红色按钮
            st.markdown('<div class="logout-btn-marker"></div>', unsafe_allow_html=True)
            if st.button("🚪 退出登录", key="logout", use_container_width=True):
                log_action(user['id'], '登出', f'用户 {user["username"]} 退出登录')
                st.session_state.user = None
                st.rerun()

        with tab2:
            render_face_registration(user)