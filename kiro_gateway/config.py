# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
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
# Server Settings
# ==================================================================================================

# Server host (default: 0.0.0.0 - listen on all interfaces)
# Use "127.0.0.1" to only allow local connections
DEFAULT_SERVER_HOST: str = "0.0.0.0"
SERVER_HOST: str = os.getenv("SERVER_HOST", DEFAULT_SERVER_HOST)

# Server port (default: 8000)
# Can be overridden by CLI: python main.py --port 9000
# Or by uvicorn directly: uvicorn main:app --port 9000
DEFAULT_SERVER_PORT: int = 8000
SERVER_PORT: int = int(os.getenv("SERVER_PORT", str(DEFAULT_SERVER_PORT)))

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

# Path to kiro-cli SQLite database (optional, for AWS SSO OIDC authentication)
# Default location: ~/.local/share/kiro-cli/data.sqlite3 (Linux/macOS)
# or ~/.local/share/amazon-q/data.sqlite3 (amazon-q-developer-cli)
_raw_cli_db_file = _get_raw_env_value("KIRO_CLI_DB_FILE") or os.getenv("KIRO_CLI_DB_FILE", "")
KIRO_CLI_DB_FILE: str = str(Path(_raw_cli_db_file)) if _raw_cli_db_file else ""

# ==================================================================================================
# Kiro API URL Templates
# ==================================================================================================

# URL for token refresh (Kiro Desktop Auth)
KIRO_REFRESH_URL_TEMPLATE: str = "https://prod.{region}.auth.desktop.kiro.dev/refreshToken"

# URL for token refresh (AWS SSO OIDC - used by kiro-cli)
AWS_SSO_OIDC_URL_TEMPLATE: str = "https://oidc.{region}.amazonaws.com/token"

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

# Kiro API returns 400 "Improperly formed request" error when tool descriptions
# in toolSpecification.description are too long.
#
# Solution: Tool Documentation Reference Pattern
# - If description ≤ limit → keep as is
# - If description > limit:
#   * In toolSpecification.description → reference to system prompt:
#     "[Full documentation in system prompt under '## Tool: {name}']"
#   * In system prompt, a section "## Tool: {name}" with full description is added
#
# The model sees an explicit reference and knows exactly where to find full documentation.

# Maximum length of tool description in characters.
# Descriptions longer than this limit will be moved to system prompt.
# Set to 0 to disable (not recommended - will cause Kiro API errors).
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


def _warn_timeout_configuration():
    """
    Print warning if timeout configuration is suboptimal.
    Called at application startup.
    
    FIRST_TOKEN_TIMEOUT should be less than STREAMING_READ_TIMEOUT:
    - FIRST_TOKEN_TIMEOUT: time to wait for model to START responding
    - STREAMING_READ_TIMEOUT: time to wait BETWEEN chunks during streaming
    """
    if FIRST_TOKEN_TIMEOUT >= STREAMING_READ_TIMEOUT:
        import sys
        YELLOW = "\033[93m"
        RESET = "\033[0m"
        
        warning_text = f"""
{YELLOW}⚠️  WARNING: Suboptimal timeout configuration detected.
    
    FIRST_TOKEN_TIMEOUT ({FIRST_TOKEN_TIMEOUT}s) >= STREAMING_READ_TIMEOUT ({STREAMING_READ_TIMEOUT}s)
    
    These timeouts serve different purposes:
      - FIRST_TOKEN_TIMEOUT: time to wait for model to START responding (default: 15s)
      - STREAMING_READ_TIMEOUT: time to wait BETWEEN chunks during streaming (default: 300s)
    
    Recommendation: FIRST_TOKEN_TIMEOUT should be LESS than STREAMING_READ_TIMEOUT.
    
    Example configuration:
      FIRST_TOKEN_TIMEOUT=15
      STREAMING_READ_TIMEOUT=300{RESET}
"""
        print(warning_text, file=sys.stderr)

# ==================================================================================================
# Fake Reasoning Settings (Extended Thinking via Tag Injection)
# ==================================================================================================

# Enable fake reasoning - injects special tags into requests to enable model reasoning.
# When enabled, the model will include its reasoning process in the response wrapped in tags.
# The response is then parsed and converted to OpenAI-compatible reasoning_content format.
#
# WHY "FAKE"? This is NOT native extended thinking API support. Instead, we inject
# <thinking_mode>enabled</thinking_mode> tags into the prompt, and the model responds
# with <thinking>...</thinking> blocks that we parse and convert to reasoning_content.
# It works great, but it's a hack - hence "fake" reasoning.
#
# Default: true (enabled) - provides premium experience out of the box
_FAKE_REASONING_RAW: str = os.getenv("FAKE_REASONING", "").lower()
# Default is True - if env var is not set or empty, enable fake reasoning
FAKE_REASONING_ENABLED: bool = _FAKE_REASONING_RAW not in ("false", "0", "no", "disabled", "off")

# Maximum thinking length in tokens.
# This value is injected into the request as <max_thinking_length>{value}</max_thinking_length>
# Higher values allow for more detailed reasoning but increase response time and token usage.
# Default: 4000 tokens
FAKE_REASONING_MAX_TOKENS: int = int(os.getenv("FAKE_REASONING_MAX_TOKENS", "4000"))

# How to handle the thinking block in responses:
# - "as_reasoning_content": Extract to reasoning_content field (OpenAI-compatible, recommended)
# - "remove": Remove thinking block completely, return only final answer
# - "pass": Pass through as-is with original tags in content
# - "strip_tags": Remove tags but keep thinking content in regular content
#
# Default: "as_reasoning_content"
_FAKE_REASONING_HANDLING_RAW: str = os.getenv("FAKE_REASONING_HANDLING", "as_reasoning_content").lower()
if _FAKE_REASONING_HANDLING_RAW in ("as_reasoning_content", "remove", "pass", "strip_tags"):
    FAKE_REASONING_HANDLING: str = _FAKE_REASONING_HANDLING_RAW
else:
    FAKE_REASONING_HANDLING: str = "as_reasoning_content"

# List of opening tags to detect thinking blocks.
# The parser will look for any of these tags at the start of the response.
# Order matters - first match wins.
FAKE_REASONING_OPEN_TAGS: List[str] = ["<thinking>", "<think>", "<reasoning>", "<thought>"]

# Maximum size of initial buffer for tag detection (characters).
# If no thinking tag is found within this limit, content is treated as regular response.
# Lower values = faster first token, but may miss tags with leading whitespace.
# Default: 30 characters (enough for longest tag + some whitespace)
FAKE_REASONING_INITIAL_BUFFER_SIZE: int = int(os.getenv("FAKE_REASONING_INITIAL_BUFFER_SIZE", "20"))


# ==================================================================================================
# Application Version
# ==================================================================================================

APP_VERSION: str = "2.0-dev"
APP_TITLE: str = "Kiro Gateway"
APP_DESCRIPTION: str = "OpenAI-compatible interface for Kiro API (AWS CodeWhisperer). Made by @jwadow"


def get_kiro_refresh_url(region: str) -> str:
    """Return Kiro Desktop Auth token refresh URL for the specified region."""
    return KIRO_REFRESH_URL_TEMPLATE.format(region=region)


def get_aws_sso_oidc_url(region: str) -> str:
    """Return AWS SSO OIDC token URL for the specified region."""
    return AWS_SSO_OIDC_URL_TEMPLATE.format(region=region)


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