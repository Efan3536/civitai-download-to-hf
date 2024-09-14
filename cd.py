import requests
import re
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import os
import subprocess
import sys

def get_civitai_model_info_by_url(model_url, api_key):
    """通过模型地址获取 Civitai 模型信息，并下载模型和图片。

    Args:
        model_url (str): Civitai 模型地址。
        api_key (str): Civitai API 密钥。

    Returns:
        dict: 包含模型信息的字典，如果模型不存在则返回 None.
    """

    # 使用正则表达式提取模型 ID 和版本 ID
    match = re.search(r"civitai\.com/models/(\d+)(?:\?modelVersionId=(\d+))?", model_url)
    if not match:
        print("无效的 Civitai 模型地址！")
        return None

    model_id = int(match.group(1))
    model_version_id = int(match.group(2)) if match.group(2) else None

    url = f"https://civitai.com/api/v1/models/{model_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        model_info = {
            "model_id": data["id"],
            "model_name": data["name"],
            "model_description": data["description"],  # 使用BeautifulSoup还原HTML格式
            "model_url": f"https://civitai.com/models/{data['id']}",
            "model_type": data["type"],
            "model_tags": data["tags"],
            "download_link": None,  # 初始化为 None，稍后更新
            "preview_image_url": None,  # 初始化为 None，稍后更新
            "model_version_id": None,
            "model_version_download_link": None,
            "model_version_image_url": None,
        }

        # 提取模型描述的HTML格式，使用BeautifulSoup
        soup = BeautifulSoup(model_info["model_description"], 'html.parser')
        model_info["model_description"] = soup.prettify()

        # 如果提供了 model_version_id，则提取特定版本的信息
        if model_version_id:
            for version in data["modelVersions"]:
                if version["id"] == model_version_id:
                    model_info["model_version_id"] = version["id"]
                    model_info["model_version_download_link"] = version["files"][0]["downloadUrl"]
                    model_info["model_version_image_url"] = version["images"][0]["url"]
                    break
        else:
            # 否则提取主版本的下载链接和预览图片链接
            model_info["download_link"] = data["modelVersions"][0]["files"][0]["downloadUrl"]
            model_info["preview_image_url"] = data["modelVersions"][0]["images"][0]["url"]

        return model_info

    else:
        print(f"请求失败: {response.status_code}")
        return None


def download_file(url, file_name=None, download_dir="."):  # 添加 download_dir 参数
    """下载文件，并显示进度条。

    Args:
        url (str): 文件 URL。
        file_name (str, optional): 保存的文件名。如果为 None，则使用默认文件名。
        download_dir (str, optional): 下载目录。默认为当前目录 (".")。
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # 获取 Civitai 提供的默认文件名
        default_file_name = get_file_name_from_response(response)
        file_name = file_name or default_file_name  # 如果未提供 file_name，则使用默认文件名

        # 构造完整的文件路径
        file_path = os.path.join(download_dir, file_name)

        # 创建下载目录（如果不存在）
        os.makedirs(download_dir, exist_ok=True)

        total_size = int(response.headers.get("content-length", 0))
        with open(file_path, "wb") as f:  # 使用 file_path 保存文件
            with tqdm(total=total_size, unit="B", unit_scale=True, desc=file_name) as pbar:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"已下载: {file_path}")
        return file_name  # 返回文件名

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {url} - {e}")


def get_file_name_from_response(response):
    """从响应头中获取文件名。

    Args:
        response: requests.Response 对象。

    Returns:
        str: 文件名，如果未找到则返回 'downloaded_file'.
    """
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        file_name_match = re.findall('filename="(.+)"', content_disposition)
        if file_name_match:
            return file_name_match[0]
    return 'downloaded_file' # 默认文件名


if __name__ == "__main__":
    # 设置默认值
    model_url = None
    download_dir = "."
    api_key = "4915cd655c09775d2320359f90fc774b"  # 将 API 密钥设置为默认值

    # 解析命令行参数
    if len(sys.argv) > 1:
        model_url = sys.argv[1]
    if len(sys.argv) > 2:
        download_dir = sys.argv[2]

    if not model_url:
        print("请提供 Civitai 模型地址。")
        sys.exit(1)

    # 调用函数获取模型信息
    model_info = get_civitai_model_info_by_url(model_url, api_key)

    if model_info:
        # 下载模型
        if model_info.get("download_link"):
            download_url = model_info["download_link"] + f"?token={api_key}"

            # 获取 Civitai 提供的默认文件名
            response = requests.get(download_url, headers={'Range': 'bytes=0-0'})  # 只请求第一个字节
            response.raise_for_status()
            default_file_name = get_file_name_from_response(response)

            model_file_path = os.path.join(download_dir, default_file_name)

            if os.path.exists(model_file_path):
                print(f"模型已存在，跳过下载: {model_file_path}")
                model_file_name = default_file_name  # 设置 model_file_name 为默认文件名
            else:
                model_file_name = download_file(download_url, download_dir=download_dir)

            # 使用模型文件名作为基础，构建 JSON 文件名和图片文件名
            file_name_base = model_file_name.rsplit(".", 1)[0]

            # 将数据保存到 JSON 文件
            json_file_path = os.path.join(download_dir, f"{file_name_base}.json")

            if os.path.exists(json_file_path):
                print(f"JSON 文件已存在，跳过下载: {json_file_path}")
            else:
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(model_info, f, ensure_ascii=False, indent=4)

        # 下载图片
        if model_info.get("preview_image_url"):
            image_file_path = os.path.join(download_dir, f"{file_name_base}.jpg")
            if os.path.exists(image_file_path):
                print(f"图片已存在，跳过下载: {image_file_path}")
            else:
                download_file(
                    model_info["preview_image_url"],
                    f"{file_name_base}.jpg",
                    download_dir=download_dir,
                )
