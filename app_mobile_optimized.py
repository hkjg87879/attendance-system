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
from dateutil.relativedelta import relativedelta
import subprocess
import sys

# --- 系统配置 ---
COMPANY_NAME = "企业考勤管理系统"
DB_FILE = 'attendance.db'
EXPECTED_START_TIME = time(9, 0, 0)  # 规定上班时间（北京时间）
EXPECTED_END_TIME = time(18, 0, 0)  # 规定下班时间（北京时间）
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 页面配置
st.set_page_config(
    page_title=COMPANY_NAME,
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 移动端检测 ---
def is_mobile():
    """检测是否是移动设备"""
    return st.session_state.get('is_mobile', False)


# --- 自定义CSS样式（包含移动端响应式设计）---
def load_css():
    st.markdown("""
        <style>
        /* 隐藏Streamlit默认菜单、footer、部署按钮 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {display: none;}
        [data-testid="stAppDeployButton"] {display: none !important;}

        /* 侧边栏样式 */
        [data-testid="stSidebar"] {
            background: #0F172A;
            color: #ffffff;
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255,255,255,0.2);
        }

        /* 侧边栏折叠按钮 */
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

        /* 登录卡片样式 */
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
        .register-inline a:hover {
            color: #EF4444;
        }

        /* 指标卡片样式 */
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border: none;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 6px 12px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
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

        /* 按钮样式 */
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

        /* 退出按钮红色样式 */
        .logout-button-container .stButton > button {
            background-color: #dc3545 !important;
            border-color: #dc3545 !important;
        }
        .logout-button-container .stButton > button:hover {
            background-color: #bb2d3b !important;
            border-color: #b02a37 !important;
        }

        /* 表格样式 */
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

        /* 状态徽章样式 */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-normal {
            background-color: #d1fae5;
            color: #065f46;
        }
        .status-late {
            background-color: #fee2e2;
            color: #991b1b;
        }
        .status-early {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-late-early {
            background-color: #fef3c7;
            color: #92400e;
        }
        .status-pending {
            background-color: #fef3c7;
            color: #92400e;
        }
        .status-approved {
            background-color: #d1fae5;
            color: #065f46;
        }
        .status-rejected {
            background-color: #fee2e2;
            color: #991b1b;
        }

        /* 页头样式 */
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
        .app-header .title {
            font-size: 20px;
            font-weight: 700;
            color: #111827;
        }
        .app-header .sub {
            font-size: 14px;
            color: #6B7280;
        }

        /* ===== 移动端响应式设计 (768px以下) ===== */
        @media (max-width: 768px) {
            /* 页头自适应 */
            .app-header {
                flex-direction: column;
                gap: 8px;
                padding: 10px 16px;
                border-radius: 8px;
            }
            .app-header .title {
                font-size: 18px;
            }
            .app-header .sub {
                font-size: 12px;
            }

            /* 指标卡片堆叠 */
            [data-testid="column"] {
                display: block !important;
                width: 100% !important;
                margin-bottom: 8px;
            }

            /* 表格字体缩小 */
            .dataframe {
                font-size: 12px;
                overflow-x: auto;
            }

            /* 表单输入字体放大（防止iOS缩放） */
            input, textarea, select {
                font-size: 16px !important;
            }

            /* 按钮高度增加（便于手指点击） */
            .stButton > button {
                padding: 12px 16px !important;
                min-height: 44px !important;
                font-size: 15px !important;
                border-radius: 8px !important;
            }

            /* 导航菜单响应式 */
            [data-testid="stHorizontalMenu"] {
                overflow-x: auto;
                white-space: nowrap;
                padding: 6px;
                -webkit-overflow-scrolling: touch;
            }

            /* 登录卡片 */
            .login-container {
                padding: 1.5rem 1.2rem;
                max-width: 100%;
                margin: 0 16px;
            }

            /* 指标卡片文字缩小 */
            .metric-value {
                font-size: 1.8rem;
            }
            .metric-label {
                font-size: 0.9rem;
            }

            /* 表单字段 */
            .stForm {
                padding: 16px;
                border-radius: 12px;
            }

            /* 打卡卡片 */
            .clock-card {
                padding: 12px;
                font-size: 14px;
            }

            /* 隐藏不必要的图表细节 */
            .altair-container {
                max-width: 100%;
            }
        }

        /* ===== 超小屏幕响应式设计 (480px以下) ===== */
        @media (max-width: 480px) {
            .app-header .title {
                font-size: 16px;
            }

            .app-header .sub {
                font-size: 11px;
            }

            .metric-value {
                font-size: 1.5rem;
            }

            .metric-label {
                font-size: 0.85rem;
            }

            .stButton > button {
                font-size: 13px;
                padding: 10px 12px !important;
                min-height: 40px !important;
            }

            .login-title {
                font-size: 22px;
            }

            .login-container {
                padding: 1.2rem 1rem;
            }

            /* 两列变一列 */
            .stForm {
                padding: 12px;
            }

            .status-badge {
                font-size: 10px;
                padding: 3px 8px;
            }

            /* 隐藏部分内容优化空间 */
            h1 { font-size: 1.3em !important; }
            h2 { font-size: 1.1em !important; }
            h3 { font-size: 1em !important; }
        }
        </style>
    """, unsafe_allow_html=True)


load_css()


# ==================== 数据库初始化（自动执行） ====================
def init_db_if_not_exists():
    """如果数据库文件不存在，则调用 init_db.py 初始化"""
    if not os.path.exists(DB_FILE):
        st.info("检测到数据库不存在，正在初始化...")
        try:
            # 尝试导入 init_db 并执行初始化
            import init_db
            init_db.init_db()
            st.success("数据库初始化完成！")
        except ImportError:
            # 如果导入失败（例如 init_db.py 不在同一目录），则通过子进程执行
            script_dir = os.path.dirname(os.path.abspath(__file__))
            init_script = os.path.join(script_dir, 'init_db.py')
            if os.path.exists(init_script):
                subprocess.run([sys.executable, init_script], check=True)
                st.success("数据库初始化完成！")
            else:
                st.error("找不到 init_db.py，无法初始化数据库，请手动执行初始化。")
        except Exception as e:
            st.error(f"数据库初始化失败: {e}")


# 应用启动时执行数据库初始化检查
init_db_if_not_exists()


# ==================== 数据库操作函数（全部使用 with 上下文） ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username, password):
    """
    登录验证：
    1. 优先匹配 secrets 中的超级管理员
    2. 失败则查询 SQLite 普通用户
    """
    # 1. 超级管理员验证
    try:
        admin_user = st.secrets.get("ADMIN_USER")
        admin_pass = st.secrets.get("ADMIN_PASSWORD")
        if admin_user and admin_pass and username == admin_user and password == admin_pass:
            # 构造一个虚拟管理员用户（不存储在数据库中）
            return {
                'id': -1,  # 特殊 ID 表示超管
                'username': admin_user,
                'name': '超级管理员',
                'role': 'admin',
                'department': '管理部',
                'department_id': None,
                'email': '',
                'phone': ''
            }
    except Exception:
        # secrets 未配置或读取失败，跳过
        pass

    # 2. 普通用户验证（查询数据库）
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
    return None


def log_action(user_id, action, detail='', ip=None):
    """记录操作日志"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO logs (user_id, action, detail, ip, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, action, detail, ip, datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
    except:
        pass


def register_user(username, password, name, department_id=None, email=None, phone=None):
    """注册新用户（普通员工）"""
    with sqlite3.connect(DB_FILE) as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            return False, "用户名已存在"
        conn.execute(
            "INSERT INTO users (username, password, role, name, department_id, email, phone, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, hash_password(password), "employee", name, department_id, email, phone,
             datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")),
        )
        conn.commit()
    return True, "注册成功，请使用新账号登录"


def update_user(user_id, username, name, department_id, role, email=None, phone=None):
    """更新用户信息"""
    with sqlite3.connect(DB_FILE) as conn:
        try:
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
    """删除用户及相关记录"""
    with sqlite3.connect(DB_FILE) as conn:
        try:
            conn.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM leaves WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM overtime WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM logs WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            return True, "删除成功"
        except Exception as e:
            return False, f"删除失败: {e}"


def get_attendance_status(user_id, date_str):
    """获取某天考勤记录"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        record = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (user_id, date_str)).fetchone()
        return dict(record) if record else None


def clock_in(user_id, date_str, time_str):
    """上班打卡"""
    with sqlite3.connect(DB_FILE) as conn:
        existing = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?',
                                (user_id, date_str)).fetchone()
        if existing:
            return False, "今日已打卡"
        check_in_dt = datetime.strptime(time_str, "%H:%M:%S").time()
        status = "正常" if check_in_dt <= EXPECTED_START_TIME else "迟到"
        conn.execute('INSERT INTO attendance (user_id, date, check_in, status) VALUES (?, ?, ?, ?)',
                     (user_id, date_str, time_str, status))
        conn.commit()
    log_action(user_id, '上班打卡', f'时间 {time_str} 状态 {status}')
    return True, "打卡成功" if status == "正常" else "已记录迟到"


