import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import json
import os
import sqlite3
import subprocess
from rubii import rubii_login
import requests
import datetime
from PIL import Image, ImageTk  # 添加PIL库用于图像处理

# 数据库初始化
def init_db():
    conn = sqlite3.connect('chat_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (user_id TEXT, file_name TEXT, content TEXT)''')
    conn.commit()
    conn.close()
    
    # 初始化用户数据库和邮箱账户表
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_accounts
                 (email TEXT PRIMARY KEY, 
                  password TEXT,
                  is_active INTEGER DEFAULT 1,
                  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# 文件管理类
class FileManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.file_data = {}
    
    def load_config(self, file_listbox):
        try:
            conn = sqlite3.connect('chat_memory.db')
            c = conn.cursor()
            c.execute("SELECT file_name, content FROM files WHERE user_id=?", (self.user_id,))
            rows = c.fetchall()
            for i, (file_name, content) in enumerate(rows, 1):
                self.file_data[file_name] = content
                file_listbox.insert(tk.END, f" 📄 {i}. {file_name}")
            conn.close()
        except Exception as e:
            print(f"加载配置文件时出错：{e}")
    
    def save_to_db(self, file_name, content):
        try:
            conn = sqlite3.connect('chat_memory.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO files (user_id, file_name, content) VALUES (?,?,?)",
                      (self.user_id, file_name, content))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"保存文件到数据库时出错：{e}")
    
    def load_file(self, file_path, file_listbox):
        file_name = os.path.basename(file_path)
        if file_name not in self.file_data:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.file_data[file_name] = content
                    self.save_to_db(file_name, content)
                    # 获取当前列表中的文件数量作为序号
                    current_count = file_listbox.size() + 1
                    file_listbox.insert(tk.END, f" 📄 {current_count}. {file_name}")
            except Exception as e:
                print(f"加载文件 {file_path} 时出错：{e}")
    
    def delete_file(self, file_name):
        if file_name in self.file_data:
            del self.file_data[file_name]
            try:
                conn = sqlite3.connect('chat_memory.db')
                c = conn.cursor()
                c.execute("DELETE FROM files WHERE user_id=? AND file_name=?", (self.user_id, file_name))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"从数据库删除文件时出错：{e}")
                return False
        return False

# 用户管理类
class UserManager:
    @staticmethod
    def delete_user(username, tree_item, tree):
        if username == '1':
            messagebox.showerror("错误", "不能删除管理员账户！")
            return False
        
        if not messagebox.askyesno("确认删除", f"确定要删除用户 '{username}' 吗？\n此操作不可恢复！"):
            return False
        
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            
            # 删除用户数据
            c.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            
            # 从树形视图中移除
            tree.delete(tree_item)
            messagebox.showinfo("成功", f"用户 '{username}' 已被删除")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"删除用户失败：{str(e)}")
            return False
    
    @staticmethod
    def refresh_user_stats(tree):
        # 清空现有数据
        for item in tree.get_children():
            tree.delete(item)

        # 从数据库获取用户数据
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("""
                SELECT username, role, 
                       datetime(register_time, 'localtime'),
                       datetime(last_login, 'localtime'),
                       login_count
                FROM users
                ORDER BY register_time DESC
            """)
            users = c.fetchall()
            conn.close()

            # 插入数据到树形视图
            for user in users:
                tree.insert('', tk.END, values=(
                    user[0],  # 用户名
                    user[1],  # 角色
                    user[2],  # 注册时间
                    user[3] if user[3] else "从未登录",  # 最后登录时间
                    user[4]   # 登录次数
                ))
            return True
        except Exception as e:
            messagebox.showerror("错误", f"获取用户数据失败：{str(e)}")
            return False

