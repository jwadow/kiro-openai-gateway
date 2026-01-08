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
Kiro Gateway - OpenAI-compatible interface for Kiro API.

Application entry point. Creates FastAPI app and connects routes.

Usage:
    # Using default settings (host: 0.0.0.0, port: 8000)
    python main.py
    
    # With CLI arguments (highest priority)
    python main.py --port 9000
    python main.py --host 127.0.0.1 --port 9000
    
    # With environment variables (medium priority)
    SERVER_PORT=9000 python main.py
    
    # Using uvicorn directly (uvicorn handles its own CLI args)
    uvicorn main:app --host 0.0.0.0 --port 8000

Priority: CLI args > Environment variables > Default values
"""

import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from kiro_gateway.config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    REFRESH_TOKEN,
    PROFILE_ARN,
    REGION,
    KIRO_CREDS_FILE,
    KIRO_CLI_DB_FILE,
    PROXY_API_KEY,
    LOG_LEVEL,
    SERVER_HOST,
    SERVER_PORT,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    _warn_deprecated_debug_setting,
    _warn_timeout_configuration,
)
from kiro_gateway.auth import KiroAuthManager
from kiro_gateway.cache import ModelInfoCache
from kiro_gateway.routes import router
from kiro_gateway.exceptions import validation_exception_handler


# --- Loguru Configuration ---
logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """
    Intercepts logs from standard logging and redirects them to loguru.
    
    This allows capturing logs from uvicorn, FastAPI and other libraries
    that use standard logging instead of loguru.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        # Get the corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find the caller frame for correct source display
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging_intercept():
    """
    Configures log interception from standard logging to loguru.
    
    Intercepts logs from:
    - uvicorn (access logs, error logs)
    - uvicorn.error
    - uvicorn.access
    - fastapi
    """
    # List of loggers to intercept
    loggers_to_intercept = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]
    
    for logger_name in loggers_to_intercept:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False


# Configure uvicorn/fastapi log interception
setup_logging_intercept()


# --- Configuration Validation ---
def validate_configuration() -> None:
    """
    Validates that required configuration is present.
    
    Checks:
    - .env file exists
    - Either REFRESH_TOKEN or KIRO_CREDS_FILE is configured
    
    Raises:
        SystemExit: If critical configuration is missing
    """
    errors = []
    
    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        errors.append(
            ".env file not found!\n"
            "\n"
            "To get started:\n"
            "1. Create .env or rename from .env.example:\n"
            "   cp .env.example .env\n"
            "\n"
            "2. Edit .env and configure your credentials:\n"
            "   2.1. Set you super-secret password as PROXY_API_KEY\n"
            "   2.2. Set your Kiro credentials:\n"
            "      - 1 way: KIRO_CREDS_FILE to your Kiro credentials JSON file\n"
            "      - 2 way: REFRESH_TOKEN from Kiro IDE traffic\n"
            "\n"
            "See README.md for detailed instructions."
        )
    else:
        # .env exists, check for credentials
        has_refresh_token = bool(REFRESH_TOKEN)
        has_creds_file = bool(KIRO_CREDS_FILE)
        has_cli_db = bool(KIRO_CLI_DB_FILE)
        
        # Check if creds file actually exists
        if KIRO_CREDS_FILE:
            creds_path = Path(KIRO_CREDS_FILE).expanduser()
            if not creds_path.exists():
                has_creds_file = False
                logger.warning(f"KIRO_CREDS_FILE not found: {KIRO_CREDS_FILE}")
        
        # Check if CLI database file actually exists
        if KIRO_CLI_DB_FILE:
            cli_db_path = Path(KIRO_CLI_DB_FILE).expanduser()
            if not cli_db_path.exists():
                has_cli_db = False
                logger.warning(f"KIRO_CLI_DB_FILE not found: {KIRO_CLI_DB_FILE}")
        
        if not has_refresh_token and not has_creds_file and not has_cli_db:
            errors.append(
                "No Kiro credentials configured!\n"
                "\n"
                "   Configure one of the following in your .env file:\n"
                "\n"
                "Set you super-secret password as PROXY_API_KEY\n"
                "   PROXY_API_KEY=\"my-super-secret-password-123\"\n"
                "\n"
                "   Option 1 (Recommended): JSON credentials file\n"
                "      KIRO_CREDS_FILE=\"path/to/your/kiro-credentials.json\"\n"
                "\n"
                "   Option 2: Refresh token\n"
                "      REFRESH_TOKEN=\"your_refresh_token_here\"\n"
                "\n"
                "   Option 3: kiro-cli SQLite database (AWS SSO)\n"
                "      KIRO_CLI_DB_FILE=\"~/.local/share/kiro-cli/data.sqlite3\"\n"
                "\n"
                "   See README.md for how to obtain credentials."
            )
    
    # Print errors and exit if any
    if errors:
        logger.error("")
        logger.error("=" * 60)
        logger.error("  CONFIGURATION ERROR")
        logger.error("=" * 60)
        for error in errors:
            for line in error.split('\n'):
                logger.error(f"  {line}")
        logger.error("=" * 60)
        logger.error("")
        sys.exit(1)
    
    # Note: Credential loading details are logged by KiroAuthManager


def _is_running_tests() -> bool:
    return "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ


