import sqlite3
import hashlib
from datetime import datetime, time

def hash_password(password):
    """密码加密函数"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Create Departments table
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    manager_id INTEGER,
                    description TEXT
                )''')

    # Create Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    name TEXT NOT NULL,
                    department_id INTEGER,
                    email TEXT,
                    phone TEXT,
                    hire_date TEXT,
                    FOREIGN KEY (department_id) REFERENCES departments (id)
                )''')

    # Create Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    check_in TEXT,
                    check_out TEXT,
                    status TEXT,
                    work_hours REAL,
                    late_minutes INTEGER,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, date)
                )''')

    # Create Leave Applications table
    c.execute('''CREATE TABLE IF NOT EXISTS leaves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    leave_type TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    days INTEGER NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    approved_by INTEGER,
                    approved_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (approved_by) REFERENCES users (id)
                )''')

    # Create Attendance Rules table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    late_threshold INTEGER DEFAULT 15,
                    early_leave_threshold INTEGER DEFAULT 15,
                    work_hours_per_day REAL DEFAULT 8.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )''')

    # Create Overtime table
    c.execute('''CREATE TABLE IF NOT EXISTS overtime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    hours REAL NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    approved_by INTEGER,
                    approved_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (approved_by) REFERENCES users (id)
                )''')

    # Create Logs table
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    detail TEXT,
                    ip TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')

    # Insert default departments
    departments = [
        ('管理部', '总部管理部门'),
        ('技术部', '软件开发与技术支持'),
        ('人事部', '人力资源与行政'),
        ('销售部', '市场与销售'),
        ('财务部', '财务与会计')
    ]
    
    for dept in departments:
        try:
            c.execute("INSERT INTO departments (name, description) VALUES (?, ?)", dept)
        except sqlite3.IntegrityError:
            pass

    # Get department IDs
    c.execute("SELECT id, name FROM departments")
    dept_rows = c.fetchall()
    dept_dict = {name: id for id, name in dept_rows}

    # Insert sample users
    users = [
        ('admin', hash_password('admin123'), 'admin', '系统管理员', dept_dict.get('管理部'), 'admin@company.com', '13800138000', '2023-01-01'),
        ('user1', hash_password('123456'), 'employee', '张三', dept_dict.get('技术部'), 'user1@company.com', '13800138002', '2023-03-01'),
        ('user2', hash_password('123456'), 'employee', '李四', dept_dict.get('人事部'), 'user2@company.com', '13800138003', '2023-03-15'),
        ('user3', hash_password('123456'), 'employee', '王五', dept_dict.get('销售部'), 'user3@company.com', '13800138004', '2023-04-01'),
    ]

    for user in users:
        try:
            c.execute("INSERT INTO users (username, password, role, name, department_id, email, phone, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", user)
        except sqlite3.IntegrityError:
            pass

    # Insert default attendance rule
    try:
        default_rule = ('标准考勤规则', '09:00:00', '18:00:00', 15, 15, 8.0, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        c.execute("INSERT INTO attendance_rules (rule_name, start_time, end_time, late_threshold, early_leave_threshold, work_hours_per_day, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", default_rule)
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()
    print("✅ 数据库初始化成功！")
    print("✅ 默认管理员账号：admin / admin123")
    print("✅ 测试员工账号：user1, user2, user3 / 123456")

if __name__ == '__main__':
    init_db()