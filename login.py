# login.py
import tkinter as tk
from tkinter import messagebox
import requests
import main_program  # 导入 main_program 模块
import os  # 添加 os 模块
import datetime  # 添加 datetime 模块

# API配置
API_BASE_URL = os.getenv("API_BASE_URL", "https://your-railway-app-url.railway.app")

# 检查数据库文件是否存在
db_path = 'users.db'
if os.path.exists(db_path):
    print(f"数据库文件存在于: {os.path.abspath(db_path)}")
else:
    print(f"数据库文件不存在，将在首次连接时创建")

# 连接到 SQLite 数据库
conn = sqlite3.connect('users.db')
c = conn.cursor()

# 获取现有用户数据
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if c.fetchone() is not None:
    print("备份现有用户数据...")
    c.execute("SELECT username, password, role, register_time, last_login, login_count FROM users")
    existing_users = c.fetchall()
    
    print("删除旧的用户表...")
    c.execute("DROP TABLE IF EXISTS users")
    conn.commit()
else:
    existing_users = []

# 创建新的用户表
print("创建新的用户表结构...")
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, 
              password TEXT,
              role TEXT DEFAULT 'user',
              register_time TIMESTAMP,
              last_login TIMESTAMP,
              login_count INTEGER DEFAULT 0)''')

# 恢复现有用户数据
if existing_users:
    print("恢复用户数据...")
    for user_data in existing_users:
        c.execute("""
            INSERT INTO users (username, password, role, register_time, last_login, login_count) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, user_data)

conn.commit()

# 确保用户1的角色是管理员
print("确保用户1为管理员...")
c.execute("UPDATE users SET role = 'admin' WHERE username = '1'")
conn.commit()

# 删除旧的宝石数据表（如果存在）
c.execute('DROP TABLE IF EXISTS gem_data')

# 创建新的宝石数据表（如果不存在）
c.execute('''CREATE TABLE IF NOT EXISTS gem_data
             (username TEXT,
              email TEXT,
              gold_before TEXT,
              gold_after TEXT,
              update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (username, email))''')

# 创建邮箱账户表（如果不存在）
c.execute('''CREATE TABLE IF NOT EXISTS email_accounts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              password TEXT,
              is_active INTEGER DEFAULT 1)''')
conn.commit()

# 添加默认的邮箱账户（如果表为空）
def init_default_emails():
    c.execute("SELECT COUNT(*) FROM email_accounts")
    if c.fetchone()[0] == 0:
        default_accounts = [
            ("1176171890@qq.com", "ouhao1992"),
            ("dengli398127@163.com", "ouhao1992??"),
            ("wanghangkua218936@163.com", "ouhao1992??"),
            ("lixuqian725734@163.com", "ouhao1992??"),
            ("shiyiang050445@163.com", "ouhao1992??"),
            ("caijieshuo811570@163.com", "ouhao1992??"),
            ("maoyiming935008@163.com", "ouhao1992??"),
            ("nrouyi4573767@163.com", "ouhao1992??")
        ]
        c.executemany("INSERT OR IGNORE INTO email_accounts (email, password) VALUES (?, ?)", 
                     default_accounts)
        conn.commit()

init_default_emails()

# 登录函数
def login():
    username = username_entry.get()
    password = password_entry.get()
    
    # 验证用户名和密码不能为空
    if not username or not password:
        messagebox.showerror("登录失败", "用户名和密码不能为空")
        return
        
    try:
        # 获取访问令牌
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            # 获取用户信息
            user_response = requests.get(
                f"{API_BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                messagebox.showinfo("登录成功", "欢迎使用 Chat Memory")
                root.destroy()
                main_program.main_program(user_id=username, user_role=user_data['role'])
            else:
                messagebox.showerror("错误", "获取用户信息失败")
        else:
            messagebox.showerror("登录失败", "用户名或密码错误")
            password_entry.delete(0, tk.END)
    except requests.exceptions.RequestException as e:
        messagebox.showerror("错误", f"连接服务器失败: {str(e)}")

# 注册对话框函数
def register_dialog():
    register_window = tk.Toplevel(root)
    register_window.title("注册")

    # 设置弹窗大小和位置
    popup_width = 400
    popup_height = 450
    x = (root.winfo_screenwidth() // 2) - (popup_width // 2)
    y = (root.winfo_screenheight() // 2) - (popup_height // 2)
    register_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    register_window.configure(bg='#F0F0F0')  # 使用更柔和的背景色

    # 创建主框架，增加内边距
    main_frame = tk.Frame(register_window, bg='#F0F0F0', padx=40, pady=30)
    main_frame.pack(expand=True, fill='both')

    # 标题
    title_label = tk.Label(main_frame, text="创建新账号", 
                          font=("Helvetica", 18, "bold"),
                          bg='#F0F0F0', fg='#333333')
    title_label.pack(pady=(0, 30))

    # 创建表单框架
    form_frame = tk.Frame(main_frame, bg='#F0F0F0')
    form_frame.pack(fill='x')

    # 统一的样式设置
    label_style = {"bg": '#F0F0F0', "fg": '#333333', "font": ("Helvetica", 12)}
    entry_style = {
        "font": ("Helvetica", 11),
        "relief": "solid",
        "bd": 1,
        "width": 25
    }

    # 用户名区域
    username_frame = tk.Frame(form_frame, bg='#F0F0F0')
    username_frame.pack(fill='x', pady=(0, 15))
    username_label = tk.Label(username_frame, text="用户名", **label_style)
    username_label.pack(anchor='w')
    new_username_entry = tk.Entry(username_frame, **entry_style)
    new_username_entry.pack(pady=(5, 0))

    # 密码区域
    password_frame = tk.Frame(form_frame, bg='#F0F0F0')
    password_frame.pack(fill='x', pady=(0, 15))
    password_label = tk.Label(password_frame, text="密码", **label_style)
    password_label.pack(anchor='w')
    new_password_entry = tk.Entry(password_frame, show="•", **entry_style)
    new_password_entry.pack(pady=(5, 0))

    # 确认密码区域
    confirm_frame = tk.Frame(form_frame, bg='#F0F0F0')
    confirm_frame.pack(fill='x', pady=(0, 25))
    confirm_label = tk.Label(confirm_frame, text="确认密码", **label_style)
    confirm_label.pack(anchor='w')
    confirm_password_entry = tk.Entry(confirm_frame, show="•", **entry_style)
    confirm_password_entry.pack(pady=(5, 0))

    # 注册按钮
    def register_user():
        new_username = new_username_entry.get()
        new_password = new_password_entry.get()
        confirm_password = confirm_password_entry.get()

        # 验证用户名和密码不能为空
        if not new_username or not new_password:
            messagebox.showerror("注册失败", "用户名和密码不能为空")
            return
            
        # 验证密码长度
        if len(new_password) < 5:
            messagebox.showerror("注册失败", "密码长度必须大于5位")
            return

        if new_password == confirm_password:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/register",
                    json={"username": new_username, "password": new_password}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("注册成功", "注册成功，请登录")
                    register_window.destroy()
                else:
                    error_msg = response.json().get('detail', '注册失败')
                    messagebox.showerror("注册失败", error_msg)
            except requests.exceptions.RequestException as e:
                messagebox.showerror("错误", f"连接服务器失败: {str(e)}")
        else:
            messagebox.showerror("注册失败", "两次输入的密码不一致")

    register_button = tk.Button(
        main_frame, 
        text="注册",
        command=register_user,
        font=("Helvetica", 12),
        bg='#4CAF50',  # 使用绿色作为主色调
        fg='white',
        width=20,
        height=2,
        relief='flat',
        cursor='hand2'  # 鼠标悬停时显示手型
    )
    register_button.pack(pady=(0, 20))

    # 添加鼠标悬停效果
    def on_enter(e):
        register_button['bg'] = '#45a049'

    def on_leave(e):
        register_button['bg'] = '#4CAF50'

    register_button.bind("<Enter>", on_enter)
    register_button.bind("<Leave>", on_leave)

    # 设置窗口为模态
    register_window.transient(root)
    register_window.grab_set()

# 注册函数
def register():
    register_dialog()

# 创建主窗口
root = tk.Tk()
root.title("Chat Memory")
root.configure(bg="black")  # 设置主窗口背景为黑色

# 获取屏幕宽度和高度
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 设置窗口大小和位置
window_width = 700
window_height = 500
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# 添加艺术性标题
title_label = tk.Label(root, text="Chat Memory", font=("Helvetica", 26, "bold italic"), bg="black", fg="white")
title_label.pack(pady=20)

# 创建一个中心框架
center_frame = tk.Frame(root, bg="black")
center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# 用户名标签和输入框
username_label = tk.Label(center_frame, text="用户名:", bg="black", fg="white")
username_label.pack(pady=20)
username_entry = tk.Entry(center_frame, bg="white", fg="black")
username_entry.pack(pady=5)

# 密码标签和输入框
password_label = tk.Label(center_frame, text="密码:", bg="black", fg="white")
password_label.pack(pady=20)
password_entry = tk.Entry(center_frame, show="*", bg="white", fg="black")
password_entry.pack(pady=5)

# 登录和注册按钮并排
button_frame = tk.Frame(center_frame, bg="black")
button_frame.pack(pady=20)

login_button = tk.Button(button_frame, text="登录", command=login, bg="white", fg="black")
login_button.pack(side=tk.LEFT, padx=10)

register_button = tk.Button(button_frame, text="注册", command=register, bg="white", fg="black")
register_button.pack(side=tk.LEFT, padx=10)

# 运行主循环
root.mainloop()

# 关闭数据库连接
conn.close()