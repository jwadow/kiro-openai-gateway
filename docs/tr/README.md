<div align="center">

# 👻 Kiro Gateway

**Kiro API (AWS CodeWhisperer) için Proxy Gateway**

[🇬🇧 English](../../README.md) • [🇷🇺 Русский](../ru/README.md) • [🇨🇳 中文](../zh/README.md) • [🇪🇸 Español](../es/README.md) • [🇮🇩 Indonesia](../id/README.md) • [🇧🇷 Português](../pt/README.md) • [🇯🇵 日本語](../ja/README.md) • [🇻🇳 Tiếng Việt](../vi/README.md) • [🇰🇷 한국어](../ko/README.md)

[@Jwadow](https://github.com/jwadow) tarafından ❤️ ile yapıldı

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Sponsor](https://img.shields.io/badge/💖_Sponsor-Geliştirmeyi_Destekle-ff69b4)](#-projeyi-destekle)

*Claude modellerini OpenAI veya Anthropic uyumlu herhangi bir araçla kullanın*

[Modeller](#-desteklenen-modeller) • [Özellikler](#-özellikler) • [Hızlı Başlangıç](#-hızlı-başlangıç) • [Yapılandırma](#%EF%B8%8F-yapılandırma) • [💖 Destek](#-projeyi-destekle)

</div>

---

## 🤖 Desteklenen Modeller

🧠 **Claude Opus 4.5** — En güçlü model. Karmaşık akıl yürütme, derin analiz ve araştırma görevleri için en iyisi.

🚀 **Claude Sonnet 4.5** — Dengeli performans. Kodlama, yazma ve genel amaçlı görevler için harika.

⚡ **Claude Haiku 4.5** — Yıldırım hızında. Hızlı yanıtlar, basit görevler ve sohbet için mükemmel.

📦 **Claude Sonnet 4** — Önceki nesil. Çoğu kullanım durumu için hala güçlü ve güvenilir.

📦 **Claude 3.7 Sonnet** — Eski model. Geriye dönük uyumluluk için mevcut.

> 💡 **Akıllı Model Çözümleme:** Herhangi bir model adı formatı kullanın — `claude-sonnet-4-5`, `claude-sonnet-4.5`, hatta `claude-sonnet-4-5-20250929` gibi sürümlü isimler. Gateway otomatik olarak normalleştirir.

---

## ✨ Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🔌 **OpenAI uyumlu API** | OpenAI uyumlu herhangi bir araçla çalışır |
| 🔌 **Anthropic uyumlu API** | Yerel `/v1/messages` endpoint'i |
| 🧠 **Genişletilmiş Düşünme** | Akıl yürütme projemize özeldir |
| 👁️ **Görüntü Desteği** | Modele görüntü gönderin |
| 🛠️ **Araç Çağırma** | Fonksiyon çağırmayı destekler |
| 💬 **Tam mesaj geçmişi** | Tam konuşma bağlamını iletir |
| 📡 **Streaming** | Tam SSE streaming desteği |
| 🔄 **Yeniden Deneme Mantığı** | Hatalarda otomatik yeniden deneme (403, 429, 5xx) |
| 📋 **Genişletilmiş model listesi** | Sürümlü modeller dahil |
| 🔐 **Akıllı token yönetimi** | Süresi dolmadan önce otomatik yenileme |

---

## 🚀 Hızlı Başlangıç

### Ön Koşullar

- Python 3.10+
- Aşağıdakilerden biri:
  - Giriş yapılmış hesapla [Kiro IDE](https://kiro.dev/), VEYA
  - AWS SSO (Builder ID) ile [Kiro CLI](https://kiro.dev/cli/)

### Kurulum

```bash
# Depoyu klonlayın (Git gerektirir)
git clone https://github.com/Jwadow/kiro-gateway.git
cd kiro-gateway

# Veya ZIP indirin: Code → Download ZIP → çıkartın → kiro-gateway klasörünü açın

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Yapılandırın (Yapılandırma bölümüne bakın)
cp .env.example .env
# .env'yi kopyalayın ve kimlik bilgilerinizle düzenleyin

# Sunucuyu başlatın
python main.py

# Veya özel port ile (8000 meşgulse)
python main.py --port 9000
```

Sunucu `http://localhost:8000` adresinde kullanılabilir olacak

---

## ⚙️ Yapılandırma

### Seçenek 1: JSON Kimlik Bilgileri Dosyası

Kimlik bilgileri dosyasının yolunu belirtin:

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"

# Proxy sunucunuzu korumak için şifre (herhangi bir güvenli dize oluşturun)
# Gateway'inize bağlanırken bunu api_key olarak kullanacaksınız
PROXY_API_KEY="my-super-secret-password-123"
```

<details>
<summary>📄 JSON dosya formatı</summary>

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

### Seçenek 2: Ortam Değişkenleri (.env dosyası)

Proje kök dizininde `.env` dosyası oluşturun:

```env
# Gerekli
REFRESH_TOKEN="kiro_refresh_token_unuz"

# Proxy sunucunuzu korumak için şifre (herhangi bir güvenli dize oluşturun)
PROXY_API_KEY="my-super-secret-password-123"

# İsteğe bağlı
PROFILE_ARN="arn:aws:codewhisperer:us-east-1:..."
KIRO_REGION="us-east-1"
```

### Seçenek 3: AWS SSO Kimlik Bilgileri (kiro-cli)

AWS IAM Identity Center (SSO) ile `kiro-cli` kullanıyorsanız, gateway otomatik olarak AWS SSO OIDC kimlik doğrulamasını algılar ve kullanır.

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/your-sso-cache-file.json"

# Proxy sunucunuzu korumak için şifre
PROXY_API_KEY="my-super-secret-password-123"

# Not: AWS SSO OIDC (Builder ID) kullanıcıları için PROFILE_ARN gerekli DEĞİLDİR
# Gateway onsuz çalışacaktır
```

<details>
<summary>📄 AWS SSO JSON dosya formatı</summary>

AWS SSO kimlik bilgileri dosyaları (`~/.aws/sso/cache/` konumundan) şunları içerir:

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

**Not:** AWS SSO OIDC (Builder ID) kullanıcıları `profileArn`'a ihtiyaç DUYMAZ. Gateway onsuz çalışacaktır (belirtilirse yok sayılır).

</details>

<details>
<summary>🔍 Nasıl çalışır</summary>

Gateway, kimlik bilgileri dosyasına göre kimlik doğrulama türünü otomatik olarak algılar:

- **Kiro Desktop Auth** (varsayılan): `clientId` ve `clientSecret` YOKKEN kullanılır
  - Endpoint: `https://prod.{region}.auth.desktop.kiro.dev/refreshToken`
  
- **AWS SSO OIDC**: `clientId` ve `clientSecret` VARKEN kullanılır
  - Endpoint: `https://oidc.{region}.amazonaws.com/token`

Ek yapılandırma gerekmez — sadece kimlik bilgileri dosyanıza işaret edin!

</details>

### Seçenek 4: kiro-cli SQLite Veritabanı

`kiro-cli` kullanıyorsanız ve SQLite veritabanını doğrudan kullanmayı tercih ediyorsanız:

```env
KIRO_CLI_DB_FILE="~/.local/share/kiro-cli/data.sqlite3"

# Proxy sunucunuzu korumak için şifre
PROXY_API_KEY="my-super-secret-password-123"

# Not: AWS SSO OIDC (Builder ID) kullanıcıları için PROFILE_ARN gerekli DEĞİLDİR
# Gateway onsuz çalışacaktır
```

<details>
<summary>📄 Veritabanı konumları</summary>

| CLI Aracı | Veritabanı Yolu |
|-----------|-----------------|
| kiro-cli | `~/.local/share/kiro-cli/data.sqlite3` |
| amazon-q-developer-cli | `~/.local/share/amazon-q/data.sqlite3` |

Gateway, `auth_kv` tablosundan kimlik bilgilerini okur:
- `kirocli:odic:token` veya `codewhisperer:odic:token` — erişim token'ı, yenileme token'ı, son kullanma tarihi
- `kirocli:odic:device-registration` veya `codewhisperer:odic:device-registration` — istemci ID'si ve gizli anahtar

Farklı kiro-cli sürümleriyle uyumluluk için her iki anahtar formatı da desteklenir.

</details>

### Kimlik Bilgilerini Alma

**Kiro IDE kullanıcıları için:**
- Kiro IDE'ye giriş yapın ve yukarıdaki Seçenek 1'i kullanın (JSON kimlik bilgileri dosyası)
- Kimlik bilgileri dosyası giriş yaptıktan sonra otomatik olarak oluşturulur

**Kiro CLI kullanıcıları için:**
- `kiro-cli login` ile giriş yapın ve yukarıdaki Seçenek 3 veya Seçenek 4'ü kullanın
- Manuel token çıkarma gerekmez!

<details>
<summary>🔧 Gelişmiş: Manuel token çıkarma</summary>

Refresh token'ı manuel olarak çıkarmanız gerekiyorsa (örneğin, hata ayıklama için), Kiro IDE trafiğini yakalayabilirsiniz:
- Şu adrese yapılan istekleri arayın: `prod.us-east-1.auth.desktop.kiro.dev/refreshToken`

</details>

---

## 📡 API Referansı

### Endpoint'ler

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/` | GET | Sağlık kontrolü |
| `/health` | GET | Detaylı sağlık kontrolü |
| `/v1/models` | GET | Mevcut modelleri listele |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API |
| `/v1/messages` | POST | Anthropic Messages API |

---

## 💡 Kullanım Örnekleri

### OpenAI API

<details>
<summary>🔹 Basit cURL İsteği</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "Merhaba!"}],
    "stream": true
  }'
```

> **Not:** `my-super-secret-password-123`'ü `.env` dosyanızda ayarladığınız `PROXY_API_KEY` ile değiştirin.

</details>

<details>
<summary>🔹 Streaming İsteği</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "system", "content": "Sen yardımcı bir asistansın."},
      {"role": "user", "content": "2+2 kaç eder?"}
    ],
    "stream": true
  }'
```

</details>

<details>
<summary>🛠️ Araç Çağırma ile</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "Londra'\''da hava nasıl?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Bir konum için hava durumunu al",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "Şehir adı"}
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
    api_key="my-super-secret-password-123"  # .env'deki PROXY_API_KEY'iniz
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "system", "content": "Sen yardımcı bir asistansın."},
        {"role": "user", "content": "Merhaba!"}
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
    api_key="my-super-secret-password-123",  # .env'deki PROXY_API_KEY'iniz
    model="claude-sonnet-4-5"
)

response = llm.invoke("Merhaba, nasılsın?")
print(response.content)
```

</details>

### Anthropic API

<details>
<summary>🔹 Basit cURL İsteği</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Merhaba!"}]
  }'
