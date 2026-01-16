<div align="center">

# 👻 Kiro Gateway

**Kiro API (AWS CodeWhisperer) 代理网关**

[🇬🇧 English](../../README.md) • [🇷🇺 Русский](../ru/README.md) • [🇪🇸 Español](../es/README.md) • [🇮🇩 Indonesia](../id/README.md) • [🇧🇷 Português](../pt/README.md) • [🇯🇵 日本語](../ja/README.md) • [🇻🇳 Tiếng Việt](../vi/README.md) • [🇹🇷 Türkçe](../tr/README.md) • [🇰🇷 한국어](../ko/README.md)

由 [@Jwadow](https://github.com/jwadow) 用 ❤️ 制作

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Sponsor](https://img.shields.io/badge/💖_Sponsor-支持开发-ff69b4)](#-支持项目)

*通过任何兼容 OpenAI 或 Anthropic 的工具使用 Claude 模型*

[模型](#-支持的模型) • [功能](#-功能特性) • [快速开始](#-快速开始) • [配置](#%EF%B8%8F-配置) • [💖 支持](#-支持项目)

</div>

---

## 🤖 支持的模型

🧠 **Claude Opus 4.5** — 最强大的模型。最适合复杂推理、深度分析和研究任务。

🚀 **Claude Sonnet 4.5** — 性能均衡。非常适合编程、写作和通用任务。

⚡ **Claude Haiku 4.5** — 闪电般快速。非常适合快速响应、简单任务和聊天。

📦 **Claude Sonnet 4** — 上一代模型。对于大多数用例仍然强大可靠。

📦 **Claude 3.7 Sonnet** — 旧版模型。为向后兼容而保留。

> 💡 **智能模型解析：** 使用任何模型名称格式 — `claude-sonnet-4-5`、`claude-sonnet-4.5`，甚至版本化名称如 `claude-sonnet-4-5-20250929`。网关会自动标准化它们。

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🔌 **兼容 OpenAI 的 API** | 与任何兼容 OpenAI 的工具配合使用 |
| 🔌 **兼容 Anthropic 的 API** | 原生 `/v1/messages` 端点 |
| 🧠 **扩展思维** | 推理功能是我们项目的独家特性 |
| 👁️ **视觉支持** | 向模型发送图像 |
| 🛠️ **工具调用** | 支持函数调用 |
| 💬 **完整消息历史** | 传递完整的对话上下文 |
| 📡 **流式传输** | 完整的 SSE 流式传输支持 |
| 🔄 **重试逻辑** | 错误时自动重试（403、429、5xx） |
| 📋 **扩展模型列表** | 包括版本化模型 |
| 🔐 **智能令牌管理** | 到期前自动刷新 |

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- 以下之一：
  - 已登录账户的 [Kiro IDE](https://kiro.dev/)，或
  - 带有 AWS SSO (Builder ID) 的 [Kiro CLI](https://kiro.dev/cli/)

### 安装

```bash
# 克隆仓库（需要 Git）
git clone https://github.com/Jwadow/kiro-gateway.git
cd kiro-gateway

# 或下载 ZIP：Code → Download ZIP → 解压 → 打开 kiro-gateway 文件夹

# 安装依赖
pip install -r requirements.txt

# 配置（参见配置部分）
cp .env.example .env
# 复制并编辑 .env 文件，填入您的凭据

# 启动服务器
python main.py

# 或使用自定义端口（如果 8000 被占用）
python main.py --port 9000
```

服务器将在 `http://localhost:8000` 上可用

---

## ⚙️ 配置

### 选项 1：JSON 凭据文件

指定凭据文件的路径：

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"

# 保护您的代理服务器的密码（设置任何安全字符串）
# 连接到您的网关时，您将使用它作为 api_key
PROXY_API_KEY="my-super-secret-password-123"
```

<details>
<summary>📄 JSON 文件格式</summary>

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresAt": "2025-01-12T23:00:00.000Z",
  "profileArn": "arn:aws:codewhisperer:us-east-1:...",
  "region": "us-east-1"
}
```

</details>

### 选项 2：环境变量（.env 文件）

在项目根目录创建 `.env` 文件：

```env
# 必需
REFRESH_TOKEN="您的_kiro_refresh_token"

# 保护您的代理服务器的密码（设置任何安全字符串）
PROXY_API_KEY="my-super-secret-password-123"

# 可选
PROFILE_ARN="arn:aws:codewhisperer:us-east-1:..."
KIRO_REGION="us-east-1"
```

### 选项 3：AWS SSO 凭据 (kiro-cli)

如果您使用带有 AWS IAM Identity Center (SSO) 的 `kiro-cli`，网关将自动检测并使用 AWS SSO OIDC 认证。

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/your-sso-cache-file.json"

# 保护您的代理服务器的密码
PROXY_API_KEY="my-super-secret-password-123"

# 注意：AWS SSO OIDC (Builder ID) 用户不需要 PROFILE_ARN
# 网关无需它即可工作
```

<details>
<summary>📄 AWS SSO JSON 文件格式</summary>

AWS SSO 凭据文件（来自 `~/.aws/sso/cache/`）包含：

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresAt": "2025-01-12T23:00:00.000Z",
  "region": "us-east-1",
  "clientId": "...",
  "clientSecret": "..."
}
```

**注意：** AWS SSO OIDC (Builder ID) 用户不需要 `profileArn`。网关无需它即可工作（如果指定，将被忽略）。

</details>

<details>
<summary>🔍 工作原理</summary>

网关根据凭据文件自动检测认证类型：

- **Kiro Desktop Auth**（默认）：当 `clientId` 和 `clientSecret` 不存在时使用
  - 端点：`https://prod.{region}.auth.desktop.kiro.dev/refreshToken`
  
- **AWS SSO OIDC**：当 `clientId` 和 `clientSecret` 存在时使用
  - 端点：`https://oidc.{region}.amazonaws.com/token`

无需额外配置 — 只需指向您的凭据文件！

</details>

### 选项 4：kiro-cli SQLite 数据库

如果您使用 `kiro-cli` 并希望直接使用其 SQLite 数据库：

```env
KIRO_CLI_DB_FILE="~/.local/share/kiro-cli/data.sqlite3"

# 保护您的代理服务器的密码
PROXY_API_KEY="my-super-secret-password-123"

# 注意：AWS SSO OIDC (Builder ID) 用户不需要 PROFILE_ARN
# 网关无需它即可工作
```

<details>
<summary>📄 数据库位置</summary>

| CLI 工具 | 数据库路径 |
|----------|-----------|
| kiro-cli | `~/.local/share/kiro-cli/data.sqlite3` |
| amazon-q-developer-cli | `~/.local/share/amazon-q/data.sqlite3` |

网关从 `auth_kv` 表读取凭据，该表存储：
- `kirocli:odic:token` 或 `codewhisperer:odic:token` — 访问令牌、刷新令牌、过期时间
- `kirocli:odic:device-registration` 或 `codewhisperer:odic:device-registration` — 客户端 ID 和密钥

两种键格式都支持，以兼容不同版本的 kiro-cli。

</details>

### 获取凭据

**Kiro IDE 用户：**
- 登录 Kiro IDE 并使用上面的选项 1（JSON 凭据文件）
- 凭据文件在登录后自动创建

**Kiro CLI 用户：**
- 使用 `kiro-cli login` 登录并使用上面的选项 3 或选项 4
- 无需手动提取令牌！

<details>
<summary>🔧 高级：手动提取令牌</summary>

如果您需要手动提取 refresh token（例如用于调试），您可以拦截 Kiro IDE 流量：
- 查找发往以下地址的请求：`prod.us-east-1.auth.desktop.kiro.dev/refreshToken`

</details>

---

## 📡 API 参考

### 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/health` | GET | 详细健康检查 |
| `/v1/models` | GET | 列出可用模型 |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API |
| `/v1/messages` | POST | Anthropic Messages API |

---

## 💡 使用示例

### OpenAI API

<details>
<summary>🔹 简单 cURL 请求</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "你好！"}],
    "stream": true
  }'
```

> **注意：** 将 `my-super-secret-password-123` 替换为您在 `.env` 文件中设置的 `PROXY_API_KEY`。

</details>

<details>
<summary>🔹 流式请求</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "system", "content": "你是一个有帮助的助手。"},
      {"role": "user", "content": "2+2 等于多少？"}
    ],
    "stream": true
  }'
```

</details>

<details>
<summary>🛠️ 带工具调用</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "伦敦的天气怎么样？"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取某个位置的天气",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "城市名称"}
          },
          "required": ["location"]
        }
      }
    }]
  }'
