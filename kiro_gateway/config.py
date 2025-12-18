# -*- coding: utf-8 -*-

# Kiro OpenAI Gateway
# https://github.com/jwadow/kiro-openai-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Kiro Gateway Configuration.

Centralized storage for all settings, constants, and mappings.
Loads environment variables and provides typed access to them.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _get_raw_env_value(var_name: str, env_file: str = ".env") -> Optional[str]:
    """
    Read variable value from .env file without processing escape sequences.
    
    This is necessary for correct handling of Windows paths where backslashes
    (e.g., D:\\Projects\\file.json) may be incorrectly interpreted
    as escape sequences (\\a -> bell, \\n -> newline, etc.).
    
    Args:
        var_name: Environment variable name
        env_file: Path to .env file (default ".env")
    
    Returns:
        Raw variable value or None if not found
    """
    env_path = Path(env_file)
    if not env_path.exists():
        return None
    
    try:
        # Read file as-is, without interpretation
        content = env_path.read_text(encoding="utf-8")
        
        # Search for variable considering different formats:
        # VAR="value" or VAR='value' or VAR=value
        # Pattern captures value with or without quotes
        pattern = rf'^{re.escape(var_name)}=(["\']?)(.+?)\1\s*$'
        
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            
            match = re.match(pattern, line)
            if match:
                # Return value as-is, without processing escape sequences
                return match.group(2)
    except Exception:
        pass
    
    return None

# ==================================================================================================
# Proxy Server Settings
# ==================================================================================================

# API key for proxy access (clients must pass it in Authorization header)
PROXY_API_KEY: str = os.getenv("PROXY_API_KEY", "changeme_proxy_secret")

# ==================================================================================================
# Kiro API Credentials
# ==================================================================================================

# Refresh token for updating access token
REFRESH_TOKEN: str = os.getenv("REFRESH_TOKEN", "")

# Profile ARN for AWS CodeWhisperer
PROFILE_ARN: str = os.getenv("PROFILE_ARN", "")

# AWS region (default us-east-1)
REGION: str = os.getenv("KIRO_REGION", "us-east-1")

# Path to credentials file (optional, alternative to .env)
# Read directly from .env to avoid escape sequence issues on Windows
# (e.g., \a in path D:\Projects\adolf is interpreted as bell character)
_raw_creds_file = _get_raw_env_value("KIRO_CREDS_FILE") or os.getenv("KIRO_CREDS_FILE", "")
# Normalize path for cross-platform compatibility
KIRO_CREDS_FILE: str = str(Path(_raw_creds_file)) if _raw_creds_file else ""

# ==================================================================================================
# Kiro API URL Templates
# ==================================================================================================

# URL for token refresh
KIRO_REFRESH_URL_TEMPLATE: str = "https://prod.{region}.auth.desktop.kiro.dev/refreshToken"

# Host for main API (generateAssistantResponse)
KIRO_API_HOST_TEMPLATE: str = "https://codewhisperer.{region}.amazonaws.com"

# Host for Q API (ListAvailableModels)
KIRO_Q_HOST_TEMPLATE: str = "https://q.{region}.amazonaws.com"

# ==================================================================================================
# Token Settings
# ==================================================================================================

# Time before token expiration when refresh is needed (in seconds)
# Default 10 minutes - refresh token in advance to avoid errors
TOKEN_REFRESH_THRESHOLD: int = 600

# ==================================================================================================
# Retry Configuration
# ==================================================================================================

# Maximum number of retry attempts on errors
MAX_RETRIES: int = 3

# Base delay between attempts (seconds)
# Uses exponential backoff: delay * (2 ** attempt)
BASE_RETRY_DELAY: float = 1.0

# ==================================================================================================
# Model Mapping
# ==================================================================================================

# External model names (OpenAI-compatible) -> internal Kiro IDs
# Clients use external names, and we convert them to internal ones
MODEL_MAPPING: Dict[str, str] = {
    # Claude Opus 4.5 - top-tier model
    "claude-opus-4-5": "claude-opus-4.5",
    "claude-opus-4-5-20251101": "claude-opus-4.5",
    
    # Claude Haiku 4.5 - fast model
    "claude-haiku-4-5": "claude-haiku-4.5",
    "claude-haiku-4.5": "claude-haiku-4.5",  # Direct passthrough
    
    # Claude Sonnet 4.5 - enhanced model
    "claude-sonnet-4-5": "CLAUDE_SONNET_4_5_20250929_V1_0",
    "claude-sonnet-4-5-20250929": "CLAUDE_SONNET_4_5_20250929_V1_0",
    
    # Claude Sonnet 4 - balanced model
    "claude-sonnet-4": "CLAUDE_SONNET_4_20250514_V1_0",
    "claude-sonnet-4-20250514": "CLAUDE_SONNET_4_20250514_V1_0",
    
    # Claude 3.7 Sonnet - legacy model
    "claude-3-7-sonnet-20250219": "CLAUDE_3_7_SONNET_20250219_V1_0",
    
    # Aliases for convenience
    "auto": "claude-sonnet-4.5",
}

# List of available models for /v1/models endpoint
# These models will be displayed to clients as available
AVAILABLE_MODELS: List[str] = [
    "claude-opus-4-5",
    "claude-opus-4-5-20251101",
    "claude-haiku-4-5",
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
    "claude-sonnet-4",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-20250219",
]

# ==================================================================================================
# Model Cache Settings
# ==================================================================================================

# Model cache TTL in seconds (1 hour)
MODEL_CACHE_TTL: int = 3600

# Default maximum number of input tokens
DEFAULT_MAX_INPUT_TOKENS: int = 200000

# ==================================================================================================
# Tool Description Handling (Kiro API Limitations)
# ==================================================================================================

