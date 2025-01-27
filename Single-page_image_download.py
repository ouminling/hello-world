import base64
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 网页 URL
url = "https://wnacg.com/photos-slide-aid-285705.html"

# 设置 Edge 浏览器选项
edge_options = Options()
edge_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口

# 指定 Edge WebDriver 路径，使用原始字符串
driver_path = r"C:\Users\oml\AppData\Local\edgedriver_win64\msedgedriver.exe"
service = Service(driver_path)

# 创建 Edge 浏览器实例
driver = webdriver.Edge(service=service, options=edge_options)

print("步骤 1: 打开网页并等待图片加载完成")
try:
    driver.get(url)
    # 等待图片加载完成，可以根据实际情况调整等待时间和定位元素
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "img"))
    )
    html = driver.page_source
    print("成功获取 HTML 代码")
except Exception as e:
    print(f"获取 HTML 代码时出错: {e}")
    driver.quit()
    exit(1)

# 关闭浏览器
driver.quit()

# 解析 HTML 并查找 <title> 标签
soup = BeautifulSoup(html, 'lxml')
title_tag = soup.find('title')
if title_tag:
    folder_name = title_tag.get_text()
    # 处理文件夹名称，去除非法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        folder_name = folder_name.replace(char, '_')
else:
    folder_name = 'downloaded_images'
    print("未找到 <title> 标签，使用默认文件夹名称。")

# D 盘 Download 文件夹路径
base_folder = r"D:\Download"
# 完整的保存路径
save_folder = os.path.join(base_folder, folder_name)

print("\n步骤 2: 检查并创建保存图片的文件夹")
# 检查 D 盘 download 文件夹是否存在，不存在则创建
if not os.path.exists(base_folder):
    try:
        os.makedirs(base_folder)
        print(f"成功创建 D 盘 Download 文件夹: {base_folder}")
    except OSError as e:
        print(f"创建 D 盘 Download 文件夹时出错: {e}")
        # 如果文件夹创建失败，后续操作无法进行，退出程序
        exit(1)

# 检查最终保存图片的文件夹是否存在，不存在则创建
if not os.path.exists(save_folder):
    try:
        os.makedirs(save_folder)
        print(f"成功创建文件夹: {save_folder}")
    except OSError as e:
        print(f"创建文件夹 {save_folder} 时出错: {e}")
        # 如果文件夹创建失败，后续操作无法进行，退出程序
        exit(1)
else:
    print(f"文件夹 {save_folder} 已存在，无需创建")

print("\n步骤 3: 解析 HTML 并查找所有图片标签")
try:
    # 找到所有 img 标签
    img_tags = soup.find_all('img')
    print(f"共找到 {len(img_tags)} 个图片标签")
except Exception as e:
    print(f"解析 HTML 时出错: {e}")
    exit(1)

print("\n步骤 4: 遍历图片标签并下载图片")
for index, img in enumerate(img_tags):
    print(f"\n正在处理第 {index + 1} 个图片标签")
    img_url = img.get('src')
    if not img_url:
        print("未找到图片的 src 属性，跳过该图片")
        continue
    print(f"获取到的图片 URL: {img_url}")

    if img_url.startswith('data:image'):
        print("检测到 Base64 编码的图片，开始处理")
        try:
            # 提取 Base64 数据
            base64_data = img_url.split(',')[1]
            # 解码 Base64 数据
            img_data = base64.b64decode(base64_data)
            file_ext = img_url.split(';')[0].split('/')[1]
            file_name = os.path.join(save_folder, f'image_{index}.{file_ext}')
            with open(file_name, 'wb') as f:
                f.write(img_data)
            print(f"成功保存 Base64 编码的图片到: {file_name}")
        except Exception as e:
            print(f"保存 Base64 编码的图片时出错: {e}")
    else:
        print("检测到普通图片 URL，开始处理")
        # 处理相对 URL
        img_url = urljoin(url, img_url)
        print(f"将相对 URL 转换为绝对 URL: {img_url}")
        try:
            print("开始下载图片...")
            response = requests.get(img_url, stream=True)
            response.raise_for_status()
            # 获取图片扩展名
            parsed_url = urlparse(img_url)
            file_ext = os.path.splitext(parsed_url.path)[1].lstrip('.') or 'jpg'
            # 过滤文件名中的非法字符
            safe_filename = ''.join(c if c.isalnum() or c in ('.', '_') else '_' for c in os.path.basename(parsed_url.path))
            file_name = os.path.join(save_folder, f'image_{index}_{safe_filename}')
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"成功保存图片到: {file_name}")
        except requests.RequestException as e:
            print(f"下载图片时出错: {e}")