```

</details>

<details>
<summary>🐍 Python OpenAI SDK</summary>

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-super-secret-password-123"  # 您在 .env 中的 PROXY_API_KEY
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好！"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

</details>

<details>
<summary>🦜 LangChain</summary>

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-super-secret-password-123",  # 您在 .env 中的 PROXY_API_KEY
    model="claude-sonnet-4-5"
)

response = llm.invoke("你好，你好吗？")
print(response.content)
```

</details>

### Anthropic API

<details>
<summary>🔹 简单 cURL 请求</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好！"}]
  }'
```

> **注意：** Anthropic API 使用 `x-api-key` 头而不是 `Authorization: Bearer`。两者都支持。

</details>

<details>
<summary>🔹 带系统提示</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "system": "你是一个有帮助的助手。",
    "messages": [{"role": "user", "content": "你好！"}]
  }'
```

> **注意：** 在 Anthropic API 中，`system` 是一个单独的字段，而不是消息。

</details>

<details>
<summary>📡 流式传输</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "stream": true,
    "messages": [{"role": "user", "content": "你好！"}]
  }'
```

</details>

<details>
<summary>🐍 Python Anthropic SDK</summary>

```python
import anthropic

client = anthropic.Anthropic(
    api_key="my-super-secret-password-123",  # 您在 .env 中的 PROXY_API_KEY
    base_url="http://localhost:8000"
)

