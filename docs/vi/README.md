<div align="center">

# 👻 Kiro Gateway

**Cổng proxy cho Kiro API (AWS CodeWhisperer)**

[🇬🇧 English](../../README.md) • [🇷🇺 Русский](../ru/README.md) • [🇨🇳 中文](../zh/README.md) • [🇪🇸 Español](../es/README.md) • [🇮🇩 Indonesia](../id/README.md) • [🇧🇷 Português](../pt/README.md) • [🇯🇵 日本語](../ja/README.md) • [🇹🇷 Türkçe](../tr/README.md) • [🇰🇷 한국어](../ko/README.md)

Được tạo với ❤️ bởi [@Jwadow](https://github.com/jwadow)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Sponsor](https://img.shields.io/badge/💖_Sponsor-Hỗ_trợ_Phát_triển-ff69b4)](#-hỗ-trợ-dự-án)

*Sử dụng các mô hình Claude thông qua bất kỳ công cụ nào tương thích với OpenAI hoặc Anthropic*

[Mô hình](#-các-mô-hình-được-hỗ-trợ) • [Tính năng](#-tính-năng) • [Bắt đầu nhanh](#-bắt-đầu-nhanh) • [Cấu hình](#%EF%B8%8F-cấu-hình) • [💖 Hỗ trợ](#-hỗ-trợ-dự-án)

</div>

---

## 🤖 Các Mô hình Được Hỗ trợ

🧠 **Claude Opus 4.5** — Mô hình mạnh nhất. Tốt nhất cho suy luận phức tạp, phân tích sâu và các nhiệm vụ nghiên cứu.

🚀 **Claude Sonnet 4.5** — Hiệu suất cân bằng. Tuyệt vời cho lập trình, viết lách và các nhiệm vụ đa năng.

⚡ **Claude Haiku 4.5** — Nhanh như chớp. Hoàn hảo cho phản hồi nhanh, nhiệm vụ đơn giản và trò chuyện.

📦 **Claude Sonnet 4** — Thế hệ trước. Vẫn mạnh mẽ và đáng tin cậy cho hầu hết các trường hợp sử dụng.

📦 **Claude 3.7 Sonnet** — Mô hình cũ. Có sẵn để tương thích ngược.

> 💡 **Phân giải Mô hình Thông minh:** Sử dụng bất kỳ định dạng tên mô hình nào — `claude-sonnet-4-5`, `claude-sonnet-4.5`, hoặc thậm chí tên có phiên bản như `claude-sonnet-4-5-20250929`. Cổng sẽ tự động chuẩn hóa.

---

## ✨ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 🔌 **API tương thích OpenAI** | Hoạt động với bất kỳ công cụ nào tương thích với OpenAI |
| 🔌 **API tương thích Anthropic** | Endpoint gốc `/v1/messages` |
| 🧠 **Tư duy Mở rộng** | Suy luận là độc quyền của dự án chúng tôi |
| 👁️ **Hỗ trợ Hình ảnh** | Gửi hình ảnh đến mô hình |
| 🛠️ **Gọi Công cụ** | Hỗ trợ gọi hàm |
| 💬 **Lịch sử tin nhắn đầy đủ** | Truyền ngữ cảnh cuộc trò chuyện hoàn chỉnh |
| 📡 **Streaming** | Hỗ trợ streaming SSE đầy đủ |
| 🔄 **Logic Thử lại** | Tự động thử lại khi có lỗi (403, 429, 5xx) |
| 📋 **Danh sách mô hình mở rộng** | Bao gồm các mô hình có phiên bản |
| 🔐 **Quản lý token thông minh** | Tự động làm mới trước khi hết hạn |

---

## 🚀 Bắt đầu Nhanh

### Yêu cầu

- Python 3.10+
- Một trong những điều sau:
  - [Kiro IDE](https://kiro.dev/) với tài khoản đã đăng nhập, HOẶC
  - [Kiro CLI](https://kiro.dev/cli/) với AWS SSO (Builder ID)

### Cài đặt

```bash
# Clone repository (yêu cầu Git)
git clone https://github.com/Jwadow/kiro-gateway.git
cd kiro-gateway

# Hoặc tải ZIP: Code → Download ZIP → giải nén → mở thư mục kiro-gateway

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình (xem phần Cấu hình)
cp .env.example .env
# Sao chép và chỉnh sửa .env với thông tin xác thực của bạn

# Khởi động server
python main.py

# Hoặc với cổng tùy chỉnh (nếu 8000 đang bận)
python main.py --port 9000
```

Server sẽ có sẵn tại `http://localhost:8000`

---

## ⚙️ Cấu hình

### Tùy chọn 1: File JSON Thông tin Xác thực

Chỉ định đường dẫn đến file thông tin xác thực:

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"

# Mật khẩu để bảo vệ server proxy CỦA BẠN (tạo bất kỳ chuỗi an toàn nào)
# Bạn sẽ sử dụng nó như api_key khi kết nối đến gateway của bạn
PROXY_API_KEY="my-super-secret-password-123"
```

<details>
<summary>📄 Định dạng file JSON</summary>

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

### Tùy chọn 2: Biến Môi trường (file .env)

Tạo file `.env` ở thư mục gốc của dự án:

```env
# Bắt buộc
REFRESH_TOKEN="kiro_refresh_token_của_bạn"

# Mật khẩu để bảo vệ server proxy CỦA BẠN (tạo bất kỳ chuỗi an toàn nào)
PROXY_API_KEY="my-super-secret-password-123"

# Tùy chọn
PROFILE_ARN="arn:aws:codewhisperer:us-east-1:..."
KIRO_REGION="us-east-1"
```

### Tùy chọn 3: Thông tin Xác thực AWS SSO (kiro-cli)

Nếu bạn sử dụng `kiro-cli` với AWS IAM Identity Center (SSO), cổng sẽ tự động phát hiện và sử dụng xác thực AWS SSO OIDC.

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/your-sso-cache-file.json"

# Mật khẩu để bảo vệ server proxy CỦA BẠN
PROXY_API_KEY="my-super-secret-password-123"

# Lưu ý: PROFILE_ARN KHÔNG cần thiết cho người dùng AWS SSO OIDC (Builder ID)
# Cổng sẽ hoạt động mà không cần nó
```

<details>
<summary>📄 Định dạng file JSON AWS SSO</summary>

Các file thông tin xác thực AWS SSO (từ `~/.aws/sso/cache/`) chứa:

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

**Lưu ý:** Người dùng AWS SSO OIDC (Builder ID) KHÔNG cần `profileArn`. Cổng sẽ hoạt động mà không cần nó (nếu được chỉ định, nó sẽ bị bỏ qua).

</details>

<details>
<summary>🔍 Cách hoạt động</summary>

Cổng tự động phát hiện loại xác thực dựa trên file thông tin xác thực:

- **Kiro Desktop Auth** (mặc định): Được sử dụng khi `clientId` và `clientSecret` KHÔNG có
  - Endpoint: `https://prod.{region}.auth.desktop.kiro.dev/refreshToken`
  
- **AWS SSO OIDC**: Được sử dụng khi `clientId` và `clientSecret` có
  - Endpoint: `https://oidc.{region}.amazonaws.com/token`

Không cần cấu hình bổ sung — chỉ cần trỏ đến file thông tin xác thực của bạn!

</details>

### Tùy chọn 4: Cơ sở dữ liệu SQLite kiro-cli

Nếu bạn sử dụng `kiro-cli` và muốn sử dụng trực tiếp cơ sở dữ liệu SQLite của nó:

```env
KIRO_CLI_DB_FILE="~/.local/share/kiro-cli/data.sqlite3"

# Mật khẩu để bảo vệ server proxy CỦA BẠN
PROXY_API_KEY="my-super-secret-password-123"

# Lưu ý: PROFILE_ARN KHÔNG cần thiết cho người dùng AWS SSO OIDC (Builder ID)
# Cổng sẽ hoạt động mà không cần nó
```

<details>
<summary>📄 Vị trí cơ sở dữ liệu</summary>

| Công cụ CLI | Đường dẫn Cơ sở dữ liệu |
|-------------|-------------------------|
| kiro-cli | `~/.local/share/kiro-cli/data.sqlite3` |
| amazon-q-developer-cli | `~/.local/share/amazon-q/data.sqlite3` |

Cổng đọc thông tin xác thực từ bảng `auth_kv` lưu trữ:
- `kirocli:odic:token` hoặc `codewhisperer:odic:token` — access token, refresh token, thời gian hết hạn
- `kirocli:odic:device-registration` hoặc `codewhisperer:odic:device-registration` — client ID và secret

Cả hai định dạng khóa đều được hỗ trợ để tương thích với các phiên bản kiro-cli khác nhau.

</details>

### Lấy Thông tin Xác thực

**Cho người dùng Kiro IDE:**
- Đăng nhập vào Kiro IDE và sử dụng Tùy chọn 1 ở trên (file JSON thông tin xác thực)
- File thông tin xác thực được tạo tự động sau khi đăng nhập

**Cho người dùng Kiro CLI:**
- Đăng nhập với `kiro-cli login` và sử dụng Tùy chọn 3 hoặc Tùy chọn 4 ở trên
- Không cần trích xuất token thủ công!

<details>
<summary>🔧 Nâng cao: Trích xuất token thủ công</summary>

Nếu bạn cần trích xuất refresh token thủ công (ví dụ: để debug), bạn có thể chặn traffic Kiro IDE:
- Tìm các request đến: `prod.us-east-1.auth.desktop.kiro.dev/refreshToken`

</details>

---

## 📡 Tham chiếu API

### Endpoints

| Endpoint | Phương thức | Mô tả |
|----------|-------------|-------|
| `/` | GET | Kiểm tra sức khỏe |
| `/health` | GET | Kiểm tra sức khỏe chi tiết |
| `/v1/models` | GET | Danh sách các mô hình có sẵn |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API |
| `/v1/messages` | POST | Anthropic Messages API |

---

## 💡 Ví dụ Sử dụng

### OpenAI API

<details>
<summary>🔹 Request cURL Đơn giản</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "Xin chào!"}],
    "stream": true
  }'
```

> **Lưu ý:** Thay thế `my-super-secret-password-123` bằng `PROXY_API_KEY` bạn đã đặt trong file `.env`.

</details>

<details>
<summary>🔹 Request với Streaming</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "system", "content": "Bạn là một trợ lý hữu ích."},
      {"role": "user", "content": "2+2 bằng bao nhiêu?"}
    ],
    "stream": true
  }'
```

</details>

<details>
<summary>🛠️ Với Gọi Công cụ</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "Thời tiết ở London như thế nào?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Lấy thời tiết cho một địa điểm",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "Tên thành phố"}
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
    api_key="my-super-secret-password-123"  # PROXY_API_KEY của bạn từ .env
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "system", "content": "Bạn là một trợ lý hữu ích."},
        {"role": "user", "content": "Xin chào!"}
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
    api_key="my-super-secret-password-123",  # PROXY_API_KEY của bạn từ .env
    model="claude-sonnet-4-5"
)