def clock_out(user_id, date_str, time_str):
    """下班打卡"""
    with sqlite3.connect(DB_FILE) as conn:
        record = conn.execute('SELECT check_in, status FROM attendance WHERE user_id = ? AND date = ?',
                              (user_id, date_str)).fetchone()
        if not record:
            return False, "请先完成上班打卡"
        conn.execute('UPDATE attendance SET check_out = ? WHERE user_id = ? AND date = ?',
                     (time_str, user_id, date_str))
        check_out_time = datetime.strptime(time_str, "%H:%M:%S").time()
        current_status = record[1]
        new_status = current_status
        if check_out_time < EXPECTED_END_TIME:
            if current_status == "迟到":
                new_status = "迟到早退"
            elif current_status == "正常":
                new_status = "早退"
        if new_status != current_status:
            conn.execute('UPDATE attendance SET status = ? WHERE user_id = ? AND date = ?',
                         (new_status, user_id, date_str))
        conn.commit()
    log_action(user_id, '下班打卡', f'时间 {time_str} 状态 {new_status}')
    return True, "下班打卡成功"


def get_all_attendance():
    """获取所有考勤记录（用于报表）"""
    with sqlite3.connect(DB_FILE) as conn:
        query = """
            SELECT a.id, u.name, d.name as department, a.date, a.check_in, a.check_out, a.status
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN departments d ON u.department_id = d.id
            ORDER BY a.date DESC, a.check_in ASC
        """
        df = pd.read_sql_query(query, conn)
    return df