# 非流式
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}]
)
print(response.content[0].text)

# 流式
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

</details>

---

## 🔧 调试

调试日志**默认禁用**。要启用，请在您的 `.env` 中添加：

```env
# 调试日志模式：
# - off：禁用（默认）
# - errors：仅保存失败请求的日志（4xx、5xx）- 推荐用于故障排除
# - all：保存每个请求的日志（每次请求时覆盖）
DEBUG_MODE=errors
```

### 调试模式

| 模式 | 描述 | 使用场景 |
|------|------|----------|
| `off` | 禁用（默认） | 生产环境 |
| `errors` | 仅保存失败请求的日志（4xx、5xx） | **推荐用于故障排除** |
| `all` | 保存每个请求的日志 | 开发/调试 |

### 调试文件

启用后，请求将记录到 `debug_logs/` 文件夹：

| 文件 | 描述 |
|------|------|
| `request_body.json` | 来自客户端的传入请求（OpenAI 格式） |
| `kiro_request_body.json` | 发送到 Kiro API 的请求 |
| `response_stream_raw.txt` | 来自 Kiro 的原始流 |
| `response_stream_modified.txt` | 转换后的流（OpenAI 格式） |
| `app_logs.txt` | 请求的应用程序日志 |
| `error_info.json` | 错误详情（仅在出错时） |

---

## 📜 许可证

本项目采用 **GNU Affero 通用公共许可证 v3.0 (AGPL-3.0)** 许可。

这意味着：
- ✅ 您可以使用、修改和分发此软件
- ✅ 您可以将其用于商业目的
- ⚠️ **您必须公开源代码** 当您分发软件时
- ⚠️ **网络使用即为分发** — 如果您在服务器上运行修改版本并让他人与之交互，您必须向他们提供源代码
- ⚠️ 修改必须在相同许可证下发布

完整许可证文本请参见 [LICENSE](../../LICENSE) 文件。

### 为什么选择 AGPL-3.0？

AGPL-3.0 确保对此软件的改进惠及整个社区。如果您修改此网关并将其部署为服务，您必须与您的用户分享您的改进。

### 贡献者许可协议 (CLA)

通过向本项目提交贡献，您同意我们的[贡献者许可协议 (CLA)](../../CLA.md) 的条款。这确保：
- 您有权提交贡献
- 您授予维护者使用和重新许可您的贡献的权利
- 项目保持法律保护

---

## 💖 支持项目

<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Smiling%20Face%20with%20Hearts.png" alt="Love" width="80" />

**如果这个项目为您节省了时间或金钱，请考虑支持它！**

每一份贡献都有助于保持这个项目的活力和发展

<br>

### 🤑 捐赠

[**☕ 一次性捐赠**](https://app.lava.top/jwadow?tabId=donate) &nbsp;•&nbsp; [**💎 每月支持**](https://app.lava.top/jwadow?tabId=subscriptions)

<br>

### 🪙 或发送加密货币

| 货币 | 网络 | 地址 |
|:----:|:----:|:-----|
| **USDT** | TRC20 | `TSVtgRc9pkC1UgcbVeijBHjFmpkYHDRu26` |
| **BTC** | Bitcoin | `12GZqxqpcBsqJ4Vf1YreLqwoMGvzBPgJq6` |
| **ETH** | Ethereum | `0xc86eab3bba3bbaf4eb5b5fff8586f1460f1fd395` |
| **SOL** | Solana | `9amykF7KibZmdaw66a1oqYJyi75fRqgdsqnG66AK3jvh` |
| **TON** | TON | `UQBVh8T1H3GI7gd7b-_PPNnxHYYxptrcCVf3qQk5v41h3QTM` |

</div>

---

## ⚠️ 免责声明

本项目与 Amazon Web Services (AWS)、Anthropic 或 Kiro IDE 无关，未经其认可或赞助。使用风险自负，并遵守底层 API 的服务条款。

---

<div align="center">

**[⬆ 返回顶部](#-kiro-gateway)**

</div>