# Kiro API возвращает ошибку 400 "Improperly formed request" при слишком длинных
# описаниях инструментов в toolSpecification.description.
#
# Решение: Tool Documentation Reference Pattern
# - Если description ≤ лимита → оставляем как есть
# - Если description > лимита:
#   * В toolSpecification.description → ссылка на system prompt:
#     "[Full documentation in system prompt under '## Tool: {name}']"
#   * В system prompt добавляется секция "## Tool: {name}" с полным описанием
#
# Модель видит явную ссылку и точно понимает, где искать полную документацию.

# Максимальная длина description для tool в символах.
# Описания длиннее этого лимита будут перенесены в system prompt.
# Установите 0 для отключения (не рекомендуется - вызовет ошибки Kiro API).
TOOL_DESCRIPTION_MAX_LENGTH: int = int(os.getenv("TOOL_DESCRIPTION_MAX_LENGTH", "10000"))

# ==================================================================================================
# Logging Settings
# ==================================================================================================

# Log level for the application
# Available levels: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO (recommended for production)
# Set to DEBUG for detailed troubleshooting
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# ==================================================================================================
# First Token Timeout Settings (Streaming Retry)
# ==================================================================================================

# Timeout for waiting for the first token from the model (in seconds).
# If the model doesn't respond within this time, the request will be cancelled and retried.
# This helps handle "stuck" requests when the model takes too long to think.
# Default: 30 seconds (recommended for production)
# Set a lower value (e.g., 10-15) for more aggressive retry.
FIRST_TOKEN_TIMEOUT: float = float(os.getenv("FIRST_TOKEN_TIMEOUT", "15"))

# Read timeout for streaming responses (in seconds).
# This is the maximum time to wait for data between chunks during streaming.
# Should be longer than FIRST_TOKEN_TIMEOUT since the model may pause between chunks
# while "thinking" (especially for tool calls or complex reasoning).
# Default: 300 seconds (5 minutes) - generous timeout to avoid premature disconnects.
STREAMING_READ_TIMEOUT: float = float(os.getenv("STREAMING_READ_TIMEOUT", "300"))

# Maximum number of attempts on first token timeout.
# After exhausting all attempts, an error will be returned.
# Default: 3 attempts
FIRST_TOKEN_MAX_RETRIES: int = int(os.getenv("FIRST_TOKEN_MAX_RETRIES", "3"))

# ==================================================================================================
# Debug Settings
# ==================================================================================================

# Legacy option (deprecated, will be removed in future releases)
# Use DEBUG_MODE instead
_DEBUG_LAST_REQUEST_RAW: str = os.getenv("DEBUG_LAST_REQUEST", "").lower()
DEBUG_LAST_REQUEST: bool = _DEBUG_LAST_REQUEST_RAW in ("true", "1", "yes")

# Debug logging mode:
# - off: disabled (default)
# - errors: save logs only for failed requests (4xx, 5xx)
# - all: save logs for every request (overwrites on each request)
_DEBUG_MODE_RAW: str = os.getenv("DEBUG_MODE", "").lower()

# Priority logic:
# 1. If DEBUG_MODE is explicitly set → use it
# 2. If DEBUG_MODE is not set but DEBUG_LAST_REQUEST=true → mode "all" (backward compatibility)
# 3. Otherwise → mode "off"
if _DEBUG_MODE_RAW in ("off", "errors", "all"):
    DEBUG_MODE: str = _DEBUG_MODE_RAW
elif DEBUG_LAST_REQUEST:
    DEBUG_MODE: str = "all"
else:
    DEBUG_MODE: str = "off"

# Directory for debug log files
DEBUG_DIR: str = os.getenv("DEBUG_DIR", "debug_logs")


def _warn_deprecated_debug_setting():
    """
    Print warning if deprecated DEBUG_LAST_REQUEST is used.
    Called at application startup.
    """
    if _DEBUG_LAST_REQUEST_RAW and not _DEBUG_MODE_RAW:
        import sys
        # ANSI escape codes: yellow text
        YELLOW = "\033[93m"
        RESET = "\033[0m"
        
        warning_text = f"""
{YELLOW}⚠️  DEPRECATED: DEBUG_LAST_REQUEST will be removed in future releases.
    Please use DEBUG_MODE instead:
      - DEBUG_MODE=off     (disabled, default)
      - DEBUG_MODE=errors  (save logs only for failed requests)
      - DEBUG_MODE=all     (save logs for every request)
    
    DEBUG_LAST_REQUEST=true is equivalent to DEBUG_MODE=all
    See .env.example for more details.{RESET}
"""
        print(warning_text, file=sys.stderr)

# ==================================================================================================
# Application Version
# ==================================================================================================

APP_VERSION: str = "1.0.7"
APP_TITLE: str = "Kiro API Gateway"
APP_DESCRIPTION: str = "OpenAI-compatible interface for Kiro API (AWS CodeWhisperer). Made by @jwadow"


def get_kiro_refresh_url(region: str) -> str:
    """Return token refresh URL for the specified region."""
    return KIRO_REFRESH_URL_TEMPLATE.format(region=region)


def get_kiro_api_host(region: str) -> str:
    """Return API host for the specified region."""
    return KIRO_API_HOST_TEMPLATE.format(region=region)


def get_kiro_q_host(region: str) -> str:
    """Return Q API host for the specified region."""
    return KIRO_Q_HOST_TEMPLATE.format(region=region)


def get_internal_model_id(external_model: str) -> str:
    """
    Convert external model name to internal Kiro ID.
    
    Args:
        external_model: External model name (e.g., "claude-sonnet-4-5")
    
    Returns:
        Internal model ID for Kiro API
    """
    return MODEL_MAPPING.get(external_model, external_model)