def get_departments():
    """获取部门列表"""
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT id, name, description FROM departments ORDER BY name", conn)
    return df


def get_attendance_rules():
    """获取当前激活的考勤规则"""
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM attendance_rules WHERE is_active = 1", conn)
    return df


def calculate_work_hours(check_in_str, check_out_str):
    """计算实际工时（扣除午餐1.5小时）"""
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
    except:
        return 0


def apply_leave(user_id, leave_type, start_date, end_date, reason):
    """提交请假申请"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    created_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_FILE) as conn:
        try:
            conn.execute("""
                INSERT INTO leaves (user_id, leave_type, start_date, end_date, days, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, leave_type, start_date, end_date, days, reason, created_at))
            conn.commit()
        except Exception as e:
            return False, f"提交失败: {str(e)}"
    log_action(user_id, '申请请假', f'{leave_type} {start_date}~{end_date} 共{days}天')
    return True, "请假申请提交成功"


def get_leave_applications(user_id=None, status=None):
    """获取请假申请列表"""
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


def apply_overtime(user_id, date, hours, reason):
    """提交加班申请"""
    created_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_FILE) as conn:
        try:
            conn.execute("""
                INSERT INTO overtime (user_id, date, hours, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, date, hours, reason, created_at))
            conn.commit()
        except Exception as e:
            return False, f"提交失败: {str(e)}"
    log_action(user_id, '申请加班', f'{date} 加班{hours}小时')
    return True, "加班申请提交成功"


def get_overtime_applications(user_id=None, status=None):
    """获取加班申请列表"""
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


def approve_overtime(overtime_id, approver_id, action):
    """审批加班"""
    status = 'approved' if action == 'approve' else 'rejected'
    now = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_FILE) as conn:
        try:
            conn.execute("""
                UPDATE overtime SET status = ?, approved_by = ?, approved_at = ?
                WHERE id = ?
            """, (status, approver_id, now, overtime_id))
            conn.commit()
        except Exception as e:
            return False
    log_action(approver_id, '审批加班', f'加班申请 {overtime_id} 状态 {status}')
    return True


def get_monthly_attendance_stats(year, month):
    """月度考勤统计"""
    with sqlite3.connect(DB_FILE) as conn:
        query = """
            SELECT 
                u.id,
                u.name,
                u.department_id,
                d.name as department_name,
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


def get_attendance_trend(days=30):
    """考勤趋势（过去N天）"""
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


def get_logs(user_id=None, limit=100):
    """获取操作日志"""
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


def update_attendance_record(record_id, check_in=None, check_out=None, status=None, notes=None):
    """更新考勤记录"""
    with sqlite3.connect(DB_FILE) as conn:
        updates = []
        params = []
        if check_in is not None:
            updates.append("check_in = ?")
            params.append(check_in)
        if check_out is not None:
            updates.append("check_out = ?")
            params.append(check_out)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if updates:
            query = f"UPDATE attendance SET {', '.join(updates)} WHERE id = ?"
            params.append(record_id)
            conn.execute(query, params)
            conn.commit()
    return True


def get_month_calendar_data(user_id, year, month):
    """获取月历考勤数据"""
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
        '正常': 'status-normal',
        '迟到': 'status-late',
        '早退': 'status-early',
        '迟到早退': 'status-late-early',
        '待审批': 'status-pending',
        '已批准': 'status-approved',
        '已拒绝': 'status-rejected'
    }
    css_class = color_map.get(status, '')
    return f'<span class="status-badge {css_class}">{status}</span>'