```

> **Not:** Anthropic API, `Authorization: Bearer` yerine `x-api-key` header'ı kullanır. Her ikisi de desteklenir.

</details>

<details>
<summary>🔹 Sistem Prompt'u ile</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "system": "Sen yardımcı bir asistansın.",
    "messages": [{"role": "user", "content": "Merhaba!"}]
  }'
```

> **Not:** Anthropic API'de `system` ayrı bir alandır, mesaj değil.

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
    "messages": [{"role": "user", "content": "Merhaba!"}]
  }'
```

</details>

<details>
<summary>🐍 Python Anthropic SDK</summary>

```python
import anthropic

client = anthropic.Anthropic(
    api_key="my-super-secret-password-123",  # .env'deki PROXY_API_KEY'iniz
    base_url="http://localhost:8000"
)

# Streaming olmadan
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Merhaba!"}]
)
print(response.content[0].text)

# Streaming ile
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Merhaba!"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

</details>

---

## 🔧 Hata Ayıklama

Hata ayıklama günlüğü **varsayılan olarak devre dışıdır**. Etkinleştirmek için `.env`'nize ekleyin:

```env
# Hata ayıklama günlük modu:
# - off: devre dışı (varsayılan)
# - errors: yalnızca başarısız istekler için günlük kaydet (4xx, 5xx) - sorun giderme için önerilir
# - all: her istek için günlük kaydet (her istekte üzerine yazar)
DEBUG_MODE=errors
```

