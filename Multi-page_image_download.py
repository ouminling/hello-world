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
from concurrent.futures import ThreadPoolExecutor
import urllib3
import time
# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 准备多个网页的 URL 列表
urls = [
    "https://wnacg.com/photos-slide-aid-285705.html",
    "https://wnacg.com/photos-slide-aid-249842.html",
    "https://wnacg.com/photos-slide-aid-250840.html"
]
# D 盘 Download 文件夹路径
base_folder = r"D:\Download"
def create_driver():
    # 设置 Edge 浏览器选项
    edge_options = Options()
    edge_options.add_argument("--headless")  # 无头模式
    edge_options.add_argument("--ignore-certificate-errors")  # 忽略证书错误
    edge_options.add_argument("--disable-gpu")  # 禁用GPU加速
    edge_options.add_argument("--no-sandbox")  # 禁用沙盒模式
    edge_options.add_argument("--disable-dev-shm-usage")  # 禁用/dev/shm使用
    # 指定 Edge WebDriver 路径
    driver_path = r"C:\Users\oml\AppData\Local\edgedriver_win64\msedgedriver.exe"
    service = Service(driver_path)
    
    return webdriver.Edge(service=service, options=edge_options)
def download_images_from_url(url, index):
    print(f"\n正在处理第 {index} 个网页: {url}")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 创建新的浏览器实例
            driver = create_driver()
            
            print("步骤 1: 打开网页并等待图片加载完成")
            driver.get(url)
            # 增加页面加载等待时间
            time.sleep(5)  # 等待5秒让页面完全加载
            
            # 等待图片加载完成
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "img"))
            )
            
            html = driver.page_source
            print("成功获取 HTML 代码")
            driver.quit()
            break
            
        except Exception as e:
            print(f"尝试 {retry_count + 1}/{max_retries} 失败: {e}")
            retry_count += 1
            if driver:
                driver.quit()
            time.sleep(2)  # 等待2秒后重试
            
        if retry_count == max_retries:
            print(f"处理网页 {url} 失败，达到最大重试次数")
            return
    # 解析 HTML 并查找 <title> 标签
    soup = BeautifulSoup(html, 'lxml')
    title_tag = soup.find('title')
    if title_tag:
        folder_name = title_tag.get_text()
        # 处理文件夹名称，去除非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            folder_name = folder_name.replace(char, '_')
        # 为避免文件夹名称冲突，加入网页序号
        folder_name = f"{index}_{folder_name}"
    else:
        folder_name = f"{index}_downloaded_images"
        print("未找到 <title> 标签，使用默认文件夹名称。")
    # 完整的保存路径
    save_folder = os.path.join(base_folder, folder_name)
    print("\n步骤 2: 检查并创建保存图片的文件夹")
    os.makedirs(save_folder, exist_ok=True)
    print(f"文件夹 {save_folder} 已准备就绪")
    print("\n步骤 3: 解析 HTML 并查找所有图片标签")
    try:
        # 找到所有 img 标签
        img_tags = soup.find_all('img')
        print(f"共找到 {len(img_tags)} 个图片标签")
    except Exception as e:
        print(f"解析 HTML 时出错: {e}")
        return
    print("\n步骤 4: 遍历图片标签并下载图片")
    for img_index, img in enumerate(img_tags):
        print(f"\n正在处理第 {img_index + 1} 个图片标签")
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
                file_name = os.path.join(save_folder, f'image_{img_index}.{file_ext}')
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
                # 设置超时时间，禁用SSL验证
                response = requests.get(img_url, stream=True, timeout=30, verify=False)
                response.raise_for_status()
                # 获取图片扩展名
                parsed_url = urlparse(img_url)
                file_ext = os.path.splitext(parsed_url.path)[1].lstrip('.') or 'jpg'
                # 过滤文件名中的非法字符
                safe_filename = ''.join(c if c.isalnum() or c in ('.', '_') else '_' for c in os.path.basename(parsed_url.path))
                file_name = os.path.join(save_folder, f'image_{img_index}_{safe_filename}')
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"成功保存图片到: {file_name}")
            except requests.RequestException as e:
                print(f"下载图片时出错: {e}")
if __name__ == "__main__":
    # 使用线程池进行多线程下载
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for index, url in enumerate(urls, start=1):
            future = executor.submit(download_images_from_url, url, index)
            futures.append(future)
        # 等待所有任务完成
        for future in futures:
            future.result()