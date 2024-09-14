# 自用下载模型

## 使用方法

**方法一：**

```bash
python cd.py <模型主页地址> 

**方法二：**

```bash
python cd_plus <模型地址> <Hugging Face Token> <Civitai API Key> <Hugging Face 仓库 ID> <下载目录(可选)>
```

**参数说明:**

* **模型主页地址:**  模型在 Civitai 或 Hugging Face 上的页面地址.
* **模型地址:** 模型文件的直接下载地址.
* **Hugging Face Token:** 你的 Hugging Face 访问令牌.
* **Civitai API Key:** 你的 Civitai API 密钥.
* **Hugging Face 仓库 ID:** 你想要上传模型的 Hugging Face 仓库 ID.
* **下载目录(可选):**  指定模型下载的目标目录，默认为当前目录.


**示例:**

**方法一:** 从 Civitai 下载模型

```bash
python cd.py https://civitai.com/models/12345/example-model
```

**方法二:** 从指定地址下载模型并上传到 Hugging Face

```bash
python cd_plus https://example.com/model.ckpt your_hf_token your_civitai_api_key your_repo_id ./my_models
```

**注意:** 

* 确保你已经安装了所需的 Python 库.
* `cd_plus` 方法需要你拥有 Hugging Face 和 Civitai 的账户并获取相应的 API 密钥.
```

**其他信息:**

* [如何获取 Hugging Face Token](https://huggingface.co/settings/tokens)
* [如何获取 Civitai API Key](https://civitai.com/apikeys)

希望以上信息能够帮助你理解如何使用这个工具. 


```

**修改说明:**

1.  将使用方法分为了两种，并分别给出了代码示例.
2.  添加了参数说明，解释了每个参数的含义.
3.  添加了获取 Hugging Face Token 和 Civitai API Key 的链接.
4.  使用 Markdown 格式进行排版，使其更易于阅读.


请根据你的实际情况修改以上内容，例如添加更多使用方法、参数说明、示例等.