### Hata Ayıklama Modları

| Mod | Açıklama | Kullanım Durumu |
|-----|----------|-----------------|
| `off` | Devre dışı (varsayılan) | Üretim |
| `errors` | Yalnızca başarısız istekler için günlük kaydet (4xx, 5xx) | **Sorun giderme için önerilir** |
| `all` | Her istek için günlük kaydet | Geliştirme/hata ayıklama |

### Hata Ayıklama Dosyaları

Etkinleştirildiğinde, istekler `debug_logs/` klasörüne kaydedilir:

| Dosya | Açıklama |
|-------|----------|
| `request_body.json` | İstemciden gelen istek (OpenAI formatı) |
| `kiro_request_body.json` | Kiro API'ye gönderilen istek |
| `response_stream_raw.txt` | Kiro'dan ham akış |
| `response_stream_modified.txt` | Dönüştürülmüş akış (OpenAI formatı) |
| `app_logs.txt` | İstek için uygulama günlükleri |
| `error_info.json` | Hata detayları (yalnızca hatalarda) |

---

## 📜 Lisans

Bu proje **GNU Affero General Public License v3.0 (AGPL-3.0)** altında lisanslanmıştır.

Bu şu anlama gelir:
- ✅ Bu yazılımı kullanabilir, değiştirebilir ve dağıtabilirsiniz
- ✅ Ticari amaçlarla kullanabilirsiniz
- ⚠️ Yazılımı dağıttığınızda **kaynak kodunu açıklamalısınız**
- ⚠️ **Ağ kullanımı dağıtımdır** — değiştirilmiş bir sürümü sunucuda çalıştırır ve başkalarının onunla etkileşime girmesine izin verirseniz, kaynak kodunu onlara sunmalısınız
- ⚠️ Değişiklikler aynı lisans altında yayınlanmalıdır