# 宝石数据管理类
class GemManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.gold_info = None

    def load_gem_data(self):
        try:
            response = requests.get(f'http://localhost:3002/api/gems/get/{self.user_id}')
            if response.status_code == 200:
                result = response.json()
                if result and result.get('data'):
                    data = json.loads(result['data'])
                    return data.get('gems', [])
            return None
        except Exception as e:
            print(f"加载宝石数据时出错：{e}")
            return None

    def save_gem_data(self, data):
        try:
            payload = {
                "userId": self.user_id,
                "data": {
                    "gems": data if isinstance(data, list) else [data],
                    "updateTime": datetime.datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                'http://localhost:3002/api/gems/save',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            print(f"保存宝石数据时出错：{e}")
            return False

    def get_email_accounts(self):
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("SELECT email, password FROM email_accounts WHERE is_active = 1")
            accounts = c.fetchall()
            conn.close()
            return accounts
        except Exception as e:
            print(f"获取邮箱账户时出错：{e}")
            return []

    def refresh_gem_data(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            response = requests.get(f'http://localhost:3002/api/gems/get/{self.user_id}')
            if response.status_code == 200:
                result = response.json()
                if result and result.get('data'):
                    data = json.loads(result['data'])
                    if isinstance(data, dict):
                        if 'data' in data:
                            gems_data = data['data'].get('gems', [])
                        else:
                            gems_data = data.get('gems', [])
                    else:
                        gems_data = []
                    
                    for gem in gems_data:
                        if isinstance(gem, dict):
                            tree.insert("", "end", values=(
                                gem.get('name', 'N/A'),
                                gem.get('count', '0'),
                                gem.get('price', '0')
                            ))
                    
                    messagebox.showinfo("成功", "数据已刷新")
                else:
                    messagebox.showinfo("提示", "暂无数据")
        except Exception as e:
            messagebox.showerror("错误", f"刷新数据时出错：{str(e)}")

# 主应用类
class ChatMemoryApp:
    def __init__(self, user_id, user_role=None):
        self.user_id = user_id
        self.user_role = user_role
        
        # 初始化其他管理器
        self.file_manager = FileManager(user_id)
        self.gem_manager = GemManager(user_id)
        
        # 界面状态变量
        self.text_modified = False  # 用于标记文本是否修改
        self.current_keyword = ""  # 用于存储当前搜索的关键词
        self.highlighted_file_index = None  # 用于记录当前高亮的文件列表项索引
        self.welcome_visible = True  # 添加欢迎页面状态变量
        
        # 初始化数据库
        init_db()
        
        # 创建主窗口
        self.window = tk.Tk()
        self.window.title("Chat Memory")
        self.window.geometry("1200x800")
        
        # 设置窗口位置居中
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # 创建UI组件
        self.create_ui()
        
        # 加载数据
        self.file_manager.load_config(self.file_listbox)
        
        # 检查是否有历史宝石数据
        gem_data = self.gem_manager.load_gem_data()
        if gem_data:
            self.gem_manager.gold_info = gem_data
            
        # 初始隐藏文本区域
        self.text_area.pack_forget()
        
        # 显示欢迎页
        self.show_welcome_page()
    
    def create_ui(self):
        # 创建文件列表框架
        file_frame = tk.Frame(self.window)
        file_frame.pack(side=tk.LEFT, fill=tk.Y)

        # 滚动条
        scrollbar = tk.Scrollbar(file_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 搜索框和按钮 - 放在顶部
        search_frame = tk.Frame(file_frame)
        search_frame.pack(side=tk.TOP, pady=5)
        self.search_entry = tk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        search_button = tk.Button(search_frame, text="搜索", command=self.search_text)
        search_button.pack(side=tk.LEFT)

        # 左侧文件列表标题
        list_header = tk.Frame(file_frame, bg="#3a7ebf")
        list_header.pack(side=tk.TOP, fill=tk.X)
        
        header_label = tk.Label(
            list_header,
            text="文件列表",
            font=("微软雅黑", 12, "bold"),
            fg="white",
            bg="#3a7ebf",
            pady=8
        )
        header_label.pack()

        # 左侧文件列表
        self.file_listbox = tk.Listbox(
            file_frame, 
            width=30, 
            height=20, 
            yscrollcommand=scrollbar.set,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            activestyle='none',
            bd=0,
            highlightthickness=0
        )
        self.file_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.show_file_content)
        self.file_listbox.bind("<Button-3>", self.show_file_context_menu)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 程序logo，放在底部
        logo_frame = tk.Frame(file_frame, bg="#e0e0e5", height=50)
        logo_frame.pack(side=tk.BOTTOM, fill=tk.X)
        logo_frame.pack_propagate(False)  # 防止框架被内容压缩
        
        logo_label = tk.Label(
            logo_frame,
            text="Chat Memory",
            font=("微软雅黑", 16, "bold"),
            fg="#3a7ebf",
            bg="#e0e0e5"
        )
        logo_label.pack(expand=True)

        # 右键菜单
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="保存", command=self.save_file)
        self.context_menu.add_command(label="删除", command=self.delete_file)

        # 创建右侧内容框架
        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(expand=True, fill='both')
        
        # 创建欢迎页面框架
        self.welcome_frame = tk.Frame(self.content_frame, bg="#f0f0f5")
        
        # 创建文本区域（初始隐藏）
        self.text_area = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD, font=("Arial", 12))
        self.text_area.bind("<<Modified>>", self.on_text_modified)

        # 创建菜单栏
        self.menu_bar = tk.Menu(self.window)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="导入文件", command=self.open_files)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)

        # 字号调整菜单
        self.font_size_menu = tk.Menu(self.window, tearoff=0)
        self.font_size_menu.add_command(label="加大字号", command=self.increase_font_size)
        self.font_size_menu.add_command(label="缩小字号", command=self.decrease_font_size)
        self.menu_bar.add_cascade(label="字号", menu=self.font_size_menu)

        # 宝石按钮
        self.menu_bar.add_cascade(label="宝石", menu=None)
        self.menu_bar.entryconfig("宝石", command=self.show_gold_info)

        # 管理员按钮（仅对管理员显示）
        if self.user_role == 'admin':
            self.menu_bar.add_cascade(label="管理员", menu=None)
            self.menu_bar.entryconfig("管理员", command=self.show_user_stats)

        self.window.config(menu=self.menu_bar)

        # 绑定点击空白处的事件
        self.window.bind("<Button-1>", self.clear_selection)
    
    def show_welcome_page(self):
        # 隐藏文本区域
        self.text_area.pack_forget()
        
        # 清除标题框架
        if hasattr(self, 'title_frame'):
            self.title_frame.destroy()
            self.title_frame = None  # 确保完全清除引用
        
        # 清空并重新创建欢迎页面
        if hasattr(self, 'welcome_frame'):
            self.welcome_frame.destroy()
        
        # 创建新的欢迎页面
        self.welcome_frame = tk.Frame(self.content_frame, bg="#f0f0f5")
        self.welcome_frame.pack(expand=True, fill='both')
        
        # 顶部标题框架
        header_frame = tk.Frame(self.welcome_frame, bg="#3a7ebf")
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        # 程序logo和标题
        title_label = tk.Label(
            header_frame, 
            text="欢迎使用 Chat Memory", 
            font=("微软雅黑", 24, "bold"), 
            fg="white", 
            bg="#3a7ebf",
            pady=30
        )
        title_label.pack()
        
        # 主内容区域
        main_frame = tk.Frame(self.welcome_frame, bg="#f0f0f5", padx=50, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        # 用户信息区域
        user_frame = tk.Frame(main_frame, bg="#f0f0f5", pady=10)
        user_frame.pack(fill=tk.X)
        
        user_label = tk.Label(
            user_frame, 
            text=f"用户ID: {self.user_id}", 
            font=("微软雅黑", 14), 
            fg="#333333", 
            bg="#f0f0f5"
        )
        user_label.pack(anchor=tk.W)
        
        role_text = "管理员" if self.user_role == "admin" else "普通用户"
        role_label = tk.Label(
            user_frame, 
            text=f"用户角色: {role_text}", 
            font=("微软雅黑", 14), 
            fg="#333333", 
            bg="#f0f0f5"
        )
        role_label.pack(anchor=tk.W)
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)
        
        # 文件统计信息
        stats_frame = tk.Frame(main_frame, bg="#f0f0f5", pady=10)
        stats_frame.pack(fill=tk.X)
        
        file_count = self.file_listbox.size()
        stats_label = tk.Label(
            stats_frame, 
            text=f"您当前共有 {file_count} 个文件", 
            font=("微软雅黑", 14), 
            fg="#333333", 
            bg="#f0f0f5"
        )
        stats_label.pack(anchor=tk.W)
        
        # 功能介绍区域
        features_frame = tk.Frame(main_frame, bg="#f0f0f5", pady=20)
        features_frame.pack(fill=tk.X)
        
        features_title = tk.Label(
            features_frame, 
            text="功能指南", 
            font=("微软雅黑", 16, "bold"), 
            fg="#333333", 
            bg="#f0f0f5"
        )
        features_title.pack(anchor=tk.W)
        
        features = [
            "• 在左侧列表点击文件名查看文件内容",
            "• 使用搜索框查找关键词",
            "• 右键点击文件可以保存或删除",
            "• 使用导入账号提交账号后可一键登录",
            "• 使用一键登录可一键签到领宝石",
            "• 点击宝石菜单查看账号宝石余额"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                features_frame, 
                text=feature, 
                font=("微软雅黑", 12), 
                fg="#555555", 
                bg="#f0f0f5",
                pady=5
            )
            feature_label.pack(anchor=tk.W)
        
        # 快速操作区域
        buttons_frame = tk.Frame(main_frame, bg="#f0f0f5", pady=20)
        buttons_frame.pack(fill=tk.X)
        
        # 添加快捷导航标签
        nav_label = tk.Label(
            buttons_frame,
            text="快捷导航：",
            font=("微软雅黑", 12, "bold"),
            fg="#333333",
            bg="#f0f0f5",
            pady=5
        )
        nav_label.pack(side=tk.LEFT, padx=10)
        
        # 创建按钮样式
        style = ttk.Style()
        style.configure("Welcome.TButton", font=("微软雅黑", 12), padding=10)
        
        # 快速操作按钮
        import_btn = ttk.Button(
            buttons_frame, 
            text="导入文件", 
            command=self.open_files,
            style="Welcome.TButton"
        )
        import_btn.pack(side=tk.LEFT, padx=10)
        
        import_account_btn = ttk.Button(
            buttons_frame, 
            text="导入账号", 
            command=self.import_accounts,
            style="Welcome.TButton"
        )
        import_account_btn.pack(side=tk.LEFT, padx=10)
        
        login_btn = ttk.Button(
            buttons_frame, 
            text="一键登录", 
            command=self.login_and_get_gold,
            style="Welcome.TButton"
        )
        login_btn.pack(side=tk.LEFT, padx=10)
        
        gold_btn = ttk.Button(
            buttons_frame, 
            text="查看宝石", 
            command=self.show_gold_info,
            style="Welcome.TButton"
        )
        gold_btn.pack(side=tk.LEFT, padx=10)
        
        # 创建一个空的填充框架来推动版权信息到底部
        spacer_frame = tk.Frame(main_frame, bg="#f0f0f5")
        spacer_frame.pack(expand=True, fill='both')
        
        # 底部版权信息
        footer_frame = tk.Frame(self.welcome_frame, bg="#e0e0e5", height=50)  # 调整高度为50像素
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)  # 防止框架被内容压缩
        
        footer_label = tk.Label(
            footer_frame, 
            text="© 2025 Chat Memory - 版本 1.0", 
            font=("微软雅黑", 10), 
            fg="#777777", 
            bg="#e0e0e5"
        )
        footer_label.pack(expand=True)
        
        self.welcome_visible = True
    
    def switch_to_text_mode(self):
        if self.welcome_visible:
            self.welcome_frame.pack_forget()
            # 只有在title_frame存在时才显示它
            if hasattr(self, 'title_frame') and self.title_frame is not None:
                self.title_frame.pack(fill=tk.X, side=tk.TOP)
            self.text_area.pack(expand=True, fill='both')
            self.welcome_visible = False
    
    # === 文件操作方法 ===
    def open_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
        for file_path in file_paths:
            self.file_manager.load_file(file_path, self.file_listbox)
    
    def show_file_content(self, event=None):
        if not event:  # 如果没有事件，说明是程序启动时的初始化
            return
        
        selection = self.file_listbox.curselection()
        if not selection:  # 如果没有选中项，直接返回
            if self.welcome_visible:  # 如果当前在欢迎页，不做任何操作
                return
            else:  # 如果在文本模式，返回欢迎页
                self.show_welcome_page()
            return
            
        index = selection[0]
        list_item = self.file_listbox.get(index)
        # 从列表项中提取文件名（移除图标和序号）
        file_name = list_item.split(". ", 1)[1] if ". " in list_item else list_item
        
        content = self.file_manager.file_data.get(file_name)
        if not content:
            messagebox.showerror("错误", "无法读取文件内容")
            return
            
        # 更新或创建标题框架
        if hasattr(self, 'title_frame') and self.title_frame is not None:
            self.title_frame.destroy()
        
        # 创建新的标题框架
        self.title_frame = tk.Frame(self.content_frame, bg="#3a7ebf")
        self.title_frame.pack(fill=tk.X, side=tk.TOP)
        
        # 创建左侧标题容器
        title_container = tk.Frame(self.title_frame, bg="#3a7ebf")
        title_container.pack(side=tk.LEFT, expand=True, fill=tk.X, pady=10)
        
        # 添加文件图标
        icon_label = tk.Label(
            title_container,
            text="📄",  # 使用 Unicode 文件图标
            font=("微软雅黑", 16),
            fg="white",
            bg="#3a7ebf"
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加序号标签
        number_label = tk.Label(
            title_container,
            text=f"#{index + 1}",
            font=("微软雅黑", 12),
            fg="#a0cfff",
            bg="#3a7ebf"
        )
        number_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 文件名标题
        title_label = tk.Label(
            title_container,
            text=file_name,
            font=("微软雅黑", 14, "bold"),
            fg="white",
            bg="#3a7ebf"
        )
        title_label.pack(side=tk.LEFT)
        
        # 创建右侧按钮容器
        button_container = tk.Frame(self.title_frame, bg="#3a7ebf")
        button_container.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # 添加返回主页按钮
        home_button = tk.Button(
            button_container,
            text="返回主页",
            font=("微软雅黑", 10),
            fg="#3a7ebf",
            bg="white",
            bd=0,
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_welcome_page
        )
        home_button.pack(side=tk.RIGHT)
        
        # 为按钮添加悬停效果
        def on_enter(e):
            home_button['bg'] = '#e6e6e6'
        def on_leave(e):
            home_button['bg'] = 'white'
        
        home_button.bind('<Enter>', on_enter)
        home_button.bind('<Leave>', on_leave)
        
        # 切换到文本模式（隐藏欢迎页）
        self.switch_to_text_mode()
            
        # 更新文本内容
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, content)
        self.text_area.edit_modified(False)  # 重置修改状态
        self.text_modified = False  # 重置修改标记
        
        # 高亮关键词
        self.highlight_keyword_in_text(self.current_keyword)
        
        # 高亮文件列表项
        self.file_listbox.itemconfig(index, {'bg': 'lightblue'})  # 修改点击后的标题颜色为浅蓝色
        if self.highlighted_file_index is not None:
            self.file_listbox.itemconfig(self.highlighted_file_index, {'bg': 'white'})
        self.highlighted_file_index = index
    
    def save_file(self):
        if self.file_listbox.curselection():
            file_name = self.file_listbox.get(self.file_listbox.curselection())
            content = self.text_area.get("1.0", tk.END)
            self.file_manager.file_data[file_name] = content
            self.file_manager.save_to_db(file_name, content)
            self.text_area.edit_modified(False)  # 重置修改状态
            self.text_modified = False  # 重置修改标记
            # 高亮关键词
            self.highlight_keyword_in_text(self.current_keyword)
            print(f"已保存 '{file_name}'")
        else:
            print("请先选择要保存的文件")
    
    def delete_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection)
            if self.file_manager.delete_file(file_name):
                self.file_listbox.delete(selection)
                self.text_area.delete(1.0, tk.END)
                print(f"已删除 '{file_name}'")
        else:
            print("请先选择要删除的文件")
    
    def show_file_context_menu(self, event):
        try:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.file_listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    # === 搜索和高亮方法 ===
    def search_text(self):
        keyword = self.search_entry.get()
        self.current_keyword = keyword
        if keyword:
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            # 清除之前文件列表的高亮
            for i in range(self.file_listbox.size()):
                self.file_listbox.itemconfig(i, {'bg': 'white'})
            for file_name, content in self.file_manager.file_data.items():
                if keyword.lower() in content.lower():
                    for i in range(self.file_listbox.size()):
                        if self.file_listbox.get(i) == file_name:
                            self.file_listbox.itemconfig(i, {'bg': 'yellow'})
            self.highlighted_file_index = None
            # 高亮当前文本区域的关键词
            self.highlight_keyword_in_text(keyword)
        else:
            # 如果关键词为空，清除文件列表的高亮
            for i in range(self.file_listbox.size()):
                self.file_listbox.itemconfig(i, {'bg': 'white'})
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            self.highlighted_file_index = None
    
    def highlight_keyword_in_text(self, keyword):
        if keyword:
            start_pos = "1.0"
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            while True:
                start_pos = self.text_area.search(keyword, start_pos, stopindex=tk.END, nocase=True)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(keyword)}c"
                self.text_area.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos
            # 确保颜色设置生效
            self.text_area.tag_configure("highlight", background="yellow", foreground="black")
    
    # === 文本编辑方法 ===
    def on_text_modified(self, event):
        self.text_modified = True  # 标记文本已修改
        self.text_area.edit_modified(False)  # 重置修改状态
    
    def increase_font_size(self):
        current_font = self.text_area.cget("font")
        font_family, font_size = current_font.split(" ")
        new_size = int(font_size) + 2
        self.text_area.config(font=(font_family, new_size))
    
    def decrease_font_size(self):
        current_font = self.text_area.cget("font")
        font_family, font_size = current_font.split(" ")
        new_size = max(int(font_size) - 2, 6)  # 最小字号为6
        self.text_area.config(font=(font_family, new_size))
    
    def show_font_size_buttons(self):
        if not self.font_size_menu.winfo_ismapped():
            self.font_size_menu.post(self.menu_bar.winfo_rootx() + 80, self.menu_bar.winfo_rooty() + 30)
        else:
            self.font_size_menu.unpost()
    
    def clear_selection(self, event):
        self.file_listbox.selection_clear(0, tk.END)
    
    # === 宝石相关方法 ===
    def login_and_get_gold(self):
        accounts = self.gem_manager.get_email_accounts()
        if not accounts:
            messagebox.showwarning("警告", "没有可用的邮箱账户")
            return

        progress_window = tk.Toplevel(self.window)
        progress_window.title("登录进度")
        progress_window.geometry("300x150")
        
        progress_label = tk.Label(progress_window, text="正在登录...", pady=10)
        progress_label.pack()
        
        progress_bar = ttk.Progressbar(progress_window, length=200, mode='determinate')
        progress_bar.pack(pady=10)
        
        account_label = tk.Label(progress_window, text="")
        account_label.pack(pady=10)

        progress_bar['maximum'] = len(accounts)
        
        all_data = []
        for i, (email, password) in enumerate(accounts):
            progress_bar['value'] = i
            account_label.config(text=f"正在登录: {email}")
            progress_window.update()
            
            result = rubii_login(email=email, password=password)
            if result:
                all_data.append(result)
            
            self.window.after(1000)
        
        progress_bar['value'] = len(accounts)
        account_label.config(text="所有账号登录完成！")
        progress_window.after(2000, progress_window.destroy)
        
        if all_data:
            if self.gem_manager.save_gem_data(all_data):
                messagebox.showinfo("成功", "所有账号数据已保存")
            else:
                messagebox.showwarning("警告", "部分数据可能未保存成功")
        
        self.gem_manager.gold_info = all_data
    
    def show_gold_info(self):
        try:
            response = requests.get(f'http://localhost:3002/api/gems/get/{self.user_id}')
            
            if response.status_code == 200:
                result = response.json()
                
                if result and result.get('data'):
                    try:
                        data = json.loads(result['data'])
                        
                        if isinstance(data, dict):
                            if 'data' in data:
                                gems_data = data['data'].get('gems', [])
                            else:
                                gems_data = data.get('gems', [])
                        else:
                            gems_data = []
                        
                        if not gems_data:
                            messagebox.showinfo("提示", "暂无金币信息")
                            return
                        
                        popup = tk.Toplevel(self.window)
                        popup.title("所有账号金币信息")

                        window_x = self.window.winfo_x()
                        window_y = self.window.winfo_y()
                        window_width = self.window.winfo_width()
                        window_height = self.window.winfo_height()

                        popup_width = 400
                        popup_height = 300
                        x = window_x + (window_width - popup_width) // 2
                        y = window_y + (window_height - popup_height) // 2
                        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

                        tree = ttk.Treeview(popup, columns=("登录邮箱", "历史余额", "当前余额"), show="headings")
                        tree.heading("登录邮箱", text="登录邮箱")
                        tree.heading("历史余额", text="历史余额")
                        tree.heading("当前余额", text="当前余额")
                        
                        tree.column("登录邮箱", width=200)
                        tree.column("历史余额", width=100)
                        tree.column("当前余额", width=100)
                        
                        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=tree.yview)
                        tree.configure(yscrollcommand=scrollbar.set)
                        
                        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                        scrollbar.pack(side="right", fill="y", pady=10)

                        for gem in gems_data:
                            if isinstance(gem, dict):
                                tree.insert("", "end", values=(
                                    gem.get('name', 'N/A'),
                                    gem.get('count', '0'),
                                    gem.get('price', '0')
                                ))
                        
                        refresh_button = tk.Button(popup, text="刷新数据", 
                                                 command=lambda: self.gem_manager.refresh_gem_data(tree))
                        refresh_button.pack(side="bottom", pady=10)
                        
                    except json.JSONDecodeError as e:
                        messagebox.showerror("错误", "数据格式错误")
                        return
                else:
                    messagebox.showinfo("提示", "暂无金币信息，请先登录")
            else:
                messagebox.showinfo("提示", "获取数据失败")
        except Exception as e:
            messagebox.showerror("错误", f"显示金币信息时出错：{str(e)}")

    # === 用户管理方法 ===
    def show_user_stats(self):
        # 检查主窗口是否还存在
        if not self.window.winfo_exists():
            return

        # 创建新窗口
        stats_window = tk.Toplevel(self.window)
        stats_window.title("用户统计信息")
        stats_window.geometry("800x600")
        
        # 设置窗口在程序中心位置
        # 获取主窗口位置和大小
        main_x = self.window.winfo_x()
        main_y = self.window.winfo_y()
        main_width = self.window.winfo_width()
        main_height = self.window.winfo_height()
        
        # 计算弹窗的位置，使其居中
        popup_width = 800
        popup_height = 600
        x = main_x + (main_width - popup_width) // 2
        y = main_y + (main_height - popup_height) // 2
        
        # 设置弹窗位置
        stats_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        # 设置窗口模态
        stats_window.transient(self.window)
        stats_window.grab_set()

        # 创建树形视图
        columns = ('用户名', '角色', '注册时间', '最后登录', '登录次数')
        tree = ttk.Treeview(stats_window, columns=columns, show='headings')

        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(stats_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 删除用户函数
        def delete_user_handler():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("警告", "请先选择要删除的用户")
                return
            
            # 获取选中的用户信息
            user_values = tree.item(selected_item[0])['values']
            username = user_values[0]
            UserManager.delete_user(username, selected_item[0], tree)

        # 创建右键菜单
        context_menu = tk.Menu(stats_window, tearoff=0)
        context_menu.add_command(label="删除用户", command=delete_user_handler)

        # 绑定右键菜单
        def show_context_menu(event):
            # 先选中点击的项
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", show_context_menu)

        # 创建按钮框架
        button_frame = tk.Frame(stats_window)
        button_frame.pack(pady=10)

        # 添加刷新按钮
        refresh_btn = ttk.Button(button_frame, text="刷新数据", command=lambda: UserManager.refresh_user_stats(tree))
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # 添加删除按钮
        delete_btn = ttk.Button(button_frame, text="删除选中用户", command=delete_user_handler)
        delete_btn.pack(side=tk.LEFT, padx=5)

        # 初始加载数据
        UserManager.refresh_user_stats(tree)
    
    def import_accounts(self):
        # 创建导入账号对话框
        dialog = tk.Toplevel(self.window)
        dialog.title("导入Rubii账号")
        dialog.geometry("300x200")
        
        # 设置对话框位置在主窗口中心
        dialog.transient(self.window)
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 创建输入框和标签
        tk.Label(dialog, text="Rubii账号:", pady=5).pack()
        email_entry = tk.Entry(dialog, width=30)
        email_entry.pack(pady=5)
        
        tk.Label(dialog, text="Rubii密码:", pady=5).pack()
        password_entry = tk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        def submit():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            
            if not email or not password:
                messagebox.showwarning("警告", "请填写完整的账号和密码信息")
                return
            
            try:
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                
                # 检查账号是否已存在
                c.execute("SELECT email FROM email_accounts WHERE email = ?", (email,))
                if c.fetchone():
                    messagebox.showwarning("警告", "该账号已存在")
                    conn.close()
                    return
                
                # 插入新账号
                c.execute("INSERT INTO email_accounts (email, password) VALUES (?, ?)",
                         (email, password))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "账号导入成功")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("错误", f"导入账号时出错：{str(e)}")
                conn.close()
        
        # 提交按钮
        submit_btn = ttk.Button(dialog, text="提交", command=submit)
        submit_btn.pack(pady=20)
        
        # 设置对话框模态
        dialog.grab_set()
        dialog.focus_set()
    
    def run(self):
        self.window.mainloop()

def main_program(user_id=None, user_role=None):
    if not user_id:
        print("错误：未提供用户ID")
        return
    
    app = ChatMemoryApp(user_id, user_role)
    app.run()

if __name__ == "__main__":
    main_program()