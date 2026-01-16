<div align="center">

# 👻 Kiro Gateway

**Gateway proxy para Kiro API (AWS CodeWhisperer)**

[🇬🇧 English](../../README.md) • [🇷🇺 Русский](../ru/README.md) • [🇨🇳 中文](../zh/README.md) • [🇮🇩 Indonesia](../id/README.md) • [🇧🇷 Português](../pt/README.md) • [🇯🇵 日本語](../ja/README.md) • [🇻🇳 Tiếng Việt](../vi/README.md) • [🇹🇷 Türkçe](../tr/README.md) • [🇰🇷 한국어](../ko/README.md)

Hecho con ❤️ por [@Jwadow](https://github.com/jwadow)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Sponsor](https://img.shields.io/badge/💖_Sponsor-Apoya_el_Desarrollo-ff69b4)](#-apoya-el-proyecto)

*Usa modelos Claude a través de cualquier herramienta compatible con OpenAI o Anthropic*

[Modelos](#-modelos-soportados) • [Características](#-características) • [Inicio Rápido](#-inicio-rápido) • [Configuración](#%EF%B8%8F-configuración) • [💖 Apoyar](#-apoya-el-proyecto)

</div>

---

## 🤖 Modelos Soportados

🧠 **Claude Opus 4.5** — El modelo más potente. Mejor para razonamiento complejo, análisis profundo y tareas de investigación.

🚀 **Claude Sonnet 4.5** — Rendimiento equilibrado. Excelente para programación, escritura y tareas de propósito general.

⚡ **Claude Haiku 4.5** — Velocidad relámpago. Perfecto para respuestas rápidas, tareas simples y chat.

📦 **Claude Sonnet 4** — Generación anterior. Todavía potente y confiable para la mayoría de casos de uso.

📦 **Claude 3.7 Sonnet** — Modelo heredado. Disponible para compatibilidad retroactiva.

> 💡 **Resolución Inteligente de Modelos:** Usa cualquier formato de nombre de modelo — `claude-sonnet-4-5`, `claude-sonnet-4.5`, o incluso nombres versionados como `claude-sonnet-4-5-20250929`. El gateway los normaliza automáticamente.

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 🔌 **API compatible con OpenAI** | Funciona con cualquier herramienta compatible con OpenAI |
| 🔌 **API compatible con Anthropic** | Endpoint nativo `/v1/messages` |
| 🧠 **Pensamiento Extendido** | El razonamiento es exclusivo de nuestro proyecto |
| 👁️ **Soporte de Visión** | Envía imágenes al modelo |
| 🛠️ **Llamada de Herramientas** | Soporta llamada de funciones |
| 💬 **Historial completo de mensajes** | Pasa el contexto completo de la conversación |
| 📡 **Streaming** | Soporte completo de streaming SSE |
| 🔄 **Lógica de Reintentos** | Reintentos automáticos en errores (403, 429, 5xx) |
| 📋 **Lista extendida de modelos** | Incluyendo modelos versionados |
| 🔐 **Gestión inteligente de tokens** | Actualización automática antes de la expiración |

---

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.10+
- Uno de los siguientes:
  - [Kiro IDE](https://kiro.dev/) con cuenta iniciada, O
  - [Kiro CLI](https://kiro.dev/cli/) con AWS SSO (Builder ID)

### Instalación

```bash
# Clona el repositorio (requiere Git)
git clone https://github.com/Jwadow/kiro-gateway.git
cd kiro-gateway

# O descarga el ZIP: Code → Download ZIP → extrae → abre la carpeta kiro-gateway

# Instala las dependencias
pip install -r requirements.txt

# Configura (ver sección Configuración)
cp .env.example .env
# Copia y edita .env con tus credenciales

# Inicia el servidor
python main.py

# O con puerto personalizado (si 8000 está ocupado)
python main.py --port 9000
```

El servidor estará disponible en `http://localhost:8000`

---

## ⚙️ Configuración

### Opción 1: Archivo JSON de Credenciales

Especifica la ruta al archivo de credenciales:

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"

# Contraseña para proteger TU servidor proxy (crea cualquier cadena segura)
# Usarás esto como api_key al conectarte a tu gateway
PROXY_API_KEY="my-super-secret-password-123"
```

<details>
<summary>📄 Formato del archivo JSON</summary>

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

### Opción 2: Variables de Entorno (archivo .env)

Crea un archivo `.env` en la raíz del proyecto:

```env
# Requerido
REFRESH_TOKEN="tu_kiro_refresh_token"

# Contraseña para proteger TU servidor proxy (crea cualquier cadena segura)
PROXY_API_KEY="my-super-secret-password-123"

# Opcional
PROFILE_ARN="arn:aws:codewhisperer:us-east-1:..."
KIRO_REGION="us-east-1"
```

### Opción 3: Credenciales AWS SSO (kiro-cli)

Si usas `kiro-cli` con AWS IAM Identity Center (SSO), el gateway detectará y usará automáticamente la autenticación AWS SSO OIDC.

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/your-sso-cache-file.json"

# Contraseña para proteger TU servidor proxy
PROXY_API_KEY="my-super-secret-password-123"

# Nota: PROFILE_ARN NO es necesario para usuarios de AWS SSO OIDC (Builder ID)
# El gateway funcionará sin él
```

<details>
<summary>📄 Formato del archivo JSON de AWS SSO</summary>

Los archivos de credenciales de AWS SSO (de `~/.aws/sso/cache/`) contienen:

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

**Nota:** Los usuarios de AWS SSO OIDC (Builder ID) NO necesitan `profileArn`. El gateway funcionará sin él (si se especifica, será ignorado).

</details>

<details>
<summary>🔍 Cómo funciona</summary>

El gateway detecta automáticamente el tipo de autenticación basándose en el archivo de credenciales:

- **Kiro Desktop Auth** (predeterminado): Usado cuando `clientId` y `clientSecret` NO están presentes
  - Endpoint: `https://prod.{region}.auth.desktop.kiro.dev/refreshToken`
  
- **AWS SSO OIDC**: Usado cuando `clientId` y `clientSecret` están presentes
  - Endpoint: `https://oidc.{region}.amazonaws.com/token`

¡No se necesita configuración adicional — solo apunta a tu archivo de credenciales!

</details>

### Opción 4: Base de datos SQLite de kiro-cli

Si usas `kiro-cli` y prefieres usar su base de datos SQLite directamente:

```env
KIRO_CLI_DB_FILE="~/.local/share/kiro-cli/data.sqlite3"

# Contraseña para proteger TU servidor proxy
PROXY_API_KEY="my-super-secret-password-123"

# Nota: PROFILE_ARN NO es necesario para usuarios de AWS SSO OIDC (Builder ID)
# El gateway funcionará sin él
```

<details>
<summary>📄 Ubicaciones de la base de datos</summary>

| Herramienta CLI | Ruta de la Base de Datos |
|-----------------|--------------------------|
| kiro-cli | `~/.local/share/kiro-cli/data.sqlite3` |
| amazon-q-developer-cli | `~/.local/share/amazon-q/data.sqlite3` |

El gateway lee las credenciales de la tabla `auth_kv` que almacena:
- `kirocli:odic:token` o `codewhisperer:odic:token` — token de acceso, token de actualización, expiración
- `kirocli:odic:device-registration` o `codewhisperer:odic:device-registration` — ID de cliente y secreto

Ambos formatos de clave son soportados para compatibilidad con diferentes versiones de kiro-cli.

</details>

### Obtener Credenciales

**Para usuarios de Kiro IDE:**
- Inicia sesión en Kiro IDE y usa la Opción 1 arriba (archivo JSON de credenciales)
- El archivo de credenciales se crea automáticamente después de iniciar sesión

**Para usuarios de Kiro CLI:**
- Inicia sesión con `kiro-cli login` y usa la Opción 3 u Opción 4 arriba
- ¡No se necesita extracción manual de tokens!

<details>
<summary>🔧 Avanzado: Extracción manual de token</summary>

Si necesitas extraer manualmente el refresh token (por ejemplo, para depuración), puedes interceptar el tráfico de Kiro IDE:
- Busca solicitudes a: `prod.us-east-1.auth.desktop.kiro.dev/refreshToken`

</details>

---

## 📡 Referencia de API

### Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Verificación de salud |
| `/health` | GET | Verificación de salud detallada |
| `/v1/models` | GET | Lista modelos disponibles |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API |
| `/v1/messages` | POST | Anthropic Messages API |

---

## 💡 Ejemplos de Uso

### OpenAI API

<details>
<summary>🔹 Solicitud cURL Simple</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "¡Hola!"}],
    "stream": true
  }'
```

> **Nota:** Reemplaza `my-super-secret-password-123` con el `PROXY_API_KEY` que configuraste en tu archivo `.env`.

</details>

<details>
<summary>🔹 Solicitud con Streaming</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "system", "content": "Eres un asistente útil."},
      {"role": "user", "content": "¿Cuánto es 2+2?"}
    ],
    "stream": true
  }'
```

</details>

<details>
<summary>🛠️ Con Llamada de Herramientas</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "¿Cómo está el clima en Londres?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Obtener el clima para una ubicación",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "Nombre de la ciudad"}
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
    api_key="my-super-secret-password-123"  # Tu PROXY_API_KEY del .env
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "system", "content": "Eres un asistente útil."},
        {"role": "user", "content": "¡Hola!"}
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
    api_key="my-super-secret-password-123",  # Tu PROXY_API_KEY del .env
    model="claude-sonnet-4-5"
)