response = llm.invoke("Xin chào, bạn khỏe không?")
print(response.content)
```

</details>

### Anthropic API

<details>
<summary>🔹 Request cURL Đơn giản</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Xin chào!"}]
  }'
```

> **Lưu ý:** Anthropic API sử dụng header `x-api-key` thay vì `Authorization: Bearer`. Cả hai đều được hỗ trợ.

</details>

<details>
<summary>🔹 Với System Prompt</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "system": "Bạn là một trợ lý hữu ích.",
    "messages": [{"role": "user", "content": "Xin chào!"}]
  }'
```

> **Lưu ý:** Trong Anthropic API, `system` là một trường riêng biệt, không phải tin nhắn.

</details>

<details>
<summary>📡 Streaming</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "stream": true,
    "messages": [{"role": "user", "content": "Xin chào!"}]
  }'
```

</details>

<details>
<summary>🐍 Python Anthropic SDK</summary>

```python
import anthropic

client = anthropic.Anthropic(
    api_key="my-super-secret-password-123",  # PROXY_API_KEY của bạn từ .env
    base_url="http://localhost:8000"
)

# Không streaming
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Xin chào!"}]
)
print(response.content[0].text)

# Với streaming
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Xin chào!"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

</details>

---

## 🔧 Gỡ lỗi

Logging gỡ lỗi **bị tắt theo mặc định**. ể bật, thêm vào `.env` của bạn:

```env
# Chế độ logging gỡ lỗi:
# - off: tắt (mặc định)
# - errors: lưu log chỉ cho các request thất bại (4xx, 5xx) - khuyến nghị để khắc phục sự cố
# - all: lưu log cho mọi request (ghi đè mỗi request)
DEBUG_MODE=errors
```

### Chế độ Gỡ lỗi

| Chế độ | Mô tả | Trường hợp Sử dụng |
|--------|-------|-------------------|
| `off` | Tắt (mặc định) | Production |
| `errors` | Lưu log chỉ cho các request thất bại (4xx, 5xx) | **Khuyến nghị để khắc phục sự cố** |
| `all` | Lưu log cho mọi request | Phát triển/gỡ lỗi |

### File Gỡ lỗi

Khi được bật, các request được ghi vào thư mục `debug_logs/`:

| File | Mô tả |
|------|-------|
| `request_body.json` | Request đến từ client (định dạng OpenAI) |
| `kiro_request_body.json` | Request được gửi đến Kiro API |
| `response_stream_raw.txt` | Stream thô từ Kiro |
| `response_stream_modified.txt` | Stream đã chuyển đổi (định dạng OpenAI) |
| `app_logs.txt` | Log ứng dụng cho request |
| `error_info.json` | Chi tiết lỗi (chỉ khi có lỗi) |

---

## 📜 Giấy phép

Dự án này được cấp phép theo **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Điều này có nghĩa là:
- ✅ Bạn có thể sử dụng, sửa đổi và phân phối phần mềm này
- ✅ Bạn có thể sử dụng nó cho mục đích thương mại
- ⚠️ **Bạn phải công khai mã nguồn** khi bạn phân phối phần mềm
- ⚠️ **Sử dụng qua mạng là phân phối** — nếu bạn chạy phiên bản đã sửa đổi trên server và cho phép người khác tương tác với nó, bạn phải cung cấp mã nguồn cho họ
- ⚠️ Các sửa đổi phải được phát hành theo cùng giấy phép

Xem file [LICENSE](../../LICENSE) để biết toàn văn giấy phép.

### Tại sao AGPL-3.0?

AGPL-3.0 đảm bảo rằng các cải tiến cho phần mềm này mang lại lợi ích cho toàn bộ cộng đồng. Nếu bạn sửa đổi gateway này và triển khai nó như một dịch vụ, bạn phải chia sẻ các cải tiến của mình với người dùng.

### Thỏa thuận Giấy phép Người đóng góp (CLA)

Bằng cách gửi đóng góp cho dự án này, bạn đồng ý với các điều khoản của [Thỏa thuận Giấy phép Người đóng góp (CLA)](../../CLA.md) của chúng tôi. Điều này đảm bảo rằng:
- Bạn có quyền gửi đóng góp
- Bạn cấp cho người bảo trì quyền sử dụng và cấp phép lại đóng góp của bạn
- Dự án vẫn được bảo vệ về mặt pháp lý

---

## 💖 Hỗ trợ Dự án

<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Smiling%20Face%20with%20Hearts.png" alt="Love" width="80" />

**Nếu dự án này đã tiết kiệm thời gian hoặc tiền bạc cho bạn, hãy cân nhắc hỗ trợ nó!**

Mọi đóng góp đều giúp duy trì và phát triển dự án này

<br>

### 🤑 Quyên góp

[**☕ Quyên góp Một lần**](https://app.lava.top/jwadow?tabId=donate) &nbsp;•&nbsp; [**💎 Hỗ trợ Hàng tháng**](https://app.lava.top/jwadow?tabId=subscriptions)

<br>

### 🪙 Hoặc gửi crypto

| Tiền tệ | Mạng | Địa chỉ |
|:-------:|:----:|:--------|
| **USDT** | TRC20 | `TSVtgRc9pkC1UgcbVeijBHjFmpkYHDRu26` |
| **BTC** | Bitcoin | `12GZqxqpcBsqJ4Vf1YreLqwoMGvzBPgJq6` |
| **ETH** | Ethereum | `0xc86eab3bba3bbaf4eb5b5fff8586f1460f1fd395` |
| **SOL** | Solana | `9amykF7KibZmdaw66a1oqYJyi75fRqgdsqnG66AK3jvh` |
| **TON** | TON | `UQBVh8T1H3GI7gd7b-_PPNnxHYYxptrcCVf3qQk5v41h3QTM` |

</div>

---

## ⚠️ Tuyên bố Miễn trừ

Dự án này không liên kết với, được chứng thực bởi, hoặc được tài trợ bởi Amazon Web Services (AWS), Anthropic, hoặc Kiro IDE. Sử dụng theo rủi ro của riêng bạn và tuân thủ các điều khoản dịch vụ của các API cơ bản.

---

<div align="center">

**[⬆ Quay lại Đầu trang](#-kiro-gateway)**

</div>