# Run configuration validation on import (skip during tests)
if not _is_running_tests():
    validate_configuration()
    _warn_deprecated_debug_setting()
    _warn_timeout_configuration()


# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    
    Creates and initializes:
    - KiroAuthManager for token management
    - ModelInfoCache for model caching
    """
    logger.info("Starting application... Creating state managers.")
    
    # Create AuthManager
    # Priority: SQLite DB > JSON file > environment variables
    app.state.auth_manager = KiroAuthManager(
        refresh_token=REFRESH_TOKEN,
        profile_arn=PROFILE_ARN,
        region=REGION,
        creds_file=KIRO_CREDS_FILE if KIRO_CREDS_FILE else None,
        sqlite_db=KIRO_CLI_DB_FILE if KIRO_CLI_DB_FILE else None,
    )
    
    # Create model cache
    app.state.model_cache = ModelInfoCache()
    
    yield
    
    logger.info("Shutting down application.")


# --- FastAPI Application ---
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)


# --- CORS Middleware ---
# Allow CORS for all origins to support browser clients
# and tools that send preflight OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


# --- Validation Error Handler Registration ---
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# --- Route Registration ---
app.include_router(router)


# --- Uvicorn log config ---
# Minimal configuration for redirecting uvicorn logs to loguru.
# Uses InterceptHandler which intercepts logs and passes them to loguru.
UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "default": {
            "class": "main.InterceptHandler",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}


def parse_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments for server configuration.
    
    CLI arguments have the highest priority, overriding both
    environment variables and default values.
    
    Returns:
        Parsed arguments namespace with host and port values
    """
    parser = argparse.ArgumentParser(
        description=f"{APP_TITLE} - {APP_DESCRIPTION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Priority (highest to lowest):
  1. CLI arguments (--host, --port)
  2. Environment variables (SERVER_HOST, SERVER_PORT)
  3. Default values (0.0.0.0:8000)

Examples:
  python main.py                          # Use defaults or env vars
  python main.py --port 9000              # Override port only
  python main.py --host 127.0.0.1         # Local connections only
  python main.py -H 0.0.0.0 -p 8080       # Short form
  
  SERVER_PORT=9000 python main.py         # Via environment
  uvicorn main:app --port 9000            # Via uvicorn directly
        """
    )
    
    parser.add_argument(
        "-H", "--host",
        type=str,
        default=None,  # None means "use env or default"
        metavar="HOST",
        help=f"Server host address (default: {DEFAULT_SERVER_HOST}, env: SERVER_HOST)"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=None,  # None means "use env or default"
        metavar="PORT",
        help=f"Server port (default: {DEFAULT_SERVER_PORT}, env: SERVER_PORT)"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}"
    )
    
    return parser.parse_args()


def resolve_server_config(args: argparse.Namespace) -> tuple[str, int]:
    """
    Resolve final server configuration using priority hierarchy.
    
    Priority (highest to lowest):
    1. CLI arguments (--host, --port)
    2. Environment variables (SERVER_HOST, SERVER_PORT)
    3. Default values (0.0.0.0:8000)
    
    Args:
        args: Parsed CLI arguments
        
    Returns:
        Tuple of (host, port) with resolved values
    """
    # Host resolution: CLI > ENV > Default
    if args.host is not None:
        final_host = args.host
        host_source = "CLI argument"
    elif SERVER_HOST != DEFAULT_SERVER_HOST:
        final_host = SERVER_HOST
        host_source = "environment variable"
    else:
        final_host = DEFAULT_SERVER_HOST
        host_source = "default"
    
    # Port resolution: CLI > ENV > Default
    if args.port is not None:
        final_port = args.port
        port_source = "CLI argument"
    elif SERVER_PORT != DEFAULT_SERVER_PORT:
        final_port = SERVER_PORT
        port_source = "environment variable"
    else:
        final_port = DEFAULT_SERVER_PORT
        port_source = "default"
    
    # Log configuration sources for transparency
    logger.debug(f"Host: {final_host} (from {host_source})")
    logger.debug(f"Port: {final_port} (from {port_source})")
    
    return final_host, final_port


def print_startup_banner(host: str, port: int) -> None:
    """
    Print a startup banner with server information.
    
    Args:
        host: Server host address
        port: Server port
    """
    # ANSI color codes
    GREEN = "\033[92m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    
    # Determine display URL
    display_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{port}"
    
    print()
    print(f"  {WHITE}{BOLD}👻 {APP_TITLE} v{APP_VERSION}{RESET}")
    print()
    print(f"  {WHITE}Server running at:{RESET}")
    print(f"  {GREEN}{BOLD}➜  {url}{RESET}")
    print()
    print(f"  {DIM}API Docs:      {url}/docs{RESET}")
    print(f"  {DIM}Health Check:  {url}/health{RESET}")
    print()


# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn
    
    # Parse CLI arguments
    args = parse_cli_args()
    
    # Resolve final configuration with priority hierarchy
    final_host, final_port = resolve_server_config(args)
    
    # Print startup banner
    print_startup_banner(final_host, final_port)
    
    logger.info(f"Starting Uvicorn server on {final_host}:{final_port}...")
    
    # Use string reference to avoid double module import
    uvicorn.run(
        "main:app",
        host=final_host,
        port=final_port,
        log_config=UVICORN_LOG_CONFIG,
    )