response = llm.invoke("Hola, ¿cómo estás?")
print(response.content)
```

</details>

### Anthropic API

<details>
<summary>🔹 Solicitud cURL Simple</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "¡Hola!"}]
  }'
```

> **Nota:** La API de Anthropic usa el header `x-api-key` en lugar de `Authorization: Bearer`. Ambos son soportados.

</details>

<details>
<summary>🔹 Con Prompt de Sistema</summary>

```bash
curl http://localhost:8000/v1/messages \
  -H "x-api-key: my-super-secret-password-123" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "system": "Eres un asistente útil.",
    "messages": [{"role": "user", "content": "¡Hola!"}]
  }'
```

> **Nota:** En la API de Anthropic, `system` es un campo separado, no un mensaje.

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
    "messages": [{"role": "user", "content": "¡Hola!"}]
  }'
```

</details>

<details>
<summary>🐍 Python Anthropic SDK</summary>

```python
import anthropic

client = anthropic.Anthropic(
    api_key="my-super-secret-password-123",  # Tu PROXY_API_KEY del .env
    base_url="http://localhost:8000"
)

# Sin streaming
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "¡Hola!"}]
)
print(response.content[0].text)

# Con streaming
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "¡Hola!"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

</details>

---

## 🔧 Depuración

El registro de depuración está **deshabilitado por defecto**. Para habilitar, añade a tu `.env`:

