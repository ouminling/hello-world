import os
import requests
from bs4 import BeautifulSoup

# 实际目标网页URL
url = 'https://wnacg.com/photos-slide-aid-285705.html'

# 模拟浏览器请求头（关键参数）
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://wnacg.com/'
}

try:
    # 获取网页内容
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 如果状态码非200会抛出异常
    
    # 解析HTML结构
    soup = BeautifulSoup(response.text, 'lxml')  # 使用lxml解析器更快
    img_list_div = soup.find('div', id='img_list')
    
    if not img_list_div:
        raise ValueError("页面结构已变化，未找到图片容器 div#img_list")

    # 提取所有图片标签
    img_tags = img_list_div.find_all('img')
    print(f"共发现 {len(img_tags)} 张待下载图片")

    # 创建保存目录（自动处理路径问题）
    save_dir = os.path.join(os.getcwd(), 'downloaded_images')
    os.makedirs(save_dir, exist_ok=True)
    print(f"图片将保存至：{os.path.abspath(save_dir)}")

    # 下载所有图片
    for idx, img in enumerate(img_tags, 1):
        try:
            img_url = img['src'].strip()
            
            # 处理协议相对URL
            if img_url.startswith('//'):
                img_url = f'https:{img_url}'
            elif img_url.startswith('/'):
                img_url = f'https://wnacg.com{img_url}'
                
            print(f"\n正在下载第 {idx}/{len(img_tags)} 张：{img_url}")
            
            # 下载图片（携带Referer反反爬）
            img_response = requests.get(img_url, headers={'Referer': url}, stream=True, timeout=15)
            img_response.raise_for_status()
            
            # 自动从URL获取文件扩展名
            ext = img_url.split('.')[-1].split('?')[0].lower()
            valid_exts = ['jpg', 'jpeg', 'png', 'webp', 'gif']
            ext = ext if ext in valid_exts else 'jpg'  # 默认jpg
            
            # 保存文件
            filename = os.path.join(save_dir, f"{idx:03d}.{ext}")
            with open(filename, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            print(f"√ 已保存为：{filename}")
            
        except Exception as img_error:
            print(f"× 第 {idx} 张下载失败：{str(img_error)}")
            continue

    print("\n全部下载完成！请检查 downloaded_images 文件夹")

except Exception as main_error:
    print(f"程序运行出错：{str(main_error)}")
    print("可能原因：")
    print("1. 网页需要登录（当前代码未处理登录）")
    print("2. 网站反爬机制触发（尝试更换代理或降低请求频率）")
    print("3. 目标网页结构已变更")