def get_late_status_from_final(final_status):
    return '迟到' if final_status in ['迟到', '迟到早退'] else '正常'


def get_early_status_from_final(final_status):
    return '早退' if final_status in ['早退', '迟到早退'] else '正常'


# ==================== 主程序逻辑 ====================

if 'user' not in st.session_state:
    st.session_state.user = None

# 未登录状态显示登录/注册界面
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
                reg_password2 = st.text_input("确认密码", type="password", placeholder="请再次输入密码",
                                              key="reg_password2")
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

    # 菜单选项定义
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

    # 页头
    # 获取北京时间并转换为中文星期
    now_beijing = datetime.now(BEIJING_TZ)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    chinese_weekday = weekdays[now_beijing.weekday()]

    st.markdown(f"""
    <div class="app-header">
        <div class="title">{COMPANY_NAME}</div>
        <div class="sub">{now_beijing.strftime("%Y年%m月%d日")} {chinese_weekday} {now_beijing.strftime("%H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

    # 水平导航菜单
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
        # 获取当前北京时间
        now_beijing = datetime.now(BEIJING_TZ)
        current_hour = now_beijing.hour
        current_time_str = now_beijing.strftime("%H:%M:%S")

        # 根据小时确定问候语
        if 5 <= current_hour < 12:
            greeting = "早安"
        elif 12 <= current_hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"

        st.title(f"👋 {greeting}, {user['name']}")

        # 激励语（可自定义或随机）
        st.markdown("✨ 新的一天，继续加油！")

        st.markdown("### 🕒 打卡签到")

        today_str = now_beijing.strftime("%Y-%m-%d")
        now_time_str = now_beijing.strftime("%H:%M:%S")
        record = get_attendance_status(user['id'], today_str)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="clock-card" style="padding: 16px; border-radius: 10px; background-color: #e3f2fd; border: 1px solid #90caf9; text-align: center;">
                <h4>⏰ 上班打卡</h4>
                <p style="margin: 8px 0; font-size: 14px;">规定时间: 09:00</p>
            </div>
            """, unsafe_allow_html=True)

            if record:
                st.markdown(f"✅ 已打卡: **{record['check_in']}**")
                late_status = get_late_status_from_final(record['status'])
                st.markdown(f"状态: {status_badge(late_status)}", unsafe_allow_html=True)
            else:
                if st.button("上班打卡", key="btn_check_in", use_container_width=True, type="primary"):
                    success, msg = clock_in(user['id'], today_str, now_time_str)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

        with col2:
            st.markdown("""
            <div class="clock-card" style="padding: 16px; border-radius: 10px; background-color: #f3e5f5; border: 1px solid #ce93d8; text-align: center;">
                <h4>🌙 下班打卡</h4>
                <p style="margin: 8px 0; font-size: 14px;">规定时间: 18:00</p>
            </div>
            """, unsafe_allow_html=True)

            if record and record['check_out']:
                st.markdown(f"✅ 已打卡: **{record['check_out']}**")
                early_status = get_early_status_from_final(record['status'])
                st.markdown(f"状态: {status_badge(early_status)}", unsafe_allow_html=True)
            elif record and not record['check_out']:
                if st.button("下班打卡", key="btn_check_out", use_container_width=True, type="primary"):
                    success, msg = clock_out(user['id'], today_str, now_time_str)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.markdown("🚫 请先完成上班打卡")

    # ========== 我的考勤 ==========
    elif selected == "我的考勤":
        st.title("📊 我的考勤记录")

        with st.expander("📅 考勤日历", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("年份",
                                    list(range(datetime.now(BEIJING_TZ).year - 1, datetime.now(BEIJING_TZ).year + 2)),
                                    index=1,
                                    key='cal_year')
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
                            status = status_row.iloc[0]['status']
                            cal_df.iloc[i, j] = f"{day} ({status})"
                        else:
                            cal_df.iloc[i, j] = f"{day} (未打卡)"
            st.dataframe(cal_df, use_container_width=True, hide_index=True)

        with sqlite3.connect(DB_FILE) as conn:
            history = pd.read_sql_query(
                "SELECT date, check_in, check_out, status FROM attendance WHERE user_id = ? ORDER BY date DESC",
                conn, params=(user['id'],))

        total_days = len(history)
        normal_days = len(history[history['status'] == '正常'])
        late_days = len(history[history['status'].isin(['迟到', '迟到早退'])])
        early_days = len(history[history['status'].isin(['早退', '迟到早退'])])

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
                in_df = history[['date', 'check_in', 'status']].copy()
                in_df['迟到状态'] = in_df['status'].apply(get_late_status_from_final)
                in_display = in_df.rename(columns={
                    'date': '日期',
                    'check_in': '上班时间',
                    '迟到状态': '状态'
                }).drop(columns=['status'])
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
                    out_display = out_df.rename(columns={
                        'date': '日期',
                        'check_out': '下班时间',
                        '早退状态': '状态'
                    }).drop(columns=['status'])
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
                    success, msg = apply_leave(
                        user['id'],
                        leave_type,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        reason
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("我的请假记录")
        my_leaves = get_leave_applications(user_id=user['id'])
        if not my_leaves.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            my_leaves = my_leaves.copy()
            my_leaves["status"] = my_leaves["status"].map(status_map).fillna(my_leaves["status"])
            display_cols = ['leave_type', 'start_date', 'end_date', 'days', 'reason', 'status']
            display_df = my_leaves[display_cols].rename(columns={
                'leave_type': '请假类型',
                'start_date': '开始日期',
                'end_date': '结束日期',
                'days': '天数',
                'reason': '事由',
                'status': '状态'
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
                    success, msg = apply_overtime(
                        user['id'],
                        overtime_date.strftime("%Y-%m-%d"),
                        hours,
                        reason
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("我的加班记录")
        my_overtime = get_overtime_applications(user_id=user['id'])
        if not my_overtime.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            my_overtime = my_overtime.copy()
            my_overtime["status"] = my_overtime["status"].map(status_map).fillna(my_overtime["status"])
            display_cols = ['date', 'hours', 'reason', 'status']
            display_df = my_overtime[display_cols].rename(columns={
                'date': '加班日期',
                'hours': '时长(小时)',
                'reason': '事由',
                'status': '状态'
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
            today_data = all_data[all_data['date'] == today_str]

            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)

            with sqlite3.connect(DB_FILE) as conn:
                total_employees = conn.execute("SELECT COUNT(*) FROM users WHERE role='employee'").fetchone()[0]

            checked_in = len(today_data)
            late_count = len(today_data[today_data['status'].isin(['迟到', '迟到早退'])])
            early_count = len(today_data[today_data['status'].isin(['早退', '迟到早退'])])
            absent_count = total_employees - checked_in

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
                st.subheader("部门出勤排行")
                dept_list = get_departments()['name'].tolist()
                if not today_data.empty:
                    dept_stats = today_data.groupby('department').agg(
                        迟到人数=('status', lambda x: (x.isin(['迟到', '迟到早退'])).sum()),
                        早退人数=('status', lambda x: (x.isin(['早退', '迟到早退'])).sum())
                    ).reset_index()
                else:
                    dept_stats = pd.DataFrame(columns=['department', '迟到人数', '早退人数'])
                for dept in dept_list:
                    if dept not in dept_stats['department'].values:
                        dept_stats = pd.concat(
                            [dept_stats, pd.DataFrame([{'department': dept, '迟到人数': 0, '早退人数': 0}])],
                            ignore_index=True)
                dept_stats_long = pd.melt(dept_stats, id_vars=['department'], var_name='类型', value_name='人数')
                bar = alt.Chart(dept_stats_long).mark_bar().encode(
                    x='人数:Q',
                    y=alt.Y('department:N', sort='-x'),
                    color='类型:N',
                    tooltip=['department', '类型', '人数']
                ).properties(height=300)
                st.altair_chart(bar, use_container_width=True)
        except Exception as e:
            st.error(f"控制台发生错误: {e}")

    # ========== 考勤报表 ==========
    elif selected == "考勤报表" and user['role'] == 'admin':
        try:
            st.title("📋 考勤数据报表")

            all_data = get_all_attendance()

            with st.expander("🔍 数据筛选", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    dept_filter = st.multiselect("筛选部门", options=all_data['department'].unique(),
                                                 default=all_data['department'].unique())
                with col2:
                    status_filter = st.multiselect("筛选状态", options=all_data['status'].unique(),
                                                   default=all_data['status'].unique())

            filtered_data = all_data[all_data['department'].isin(dept_filter) & all_data['status'].isin(status_filter)]

            st.subheader("模板导出")
            month_template = pd.DataFrame(
                columns=["月份", "部门", "员工", "正常天数", "迟到次数", "早退次数", "缺勤次数", "请假天数"])
            dept_template = pd.DataFrame(
                columns=["部门", "月份", "出勤天数", "迟到次数", "早退次数", "缺勤次数", "备注"])
            emp_template = pd.DataFrame(
                columns=["员工", "工号", "部门", "月份", "出勤天数", "迟到次数", "早退次数", "缺勤次数", "请假天数",
                         "备注"])
            template_map = {
                "按月模板": (month_template, "template_month.csv"),
                "按部门模板": (dept_template, "template_department.csv"),
                "按员工模板": (emp_template, "template_employee.csv"),
            }
            template_choice = st.selectbox("选择导出模板", list(template_map.keys()))
            template_df, template_name = template_map[template_choice]
            st.download_button(
                label="下载模板",
                data=template_df.to_csv(index=False).encode('utf-8'),
                file_name=template_name,
                mime='text/csv'
            )

            st.dataframe(filtered_data.rename(columns={
                "id": "ID",
                "name": "姓名",
                "department": "部门",
                "date": "日期",
                "check_in": "上班时间",
                "check_out": "下班时间",
                "status": "状态"
            }), use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 导出 CSV",
                data=filtered_data.to_csv(index=False).encode('utf-8'),
                file_name=f'attendance_report_{datetime.now(BEIJING_TZ).strftime("%Y%m%d")}.csv',
                mime='text/csv',
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"报表发生错误: {e}")

    # ========== 员工管理 ==========
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
                    dept_map = {row['name']: row['id'] for _, row in
                                departments.iterrows()} if not departments.empty else {}
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

        with sqlite3.connect(DB_FILE) as conn:
            users_df = pd.read_sql_query(
                "SELECT u.id, u.username, u.name, u.role, u.department_id, d.name as department, u.email, u.phone FROM users u LEFT JOIN departments d ON u.department_id = d.id",
                conn)

        users_display = users_df.rename(columns={
            "id": "ID",
            "username": "用户名",
            "name": "姓名",
            "department": "部门",
            "role": "角色",
            "email": "邮箱",
            "phone": "电话"
        })
        st.dataframe(users_display, use_container_width=True, hide_index=True)

        st.subheader("🔧 管理操作")
        if not users_df.empty:
            emp_options = {f"{row['id']} - {row['name']} ({row['username']})": row['id'] for _, row in
                           users_df.iterrows()}
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
                                                 index=["employee", "admin"].index(emp_data['role']) if emp_data[
                                                                                                            'role'] in [
                                                                                                            "employee",
                                                                                                            "admin"] else 0)
                    with col2:
                        dept_idx = 0
                        if emp_data['department'] in dept_options:
                            dept_idx = dept_options.index(emp_data['department'])
                        edit_dept = st.selectbox("部门", dept_options, index=dept_idx, key="edit_dept_select")
                        edit_email = st.text_input("邮箱", value=emp_data['email'] if emp_data['email'] else "")
                        edit_phone = st.text_input("电话", value=emp_data['phone'] if emp_data['phone'] else "")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("保存修改", use_container_width=True, type="primary"):
                            dept_id = dept_map.get(edit_dept)
                            ok, msg = update_user(emp_id, edit_username, edit_name, dept_id, edit_role, edit_email,
                                                  edit_phone)
                            if ok:
                                st.success(msg)
                                log_action(user['id'], '编辑员工', f'用户ID {emp_id}')
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_cancel:
                        if st.form_submit_button("取消", use_container_width=True):
                            pass

                if st.button("🗑️ 删除该员工", type="primary", use_container_width=True):
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
                with st.expander(
                        f"{row['applicant_name']} - {row['leave_type']} ({row['start_date']} 至 {row['end_date']})"):
                    st.markdown(f"""
                    **申请人**: {row['applicant_name']} ({row['department_name']})

                    **请假类型**: {row['leave_type']}

                    **时间**: {row['start_date']} 至 {row['end_date']} (共 {row['days']} 天)

                    **事由**: {row['reason']}

                    **申请时间**: {row['created_at']}
                    """)

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ 批准", key=f"approve_leave_{row['id']}", use_container_width=True,
                                     type="primary"):
                            with sqlite3.connect(DB_FILE) as conn:
                                conn.execute("""
                                    UPDATE leaves SET status = 'approved', approved_by = ?, approved_at = ?
                                    WHERE id = ?
                                """, (user['id'], datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"), row['id']))
                                conn.commit()
                            log_action(user['id'], '审批请假', f'批准请假 {row["id"]}')
                            st.success(f"已批准 {row['applicant_name']} 的请假申请")
                            st.rerun()
                    with col2:
                        if st.button("❌ 拒绝", key=f"reject_leave_{row['id']}", use_container_width=True):
                            with sqlite3.connect(DB_FILE) as conn:
                                conn.execute(
                                    "UPDATE leaves SET status = 'rejected', approved_by = ?, approved_at = ? WHERE id = ?",
                                    (user['id'], datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"), row['id']))
                                conn.commit()
                            log_action(user['id'], '审批请假', f'拒绝请假 {row["id"]}')
                            st.warning(f"已拒绝 {row['applicant_name']} 的请假申请")
                            st.rerun()
        else:
            st.info("暂无待审批的请假申请")

        st.markdown("---")
        st.subheader("审批历史")
        all_leaves = get_leave_applications()
        if not all_leaves.empty:
            status_map = {"pending": "待审批", "approved": "已批准", "rejected": "已拒绝"}
            all_leaves = all_leaves.copy()
            all_leaves["status"] = all_leaves["status"].map(status_map).fillna(all_leaves["status"])

            approval_history_display = all_leaves[
                ['applicant_name', 'leave_type', 'start_date', 'end_date', 'status', 'approver_name']].rename(columns={
                "applicant_name": "申请人",
                "leave_type": "请假类型",
                "start_date": "开始日期",
                "end_date": "结束日期",
                "status": "状态",
                "approver_name": "审批人"
            })
            st.dataframe(approval_history_display, use_container_width=True, hide_index=True)
        else:
            st.info("暂无审批记录")
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
                        if st.button("✅ 批准", key=f"approve_overtime_{row['id']}", use_container_width=True,
                                     type="primary"):
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

            history_display = all_overtime[
                ['applicant_name', 'date', 'hours', 'reason', 'status', 'approver_name']].rename(columns={
                "applicant_name": "申请人",
                "date": "加班日期",
                "hours": "时长(小时)",
                "reason": "事由",
                "status": "状态",
                "approver_name": "审批人"
            })
            st.dataframe(history_display, use_container_width=True, hide_index=True)
        else:
            st.info("暂无审批记录")

    # ========== 统计报表 ==========
    elif selected == "统计报表" and user['role'] == 'admin':
        st.title("📈 统计报表")

        tab1, tab2 = st.tabs(["月度统计", "趋势分析"])

        with tab1:
            st.subheader("月度考勤统计")
            current_year = datetime.now(BEIJING_TZ).year
            current_month = datetime.now(BEIJING_TZ).month

            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("选择年份", list(range(current_year - 1, current_year + 2)), index=1,
                                    key='stat_year')
            with col2:
                month = st.selectbox("选择月份", list(range(1, 13)), index=current_month - 1, key='stat_month')

            monthly_stats = get_monthly_attendance_stats(year, month)
            if not monthly_stats.empty:
                monthly_stats_display = monthly_stats.rename(columns={
                    "id": "ID",
                    "name": "姓名",
                    "department_id": "部门ID",
                    "department_name": "部门",
                    "attendance_days": "出勤天数",
                    "normal_days": "正常天数",
                    "late_days": "迟到次数",
                    "early_leave_days": "早退次数",
                    "absent_days": "缺勤次数"
                })
                st.dataframe(monthly_stats_display, use_container_width=True, hide_index=True)

                csv = monthly_stats_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 导出月度报表",
                    data=csv,
                    file_name=f'monthly_attendance_{year}_{month:02d}.csv',
                    mime='text/csv',
                    use_container_width=True
                )
            else:
                st.info("该月份暂无数据")

        with tab2:
            st.subheader("考勤趋势")
            trend_data = get_attendance_trend(30)
            if not trend_data.empty:
                trend_data['date'] = pd.to_datetime(trend_data['date'])
                line = alt.Chart(trend_data).mark_line().encode(
                    x='date:T',
                    y='total_attendance:Q',
                    tooltip=['date', 'total_attendance', 'normal_count', 'late_count', 'early_leave_count']
                ).properties(title='每日出勤人数')
                st.altair_chart(line, use_container_width=True)
            else:
                st.info("暂无趋势数据")

    # ========== 系统设置 ==========
    elif selected == "系统设置" and user['role'] == 'admin':
        st.title("⚙️ 系统设置")

        tab1, tab2, tab3 = st.tabs(["考勤规则", "系统信息", "操作日志"])

        with tab1:
            st.subheader("考勤规则设置")
            rules = get_attendance_rules()
            if not rules.empty:
                rules_display = rules[['rule_name', 'start_time', 'end_time', 'late_threshold', 'early_leave_threshold',
                                       'work_hours_per_day']].rename(columns={
                    "rule_name": "规则名称",
                    "start_time": "上班时间",
                    "end_time": "下班时间",
                    "late_threshold": "迟到阈值(分钟)",
                    "early_leave_threshold": "早退阈值(分钟)",
                    "work_hours_per_day": "每日标准工时(小时)"
                })
                st.dataframe(rules_display, use_container_width=True, hide_index=True)
            else:
                st.info("暂无考勤规则")

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
                        work_hours = st.number_input("每日标准工时(小时)", min_value=1.0, max_value=12.0, value=8.0,
                                                     step=0.5)

                    if st.form_submit_button("保存规则", use_container_width=True, type="primary"):
                        with sqlite3.connect(DB_FILE) as conn:
                            conn.execute("UPDATE attendance_rules SET is_active = 0")
                            conn.execute("""
                                INSERT INTO attendance_rules (rule_name, start_time, end_time, late_threshold, early_leave_threshold, work_hours_per_day, is_active, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                            rule_name, start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"), late_threshold,
                            early_leave_threshold, work_hours, 1,
                            datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                        log_action(user['id'], '修改考勤规则', f'新规则: {rule_name}')
                        st.success("考勤规则已保存")
                        st.rerun()

        with tab2:
            st.subheader("系统信息")
            with sqlite3.connect(DB_FILE) as conn:
                user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
                leave_count = conn.execute("SELECT COUNT(*) FROM leaves").fetchone()[0]
                overtime_count = conn.execute("SELECT COUNT(*) FROM overtime").fetchone()[0]
                log_count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]

            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <p><strong>系统版本:</strong> 2.0.0 (移动优化版)</p>
                <p><strong>用户数量:</strong> {user_count}</p>
                <p><strong>考勤记录数:</strong> {attendance_count}</p>
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

        with tab3:
            st.subheader("操作日志")
            logs = get_logs(limit=200)
            if not logs.empty:
                logs_display = logs.rename(columns={
                    'user_name': '用户名',
                    'action': '操作',
                    'detail': '详情',
                    'ip': 'IP',
                    'created_at': '时间'
                })
                st.dataframe(logs_display[['时间', '用户名', '操作', '详情']], use_container_width=True,
                             hide_index=True)
            else:
                st.info("暂无日志记录")

    # ========== 个人中心 ==========
    elif selected == "个人中心":
        st.title("👤 个人中心")

        # 基本信息展示
        st.markdown("### 基本信息")
        st.markdown(f"""
        <div style="background-color: white; padding: 16px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <p><strong>姓名:</strong> {user['name']}</p>
            <p><strong>工号:</strong> {user['username']}</p>
            <p><strong>部门:</strong> {user.get('department', '未分配')}</p>
            <p><strong>角色:</strong> {user['role']}</p>
        </div>
        """, unsafe_allow_html=True)

        # 修改按钮
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

        # 修改姓名表单
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
                        with sqlite3.connect(DB_FILE) as conn:
                            conn.execute("UPDATE users SET name = ? WHERE id = ?", (new_name, user['id']))
                            conn.commit()
                        st.session_state.user['name'] = new_name
                        log_action(user['id'], '修改姓名', f'姓名改为 {new_name}')
                        st.success("姓名已更新")
                        st.session_state.show_name_form = False
                        st.rerun()
                    else:
                        st.warning("姓名未改变或为空")

        # 修改密码表单
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

        st.markdown("---")

        # 退出登录按钮
        st.markdown('<div class="logout-button-container">', unsafe_allow_html=True)
        if st.button("退出登录", key="logout", use_container_width=True):
            log_action(user['id'], '登出', f'用户 {user["username"]} 退出登录')
            st.session_state.user = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)