Tam lisans metni için [LICENSE](../../LICENSE) dosyasına bakın.

### Neden AGPL-3.0?

AGPL-3.0, bu yazılıma yapılan iyileştirmelerin tüm topluluğa fayda sağlamasını garanti eder. Bu gateway'i değiştirir ve bir hizmet olarak dağıtırsanız, iyileştirmelerinizi kullanıcılarınızla paylaşmalısınız.

### Katkıda Bulunan Lisans Sözleşmesi (CLA)

Bu projeye katkı göndererek, [Katkıda Bulunan Lisans Sözleşmemizin (CLA)](../../CLA.md) şartlarını kabul etmiş olursunuz. Bu şunları garanti eder:
- Katkıyı gönderme hakkınız var
- Bakımcıya katkınızı kullanma ve yeniden lisanslama hakları veriyorsunuz
- Proje yasal olarak korunmaya devam ediyor

---

## 💖 Projeyi Destekle

<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Smiling%20Face%20with%20Hearts.png" alt="Love" width="80" />

**Bu proje size zaman veya para kazandırdıysa, desteklemeyi düşünün!**

Her katkı bu projenin canlı ve büyüyen kalmasına yardımcı olur

<br>

### 🤑 Bağış Yap

[**☕ Tek Seferlik Bağış**](https://app.lava.top/jwadow?tabId=donate) &nbsp;•&nbsp; [**💎 Aylık Destek**](https://app.lava.top/jwadow?tabId=subscriptions)

<br>

### 🪙 Veya kripto gönderin

| Para Birimi | Ağ | Adres |
|:-----------:|:--:|:------|
| **USDT** | TRC20 | `TSVtgRc9pkC1UgcbVeijBHjFmpkYHDRu26` |
| **BTC** | Bitcoin | `12GZqxqpcBsqJ4Vf1YreLqwoMGvzBPgJq6` |
| **ETH** | Ethereum | `0xc86eab3bba3bbaf4eb5b5fff8586f1460f1fd395` |
| **SOL** | Solana | `9amykF7KibZmdaw66a1oqYJyi75fRqgdsqnG66AK3jvh` |
| **TON** | TON | `UQBVh8T1H3GI7gd7b-_PPNnxHYYxptrcCVf3qQk5v41h3QTM` |

</div>

---

## ⚠️ Sorumluluk Reddi

Bu proje Amazon Web Services (AWS), Anthropic veya Kiro IDE ile bağlantılı değildir, onlar tarafından onaylanmamış veya desteklenmemiştir. Kendi riskinizle kullanın ve temel API'lerin hizmet şartlarına uygun olarak kullanın.

---

<div align="center">

**[⬆ Başa Dön](#-kiro-gateway)**

</div>
