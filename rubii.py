from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import undetected_chromedriver as uc  # 规避检测
import sqlite3

def get_history_gold(email):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # 获取该邮箱最近一次的当前余额作为历史余额
        c.execute("SELECT gold_after FROM gem_data WHERE email = ? ORDER BY update_time DESC LIMIT 1", (email,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]  # 返回上次的当前余额作为这次的历史余额
        return "0"  # 如果是第一次登录，返回0
    except Exception as e:
        print(f"获取历史金币数据时出错：{e}")
        return "0"

def rubii_login(email="1176171890@qq.com", password="ouhao1992"):
    # === 配置 Chrome 选项 ===
    chrome_options = Options()
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 规避检测
    chrome_options.add_argument('--start-maximized')  # 最大化窗口
    chrome_options.add_argument("--incognito")  # 无痕模式

    # === 使用 undetected_chromedriver 防止检测 ===
    service = Service(ChromeDriverManager().install())  # 自动下载适合的 chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # === 打开网站 ===
        print(f"正在打开网站，准备登录账号：{email}")
        driver.get("https://rubii.ai/zh/mine")

        # 获取该账号的历史金币数据（上次的当前余额）
        gold_before = get_history_gold(email)
        print(f"账号 {email} 的历史金币：{gold_before}")

        # === 输入用户名 ===
        username_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='请输入您的邮箱']"))
        )
        username_input.clear()
        username_input.send_keys(email)
        print("输入了用户名")

        # === 处理 iframe（如果有）===
        password_input = None
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"找到 {len(iframes)} 个 iframe，检查是否包含密码输入框...")
        for iframe in iframes:
            driver.switch_to.frame(iframe)
            try:
                password_input = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='请输入密码']"))
                )
                print(f"在 iframe {iframe.get_attribute('name') or iframe.get_attribute('id')} 中找到了密码输入框")
                break
            except:
                driver.switch_to.default_content()  # 没找到密码框，切回主页面
        if not password_input:
            password_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='请输入密码']"))
            )
            print("在主页面找到了密码输入框")

        # === 输入密码（多方案保证输入成功） ===
        try:
            password_input.click()
            password_input.send_keys(password)
            print("方案 1 成功：直接 send_keys()")

            # 检查是否真的输入了密码
            if password_input.get_attribute("value") == "":
                raise Exception("send_keys() 输入失败，尝试其他方法")
        except:
            print("方案 1 失败，尝试其他方法")

            # 方案 2：JavaScript 直接赋值
            try:
                driver.execute_script("arguments[0].value = arguments[1];", password_input, password)
                print("方案 2 成功：使用 JavaScript 赋值")
            except:
                print("方案 2 失败，尝试方案 3")

                # 方案 3：用 ActionChains 模拟输入
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(password_input).click().send_keys(password).perform()
                    print("方案 3 成功：使用 ActionChains 模拟输入")
                except:
                    print("方案 3 失败，无法输入密码")

        # === 模拟回车键登录 ===
        password_input.send_keys(Keys.ENTER)
        print("按下回车键尝试登录")

        # === 等待登录完成 ===
        time.sleep(5)
        print("已尝试登录")

        # 抓取登录后的金币数据
        try:
            # 等待金币元素出现
            gold_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//strong[contains(@class, 'text-2xl') and contains(@class, 'font-normal')]"))
            )
            gold_after = gold_element.text
            print(f"抓取后金币：{gold_after}")

            # 不再需要保存到 SQLite 数据库
            # 直接返回数据
            return {
                "name": email,
                "count": gold_before,
                "price": gold_after
            }

        except Exception as e:
            print(f"抓取后金币数据失败: {e}")
            return {
                "name": email,
                "count": gold_before,
                "price": gold_before
            }

    except Exception as e:
        print(f"发生错误: {e}")
        return {
            "name": email,
            "count": gold_before,
            "price": gold_before
        }

    finally:
        driver.quit()