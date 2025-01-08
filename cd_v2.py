import re
import requests
import os
import json
from urllib.parse import urlparse, parse_qs
from tqdm import tqdm
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import HfFolder

def extract_model_id(url):
    """从URL中提取模型ID"""
    match = re.search(r'/models/(\d+)', url)
    if match:
        return match.group(1)
    return None

def extract_version_id(url):
    """从URL中提取版本ID"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    version_id = query_params.get('modelVersionId', [None])[0]
    return version_id

def get_model_info(model_id, api_key=None):
    """获取模型信息"""
    api_url = f"https://civitai.com/api/v1/models/{model_id}"
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取模型信息失败: {response.status_code}")

def get_model_page_html(model_info, model_id):
    """生成模型页面HTML"""
    latest_version = model_info['modelVersions'][0]
    
    # 获取基本信息
    model_name = model_info['name']
    creator = model_info['creator']['username']
    creator_avatar = model_info['creator']['image']
    version_name = latest_version['name']
    base_model = latest_version['baseModel']
    download_url = latest_version['downloadUrl']
    
    # 构建HTML内容
    html_content = f"""
                <head>
                    <meta charset="UTF-8">
                    <link rel="stylesheet" type="text/css" href="/root/Cccc_emm/extensions/sd-civitai-browser-plus/style_html.css">
                </head>
                <div class="model-block">
                    <h2><a href="https://civitai.com/models/{model_id}" target="_blank" id="model_header">{model_name}</a></h2>
                    <h3 class="model-uploader">Uploaded by <a href="https://civitai.com/user/{creator}" target="_blank">{creator}</a>
                    <div class="avatar"><img src="{creator_avatar}"></div></h3>
                    <div class="civitai-version-info" style="display:flex; flex-wrap:wrap; justify-content:space-between;">
                        <dl id="info_block">
                            <dt>Version</dt>
                            <dd>{version_name}</dd>
                            <dt>Base Model</dt>
                            <dd>{base_model}</dd>
                            <dt>CivitAI Tags</dt>
                            <dd>
                                <div class="civitai-tags-container">
                                    {"".join(f'<span class="civitai-tag">{tag}</span>' for tag in model_info['tags'])}
                                </div>
                            </dd>
                            <dt>Download Link</dt>
                            <dd><a href="{download_url}" target="_blank">{download_url}</a></dd>
                        </dl>
                    </div>
                    <input type="checkbox" id="civitai-description" class="description-toggle-checkbox">
                    <div class="model-description">
                        <h2>Description</h2>
                        {model_info['description']}
                    </div>
                    <label for="civitai-description" class="description-toggle-label"></label>
                </div>
                <div align=center><div class="sampleimgs"><input type="radio" name="zoomRadio" id="resetZoom" class="zoom-radio" checked>
    """
    
    # 添加示例图片
    for i, image in enumerate(latest_version['images']):
        img_url = image['url']
        html_content += f"""
                    <div class="model-block" style="display:flex;align-items:flex-start;">
                    <div class="civitai-image-container">
                    <input type="radio" name="zoomRadio" id="zoomRadio{i}" class="zoom-radio">
                    <label for="zoomRadio{i}" class="zoom-img-container">
                    <img data-sampleimg="true" src="{img_url}">
                        </label>
                        <label for="resetZoom" class="zoom-overlay"></label>
                    
                            <div class="civitai_txt2img" style="margin-top:30px;margin-bottom:30px;">
                            <label onclick='sendImgUrl("{img_url}")' class="civitai-txt2img-btn" style="max-width:fit-content;cursor:pointer;">Send to txt2img</label>
                            </div></div>
                    </div>
        """
    
    html_content += "</div></div>"
    return html_content

def check_file_exists(filepath, expected_size=None):
    """检查文件是否存在且完整"""
    if not os.path.exists(filepath):
        return False
    
    if expected_size is not None:
        actual_size = os.path.getsize(filepath)
        if actual_size != expected_size:
            return False
    
    return True

def download_file(url, filename, api_key=None, expected_size=None):
    """下载文件并显示进度条"""
    # 检查文件是否已存在
    if check_file_exists(filename, expected_size):
        print(f"文件已存在,跳过下载: {filename}")
        return
    
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"下载 {os.path.basename(filename)}") as pbar:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    pbar.update(len(data))
        print(f"文件下载完成: {filename}")
    else:
        raise Exception(f"下载失败: {response.status_code}")

def create_model_json(model_info, model_id, version_id, base_filename):
    """创建模型信息JSON文件"""
    # 获取版本信息
    if version_id:
        version_info = next((v for v in model_info['modelVersions'] if str(v['id']) == version_id), model_info['modelVersions'][0])
    else:
        version_info = model_info['modelVersions'][0]
        version_id = str(version_info['id'])  # 获取最新版本的ID
    
    # 构建JSON数据
    json_data = {
        "model_id": int(model_id),
        "model_name": model_info['name'],
        "model_description": model_info.get('description', ''),
        "model_url": f"https://civitai.com/models/{model_id}",
        "model_type": model_info.get('type', 'Unknown'),
        "model_tags": model_info.get('tags', []),
        "download_link": version_info['downloadUrl'],
        "preview_image_url": version_info['images'][0]['url'] if version_info.get('images') else '',
        "model_version_id": version_id,
        "model_version_download_link": version_info['downloadUrl'],
        "model_version_image_url": version_info['images'][0]['url'] if version_info.get('images') else ''
    }
    
    # 保存JSON文件
    json_filename = f"{base_filename}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    return json_filename

def upload_to_huggingface(model_name, model_dir, repo_id, repo_type, hf_token):
    """将模型文件上传到 Hugging Face Hub"""
    # 设置 Hugging Face 访问令牌
    HfFolder.save_token(hf_token)

    # 初始化 Hugging Face API 客户端
    api = HfApi()

    # 获取目录中的所有文件
    all_files = os.listdir(model_dir)
    
    # 上传目录中的所有文件
    for filename in all_files:
        local_file_path = os.path.join(model_dir, filename)
        
        # 跳过目录
        if os.path.isdir(local_file_path):
            continue
            
        # 构建在仓库中的文件路径
        repo_file_path = f"{model_name}/{filename}"
        
        try:
            print(f"正在上传: {filename}")
            api.upload_file(
                path_or_fileobj=local_file_path,
                path_in_repo=repo_file_path,
                repo_id=repo_id,
                repo_type=repo_type,
            )
            print(f"文件 '{local_file_path}' 已成功上传到仓库 '{repo_id}' 的 '{repo_file_path}'")
        except Exception as e:
            print(f"上传文件 '{local_file_path}' 失败: {str(e)}")

def main(model_url, api_key=None, hf_token=None, repo_id=None):
    """主函数"""
    # 提取模型ID和版本ID
    model_id = extract_model_id(model_url)
    version_id = extract_version_id(model_url)
    
    if not model_id:
        raise Exception("无法从URL中提取模型ID")
        
    # 获取模型信息
    model_info = get_model_info(model_id, api_key)
    
    # 获取最新版本信息
    if version_id:
        # 如果指定了版本ID，找到对应版本
        version_info = next((v for v in model_info['modelVersions'] if str(v['id']) == version_id), None)
        if not version_info:
            raise Exception(f"找不到指定版本ID: {version_id}")
        latest_version = version_info
    else:
        latest_version = model_info['modelVersions'][0]
    
    # 获取主模型文件信息
    model_file = None
    
    # 1. 首先尝试查找primary为True的文件
    try:
        model_file = next((f for f in latest_version['files'] if f.get('primary', False)), None)
    except Exception:
        pass
        
    # 2. 如果没找到，尝试查找类型为Model的文件
    if not model_file:
        try:
            model_file = next((f for f in latest_version['files'] if f.get('type', '').lower() == 'model'), None)
        except Exception:
            pass
            
    # 3. 如果还是没找到，使用第一个文件
    if not model_file and latest_version['files']:
        model_file = latest_version['files'][0]
    
    if not model_file:
        raise Exception("无法找到模型文件")
        
    print(f"选择下载文件: {model_file['name']} ({model_file.get('type', 'Unknown Type')})")
    
    # 使用模型名称作为文件夹名（移除非法字符）
    model_name = re.sub(r'[<>:"/\\|?*]', '', model_info['name'])  # 移除Windows不允许的文件名字符
    model_dir = os.path.join(os.getcwd(), model_name)
    
    # 创建模型专属目录
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    # 下载模型文件
    model_download_url = model_file['downloadUrl']
    model_filename = model_file['name']
    model_path = os.path.join(model_dir, model_filename)
    expected_model_size = model_file['sizeKB'] * 1024  # 转换为字节
    print(f"开始下载模型文件...")
    download_file(model_download_url, model_path, api_key, expected_model_size)
    
    # 下载封面图片
    cover_image_url = latest_version['images'][0]['url']
    image_ext = os.path.splitext(cover_image_url)[1] or '.jpg'
    image_filename = f"{model_name}{image_ext}"  # 使用模型名称作为图片文件名
    image_path = os.path.join(model_dir, image_filename)
    print(f"开始下载封面图片...")
    download_file(cover_image_url, image_path, api_key)
    
    # 创建JSON信息文件
    json_path = os.path.join(model_dir, f"{model_name}.json")
    if not os.path.exists(json_path):
        print(f"创建JSON信息文件...")
        create_model_json(model_info, model_id, version_id, os.path.join(model_dir, model_name))
    else:
        print(f"JSON文件已存在,跳过创建: {json_path}")
    
    # 生成并保存HTML页面
    html_path = os.path.join(model_dir, f"{model_name}.html")
    if not os.path.exists(html_path):
        print(f"生成HTML页面...")
        html_content = get_model_page_html(model_info, model_id)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    else:
        print(f"HTML文件已存在,跳过生成: {html_path}")
    
    print(f"所有文件处理完成！保存在目录: {model_dir}")
    
    # 如果提供了 Hugging Face 相关参数，则上传到 Hugging Face
    if hf_token and repo_id:
        print("开始上传文件到 Hugging Face...")
        upload_to_huggingface(model_name, model_dir, repo_id, "model", hf_token)
        print("上传完成！")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("1. 仅下载模型:")
        print("   python download_civitai.py <模型URL>")
        print("2. 下载并上传到 Hugging Face:")
        print("   python download_civitai.py <模型URL> <HF_TOKEN> <REPO_ID>")
        print("示例:")
        print("   python download_civitai.py https://civitai.com/models/827184")
        sys.exit(1)
    
    # 设置默认的 Civitai API key
    api_key = "ffc12ea6282a24a0286ac40f700268cc"
    
    # 获取命令行参数
    model_url = sys.argv[1]
    hf_token = sys.argv[2] if len(sys.argv) > 2 else None
    repo_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        main(model_url, api_key, hf_token, repo_id)
    except Exception as e:
        print(f"发生错误: {str(e)}") 