```env
# Modo de registro de depuración:
# - off: deshabilitado (predeterminado)
# - errors: guardar logs solo para solicitudes fallidas (4xx, 5xx) - recomendado para solución de problemas
# - all: guardar logs para cada solicitud (sobrescribe en cada solicitud)
DEBUG_MODE=errors
```

### Modos de Depuración

| Modo | Descripción | Caso de Uso |
|------|-------------|-------------|
| `off` | Deshabilitado (predeterminado) | Producción |
| `errors` | Guardar logs solo para solicitudes fallidas (4xx, 5xx) | **Recomendado para solución de problemas** |
| `all` | Guardar logs para cada solicitud | Desarrollo/depuración |

### Archivos de Depuración

Cuando está habilitado, las solicitudes se registran en la carpeta `debug_logs/`:

| Archivo | Descripción |
|---------|-------------|
| `request_body.json` | Solicitud entrante del cliente (formato OpenAI) |
| `kiro_request_body.json` | Solicitud enviada a la API de Kiro |
| `response_stream_raw.txt` | Stream crudo de Kiro |
| `response_stream_modified.txt` | Stream transformado (formato OpenAI) |
| `app_logs.txt` | Logs de la aplicación para la solicitud |
| `error_info.json` | Detalles del error (solo en errores) |

---

## 📜 Licencia

Este proyecto está licenciado bajo la **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Esto significa:
- ✅ Puedes usar, modificar y distribuir este software
- ✅ Puedes usarlo con fines comerciales
- ⚠️ **Debes revelar el código fuente** cuando distribuyas el software
- ⚠️ **El uso en red es distribución** — si ejecutas una versión modificada en un servidor y permites que otros interactúen con ella, debes hacer el código fuente disponible para ellos
- ⚠️ Las modificaciones deben ser liberadas bajo la misma licencia

Consulta el archivo [LICENSE](../../LICENSE) para el texto completo de la licencia.

### ¿Por qué AGPL-3.0?

AGPL-3.0 asegura que las mejoras a este software beneficien a toda la comunidad. Si modificas este gateway y lo despliegas como un servicio, debes compartir tus mejoras con tus usuarios.

### Acuerdo de Licencia de Contribuidor (CLA)

Al enviar una contribución a este proyecto, aceptas los términos de nuestro [Acuerdo de Licencia de Contribuidor (CLA)](../../CLA.md). Esto asegura que:
- Tienes el derecho de enviar la contribución
- Otorgas al mantenedor derechos para usar y relicenciar tu contribución
- El proyecto permanece legalmente protegido

---

## 💖 Apoya el Proyecto

<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Smiling%20Face%20with%20Hearts.png" alt="Love" width="80" />

**¡Si este proyecto te ahorró tiempo o dinero, considera apoyarlo!**

Cada contribución ayuda a mantener este proyecto vivo y creciendo

<br>

### 🤑 Donar

[**☕ Donación Única**](https://app.lava.top/jwadow?tabId=donate) &nbsp;•&nbsp; [**💎 Apoyo Mensual**](https://app.lava.top/jwadow?tabId=subscriptions)

<br>

### 🪙 O envía criptomonedas

| Moneda | Red | Dirección |
|:------:|:---:|:----------|
| **USDT** | TRC20 | `TSVtgRc9pkC1UgcbVeijBHjFmpkYHDRu26` |
| **BTC** | Bitcoin | `12GZqxqpcBsqJ4Vf1YreLqwoMGvzBPgJq6` |
| **ETH** | Ethereum | `0xc86eab3bba3bbaf4eb5b5fff8586f1460f1fd395` |
| **SOL** | Solana | `9amykF7KibZmdaw66a1oqYJyi75fRqgdsqnG66AK3jvh` |
| **TON** | TON | `UQBVh8T1H3GI7gd7b-_PPNnxHYYxptrcCVf3qQk5v41h3QTM` |

</div>

---

## ⚠️ Descargo de Responsabilidad

Este proyecto no está afiliado, respaldado ni patrocinado por Amazon Web Services (AWS), Anthropic o Kiro IDE. Úsalo bajo tu propio riesgo y en cumplimiento con los términos de servicio de las APIs subyacentes.

---

<div align="center">

**[⬆ Volver Arriba](#-kiro-gateway)**

</div>
