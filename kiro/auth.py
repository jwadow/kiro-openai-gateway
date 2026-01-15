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
Authentication manager for Kiro API.

Manages the lifecycle of access tokens:
- Loading credentials from .env or JSON file
- Automatic token refresh on expiration
- Thread-safe refresh using asyncio.Lock
- Support for both Kiro Desktop Auth and AWS SSO OIDC (kiro-cli)
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from kiro.config import (
    TOKEN_REFRESH_THRESHOLD,
    get_kiro_refresh_url,
    get_kiro_api_host,
    get_kiro_q_host,
    get_aws_sso_oidc_url,
)
from kiro.utils import get_machine_fingerprint


class AuthType(Enum):
    """
    Type of authentication mechanism.
    
    KIRO_DESKTOP: Kiro IDE credentials (default)
        - Uses https://prod.{region}.auth.desktop.kiro.dev/refreshToken
        - JSON body: {"refreshToken": "..."}
    
    AWS_SSO_OIDC: AWS SSO credentials from kiro-cli
        - Uses https://oidc.{region}.amazonaws.com/token
        - Form body: grant_type=refresh_token&client_id=...&client_secret=...&refresh_token=...
        - Requires clientId and clientSecret from credentials file
    """
    KIRO_DESKTOP = "kiro_desktop"
    AWS_SSO_OIDC = "aws_sso_oidc"


class TokenHealth:
    """
    Tracks health status of a refresh token.

    Used to avoid repeatedly trying tokens that have failed recently.
    Implements exponential backoff for failed tokens.
    """

    def __init__(self, token: str):
        self.token = token
        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.total_successes = 0
        self.total_failures = 0
        # Per-token access token storage for background refresh
        self.access_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None

    def record_success(self, access_token: str, expires_at: datetime) -> None:
        """Record a successful token refresh."""
        self.consecutive_failures = 0
        self.last_success_time = datetime.now(timezone.utc)
        self.total_successes += 1
        self.access_token = access_token
        self.expires_at = expires_at

    def record_failure(self) -> None:
        """Record a failed token refresh."""
        self.consecutive_failures += 1
        self.last_failure_time = datetime.now(timezone.utc)
        self.total_failures += 1

    def is_healthy(self) -> bool:
        """
        Check if token should be tried.

        Uses exponential backoff: after N consecutive failures,
        wait 2^N seconds before retrying (max 5 minutes).
        """
        if self.consecutive_failures == 0:
            return True

        if not self.last_failure_time:
            return True

        # Exponential backoff: 2^failures seconds, max 300 seconds (5 min)
        backoff_seconds = min(2 ** self.consecutive_failures, 300)
        cooldown_until = self.last_failure_time + timedelta(seconds=backoff_seconds)

        return datetime.now(timezone.utc) >= cooldown_until

    def is_expiring_soon(self, threshold_seconds: int = 600) -> bool:
        """Check if this token's access token is expiring soon."""
        if not self.expires_at:
            return True
        now = datetime.now(timezone.utc)
        return (self.expires_at.timestamp() - now.timestamp()) <= threshold_seconds

    def has_valid_access_token(self) -> bool:
        """Check if this token has a valid (non-expired) access token."""
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def masked_token(self) -> str:
        """Return masked token for logging."""
        if len(self.token) > 16:
            return f"{self.token[:8]}...{self.token[-4:]}"
        return "***"


class KiroAuthManager:
    """
    Manages the token lifecycle for accessing Kiro API.

    Supports:
    - Loading credentials from .env or JSON file
    - Automatic token refresh on expiration
    - Expiration time validation (expiresAt)
    - Saving updated tokens to file
    - Both Kiro Desktop Auth and AWS SSO OIDC (kiro-cli) authentication
    - Multiple refresh tokens with rotation and fallback

    Token Rotation Strategy:
    - Round-robin: Distributes load across all healthy tokens
    - Fallback: On failure, tries next healthy token
    - Health tracking: Avoids repeatedly trying failed tokens (exponential backoff)

    Attributes:
        profile_arn: AWS CodeWhisperer profile ARN
        region: AWS region
        api_host: API host for the current region
        q_host: Q API host for the current region
        fingerprint: Unique machine fingerprint
        auth_type: Type of authentication (KIRO_DESKTOP or AWS_SSO_OIDC)

    Example:
        >>> # Kiro Desktop Auth (default)
        >>> auth_manager = KiroAuthManager(
        ...     refresh_token="your_refresh_token",
        ...     region="us-east-1"
        ... )
        >>> token = await auth_manager.get_access_token()

        >>> # Multiple tokens with rotation
        >>> auth_manager = KiroAuthManager(
        ...     refresh_tokens=["token1", "token2", "token3"],
        ...     region="us-east-1"
        ... )
        >>> token = await auth_manager.get_access_token()

        >>> # AWS SSO OIDC (kiro-cli) - auto-detected from credentials file
        >>> auth_manager = KiroAuthManager(
        ...     creds_file="~/.aws/sso/cache/your-cache.json"
        ... )
        >>> token = await auth_manager.get_access_token()
    """
    
    def __init__(
        self,
        refresh_token: Optional[str] = None,
        refresh_tokens: Optional[list[str]] = None,
        profile_arn: Optional[str] = None,
        region: str = "us-east-1",
        creds_file: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        sqlite_db: Optional[str] = None,
    ):
        """
        Initializes the authentication manager.
        
        Args:
            refresh_token: Refresh token for obtaining access token (deprecated, use refresh_tokens)
            refresh_tokens: List of refresh tokens for fallback/rotation
            profile_arn: AWS CodeWhisperer profile ARN
            region: AWS region (default: us-east-1)
            creds_file: Path to JSON file with credentials (optional)
            client_id: OAuth client ID (for AWS SSO OIDC, optional)
            client_secret: OAuth client secret (for AWS SSO OIDC, optional)
            sqlite_db: Path to kiro-cli SQLite database (optional)
                       Default location: ~/.local/share/kiro-cli/data.sqlite3
        """
        if refresh_tokens:
            self._refresh_tokens = refresh_tokens
        elif refresh_token:
            self._refresh_tokens = [refresh_token]
        else:
            self._refresh_tokens = []

        # Token rotation state
        self._current_token_index = 0
        self._token_health: dict[str, TokenHealth] = {}
        self._total_requests = 0  # For round-robin distribution

        # Initialize health tracking for all tokens
        for token in self._refresh_tokens:
            self._token_health[token] = TokenHealth(token)

        self._refresh_token = self._refresh_tokens[0] if self._refresh_tokens else None

        if len(self._refresh_tokens) > 1:
            logger.info(f"Initialized with {len(self._refresh_tokens)} refresh tokens (rotation enabled)")
        self._profile_arn = profile_arn
        self._region = region
        self._creds_file = creds_file
        self._sqlite_db = sqlite_db
        
        # AWS SSO OIDC specific fields
        self._client_id: Optional[str] = client_id
        self._client_secret: Optional[str] = client_secret
        self._scopes: Optional[list] = None  # OAuth scopes for AWS SSO OIDC
        self._sso_region: Optional[str] = None  # SSO region for OIDC token refresh (may differ from API region)
        
        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

        # Background refresh task
        self._background_refresh_task: Optional[asyncio.Task] = None
        self._background_refresh_interval: int = 300  # 5 minutes
        self._shutdown_event: Optional[asyncio.Event] = None

        # Auth type will be determined after loading credentials
        self._auth_type: AuthType = AuthType.KIRO_DESKTOP
        
        # Dynamic URLs based on region
        self._refresh_url = get_kiro_refresh_url(region)
        self._api_host = get_kiro_api_host(region)
        self._q_host = get_kiro_q_host(region)
        
        # Fingerprint for User-Agent
        self._fingerprint = get_machine_fingerprint()
        
        # Load credentials from SQLite if specified (takes priority over JSON)
        if sqlite_db:
            self._load_credentials_from_sqlite(sqlite_db)
        # Load credentials from JSON file if specified
        elif creds_file:
            self._load_credentials_from_file(creds_file)
        
        # Determine auth type based on available credentials
        self._detect_auth_type()
    
    def _detect_auth_type(self) -> None:
        """
        Detects authentication type based on available credentials.

        AWS SSO OIDC credentials contain clientId and clientSecret.
        Kiro Desktop credentials do not contain these fields.
        """
        if self._client_id and self._client_secret:
            self._auth_type = AuthType.AWS_SSO_OIDC
            logger.info("Detected auth type: AWS SSO OIDC (kiro-cli)")
        else:
            self._auth_type = AuthType.KIRO_DESKTOP
            logger.info("Detected auth type: Kiro Desktop")

    def _get_next_healthy_token(self) -> Optional[str]:
        """
        Get the next healthy token using round-robin distribution.

        Returns:
            Next healthy refresh token, or None if no healthy tokens available
        """
        if not self._refresh_tokens:
            return None

        num_tokens = len(self._refresh_tokens)
        if num_tokens == 1:
            return self._refresh_tokens[0]

        # Round-robin: start from current index and find next healthy token
        for i in range(num_tokens):
            idx = (self._current_token_index + i) % num_tokens
            token = self._refresh_tokens[idx]
            health = self._token_health.get(token)

            if health and health.is_healthy():
                # Move index to next position for true round-robin
                self._current_token_index = (idx + 1) % num_tokens
                return token

        # All tokens unhealthy - return the one with oldest failure (most likely recovered)
        oldest_failure_token = min(
            self._refresh_tokens,
            key=lambda t: (self._token_health[t].last_failure_time or datetime.min.replace(tzinfo=timezone.utc))
        )
        logger.warning(f"All tokens unhealthy, trying oldest failed token")
        return oldest_failure_token

    def _rotate_to_next_token(self) -> Optional[str]:
        """
        Rotate to the next available token after a failure.

        Called when current token fails. Marks current as failed and
        returns next healthy token.

        Returns:
            Next healthy token, or None if no more tokens available
        """
        if not self._refresh_tokens or len(self._refresh_tokens) <= 1:
            return None

        # Mark current token as failed
        if self._refresh_token and self._refresh_token in self._token_health:
            self._token_health[self._refresh_token].record_failure()
            logger.warning(
                f"Token {self._token_health[self._refresh_token].masked_token} failed, "
                f"consecutive failures: {self._token_health[self._refresh_token].consecutive_failures}"
            )

        # Get next healthy token
        next_token = self._get_next_healthy_token()
        if next_token and next_token != self._refresh_token:
            self._refresh_token = next_token
            logger.info(f"Rotated to token {self._token_health[next_token].masked_token}")
            return next_token

        return None

    def _record_token_success(self) -> None:
        """Record successful refresh for current token."""
        if self._refresh_token and self._refresh_token in self._token_health:
            if self._access_token and self._expires_at:
                self._token_health[self._refresh_token].record_success(
                    self._access_token, self._expires_at
                )
            else:
                # Fallback: just update timestamps without storing token
                health = self._token_health[self._refresh_token]
                health.consecutive_failures = 0
                health.last_success_time = datetime.now(timezone.utc)
                health.total_successes += 1

    def get_token_stats(self) -> dict:
        """
        Get statistics about token health and usage.

        Returns:
            Dictionary with token statistics for monitoring
        """
        stats = {
            "total_tokens": len(self._refresh_tokens),
            "current_index": self._current_token_index,
            "total_requests": self._total_requests,
            "background_refresh_active": self._background_refresh_task is not None,
            "tokens": []
        }

        for i, token in enumerate(self._refresh_tokens):
            health = self._token_health.get(token)
            if health:
                stats["tokens"].append({
                    "index": i,
                    "masked": health.masked_token,
                    "healthy": health.is_healthy(),
                    "has_valid_token": health.has_valid_access_token(),
                    "expires_at": health.expires_at.isoformat() if health.expires_at else None,
                    "consecutive_failures": health.consecutive_failures,
                    "total_successes": health.total_successes,
                    "total_failures": health.total_failures,
                    "last_success": health.last_success_time.isoformat() if health.last_success_time else None,
                    "last_failure": health.last_failure_time.isoformat() if health.last_failure_time else None,
                })

        return stats

    async def start_background_refresh(self) -> None:
        """
        Start background task to refresh all tokens periodically.

        This keeps all tokens in the pool "warm" and ready to use,
        reducing latency on requests (no waiting for refresh).
        """
        if len(self._refresh_tokens) <= 1:
            logger.debug("Background refresh not needed for single token")
            return

        if self._background_refresh_task is not None:
            logger.warning("Background refresh already running")
            return

        self._shutdown_event = asyncio.Event()
        self._background_refresh_task = asyncio.create_task(
            self._background_refresh_loop(),
            name="token-background-refresh"
        )
        logger.info(f"Background token refresh started (interval: {self._background_refresh_interval}s)")

    async def stop_background_refresh(self) -> None:
        """Stop the background refresh task gracefully."""
        if self._background_refresh_task is None:
            return

        logger.info("Stopping background token refresh...")
        if self._shutdown_event:
            self._shutdown_event.set()

        try:
            # Wait for task to finish with timeout
            await asyncio.wait_for(self._background_refresh_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Background refresh task did not stop gracefully, cancelling...")
            self._background_refresh_task.cancel()
            try:
                await self._background_refresh_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            pass

        self._background_refresh_task = None
        self._shutdown_event = None
        logger.info("Background token refresh stopped")

    async def _background_refresh_loop(self) -> None:
        """
        Background loop that refreshes all tokens periodically.

        Runs every _background_refresh_interval seconds and refreshes
        any tokens that are expiring soon.
        """
        logger.info("Background refresh loop started")

        # Initial refresh of all tokens
        await self._refresh_all_tokens()

        while True:
            try:
                # Wait for interval or shutdown signal
                if self._shutdown_event:
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self._background_refresh_interval
                        )
                        # Shutdown signaled
                        break
                    except asyncio.TimeoutError:
                        # Normal timeout, continue with refresh
                        pass

                await self._refresh_all_tokens()

            except asyncio.CancelledError:
                logger.debug("Background refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background refresh loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait a bit before retrying

        logger.info("Background refresh loop ended")

    async def _refresh_all_tokens(self) -> None:
        """
        Refresh all tokens that are expiring soon.

        Each token is refreshed independently to maintain separate
        access tokens for the entire pool.
        """
        if not self._refresh_tokens or len(self._refresh_tokens) <= 1:
            return

        logger.debug(f"Background refresh: checking {len(self._refresh_tokens)} tokens")
        refreshed = 0
        failed = 0

        for refresh_token in self._refresh_tokens:
            health = self._token_health.get(refresh_token)
            if not health:
                continue

            # Skip if token has valid access token that's not expiring soon
            if health.has_valid_access_token() and not health.is_expiring_soon(threshold_seconds=self._background_refresh_interval + 60):
                continue

            # Skip unhealthy tokens (in backoff)
            if not health.is_healthy():
                logger.debug(f"Skipping unhealthy token {health.masked_token}")
                continue

            try:
                await self._refresh_single_token(refresh_token)
                refreshed += 1
            except Exception as e:
                logger.warning(f"Background refresh failed for {health.masked_token}: {e}")
                health.record_failure()
                failed += 1

        if refreshed > 0 or failed > 0:
            logger.info(f"Background refresh complete: {refreshed} refreshed, {failed} failed")

    async def _refresh_single_token(self, refresh_token: str) -> None:
        """
        Refresh a single token and store its access token.

        Args:
            refresh_token: The refresh token to use
        """
        health = self._token_health.get(refresh_token)
        if not health:
            return

        # Temporarily set this as the current refresh token
        original_refresh_token = self._refresh_token
        self._refresh_token = refresh_token

        try:
            # Perform the refresh
            await self._refresh_token_request()

            # Store the access token in the health tracker
            if self._access_token and self._expires_at:
                health.record_success(self._access_token, self._expires_at)
                logger.debug(f"Refreshed token {health.masked_token}, expires: {self._expires_at.isoformat()}")

        finally:
            # Restore original refresh token
            self._refresh_token = original_refresh_token
    
    def _load_credentials_from_sqlite(self, db_path: str) -> None:
        """
        Loads credentials from kiro-cli SQLite database.
        
        The database contains an auth_kv table with key-value pairs:
        - 'codewhisperer:odic:token': JSON with access_token, refresh_token, expires_at, region
        - 'codewhisperer:odic:device-registration': JSON with client_id, client_secret
        
        Args:
            db_path: Path to SQLite database file
        """
        try:
            path = Path(db_path).expanduser()
            if not path.exists():
                logger.warning(f"SQLite database not found: {db_path}")
                return
            
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            
            # Load token data (try both kiro-cli and codewhisperer key formats)
            cursor.execute("SELECT value FROM auth_kv WHERE key = ?", ("kirocli:odic:token",))
            token_row = cursor.fetchone()
            if not token_row:
                cursor.execute("SELECT value FROM auth_kv WHERE key = ?", ("codewhisperer:odic:token",))
                token_row = cursor.fetchone()
            
            if token_row:
                token_data = json.loads(token_row[0])
                if token_data:
                    # Load token fields (using snake_case as in Rust struct)
                    if 'access_token' in token_data:
                        self._access_token = token_data['access_token']
                    if 'refresh_token' in token_data:
                        self._refresh_token = token_data['refresh_token']
                    if 'region' in token_data:
                        # Store SSO region for OIDC token refresh only
                        # IMPORTANT: CodeWhisperer API is only available in us-east-1,
                        # so we don't update _api_host and _q_host here.
                        # The SSO region (e.g., ap-southeast-1) is only used for OIDC token refresh.
                        self._sso_region = token_data['region']
                        logger.debug(f"SSO region from SQLite: {self._sso_region} (API stays at {self._region})")
                    
                    # Load scopes if available
                    if 'scopes' in token_data:
                        self._scopes = token_data['scopes']
                    
                    # Parse expires_at (RFC3339 format)
                    if 'expires_at' in token_data:
                        try:
                            expires_str = token_data['expires_at']
                            # Handle various ISO 8601 formats
                            if expires_str.endswith('Z'):
                                self._expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                            else:
                                self._expires_at = datetime.fromisoformat(expires_str)
                        except Exception as e:
                            logger.warning(f"Failed to parse expires_at from SQLite: {e}")
            
            # Load device registration (client_id, client_secret) - try both key formats
            cursor.execute("SELECT value FROM auth_kv WHERE key = ?", ("kirocli:odic:device-registration",))
            registration_row = cursor.fetchone()
            if not registration_row:
                cursor.execute("SELECT value FROM auth_kv WHERE key = ?", ("codewhisperer:odic:device-registration",))
                registration_row = cursor.fetchone()
            
            if registration_row:
                registration_data = json.loads(registration_row[0])
                if registration_data:
                    if 'client_id' in registration_data:
                        self._client_id = registration_data['client_id']
                    if 'client_secret' in registration_data:
                        self._client_secret = registration_data['client_secret']
                    # SSO region from registration (fallback if not in token data)
                    if 'region' in registration_data and not self._sso_region:
                        self._sso_region = registration_data['region']
                        logger.debug(f"SSO region from device-registration: {self._sso_region}")
            
            conn.close()
            logger.info(f"Credentials loaded from SQLite database: {db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error loading credentials: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in SQLite data: {e}")
        except Exception as e:
            logger.error(f"Error loading credentials from SQLite: {e}")
    
    def _load_credentials_from_file(self, file_path: str) -> None:
        """
        Loads credentials from a JSON file.
        
        Supported JSON fields (Kiro Desktop):
        - refreshToken: Refresh token
        - accessToken: Access token (if already available)
        - profileArn: Profile ARN
        - region: AWS region
        - expiresAt: Token expiration time (ISO 8601)
        
        Additional fields for AWS SSO OIDC (kiro-cli):
        - clientId: OAuth client ID
        - clientSecret: OAuth client secret
        
        Args:
            file_path: Path to JSON file
        """
        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                logger.warning(f"Credentials file not found: {file_path}")
                return
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load common data from file
            if 'refreshToken' in data:
                self._refresh_token = data['refreshToken']
            if 'accessToken' in data:
                self._access_token = data['accessToken']
            if 'profileArn' in data:
                self._profile_arn = data['profileArn']
            if 'region' in data:
                self._region = data['region']
                # Update URLs for new region
                self._refresh_url = get_kiro_refresh_url(self._region)
                self._api_host = get_kiro_api_host(self._region)
                self._q_host = get_kiro_q_host(self._region)
            
            # Load AWS SSO OIDC specific fields
            if 'clientId' in data:
                self._client_id = data['clientId']
            if 'clientSecret' in data:
                self._client_secret = data['clientSecret']
            
            # Parse expiresAt
            if 'expiresAt' in data:
                try:
                    expires_str = data['expiresAt']
                    # Support for different date formats
                    if expires_str.endswith('Z'):
                        self._expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    else:
                        self._expires_at = datetime.fromisoformat(expires_str)
                except Exception as e:
                    logger.warning(f"Failed to parse expiresAt: {e}")
            
            logger.info(f"Credentials loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading credentials from file: {e}")
    
    def _save_credentials_to_file(self) -> None:
        """
        Saves updated credentials to a JSON file.
        
        Updates the existing file while preserving other fields.
        """
        if not self._creds_file:
            return
        
        try:
            path = Path(self._creds_file).expanduser()
            
            # Read existing data
            existing_data = {}
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Update data
            existing_data['accessToken'] = self._access_token
            existing_data['refreshToken'] = self._refresh_token
            if self._expires_at:
                existing_data['expiresAt'] = self._expires_at.isoformat()
            if self._profile_arn:
                existing_data['profileArn'] = self._profile_arn
            
            # Save
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Credentials saved to {self._creds_file}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def is_token_expiring_soon(self) -> bool:
        """
        Checks if the token is expiring soon.
        
        Returns:
            True if the token expires within TOKEN_REFRESH_THRESHOLD seconds
            or if expiration time information is not available
        """
        if not self._expires_at:
            return True  # If no expiration info available, assume refresh is needed
        
        now = datetime.now(timezone.utc)
        threshold = now.timestamp() + TOKEN_REFRESH_THRESHOLD
        
        return self._expires_at.timestamp() <= threshold
    
    def is_token_expired(self) -> bool:
        """
        Checks if the token is actually expired (not just expiring soon).
        
        This is used for graceful degradation when refresh fails but
        the access token might still be valid for a short time.
        
        Returns:
            True if the token has already expired or if expiration time
            information is not available
        """
        if not self._expires_at:
            return True  # If no expiration info available, assume expired
        
        now = datetime.now(timezone.utc)
        return now >= self._expires_at
    
    async def _refresh_token_request(self) -> None:
        """
        Performs a token refresh request.
        
        Routes to appropriate refresh method based on auth type:
        - KIRO_DESKTOP: Uses Kiro Desktop Auth endpoint
        - AWS_SSO_OIDC: Uses AWS SSO OIDC endpoint
        
        Raises:
            ValueError: If refresh token is not set or response doesn't contain accessToken
            httpx.HTTPError: On HTTP request error
        """
        if self._auth_type == AuthType.AWS_SSO_OIDC:
            await self._refresh_token_aws_sso_oidc()
        else:
            await self._refresh_token_kiro_desktop()
    
    async def _refresh_token_kiro_desktop(self) -> None:
        """
        Refreshes token using Kiro Desktop Auth endpoint.
        
        Endpoint: https://prod.{region}.auth.desktop.kiro.dev/refreshToken
        Method: POST
        Content-Type: application/json
        Body: {"refreshToken": "..."}
        
        Raises:
            ValueError: If refresh token is not set or response doesn't contain accessToken
            httpx.HTTPError: On HTTP request error
        """
        if not self._refresh_token:
            raise ValueError("Refresh token is not set")
        
        logger.info("Refreshing Kiro token via Kiro Desktop Auth...")
        
        payload = {'refreshToken': self._refresh_token}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"KiroIDE-0.7.45-{self._fingerprint}",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self._refresh_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        new_access_token = data.get("accessToken")
        new_refresh_token = data.get("refreshToken")
        expires_in = data.get("expiresIn", 3600)
        new_profile_arn = data.get("profileArn")
        
        if not new_access_token:
            raise ValueError(f"Response does not contain accessToken: {data}")
        
        # Update data
        self._access_token = new_access_token
        if new_refresh_token:
            self._refresh_token = new_refresh_token
        if new_profile_arn:
            self._profile_arn = new_profile_arn
        
        # Calculate expiration time with buffer (minus 60 seconds)
        self._expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        self._expires_at = datetime.fromtimestamp(
            self._expires_at.timestamp() + expires_in - 60,
            tz=timezone.utc
        )
        
        logger.info(f"Token refreshed via Kiro Desktop Auth, expires: {self._expires_at.isoformat()}")

        # Record success for health tracking
        self._record_token_success()

        # Save to file
        self._save_credentials_to_file()
    
    async def _refresh_token_aws_sso_oidc(self) -> None:
        """
        Refreshes token using AWS SSO OIDC endpoint.
        
        Used by kiro-cli which authenticates via AWS IAM Identity Center.
        
        Strategy: Try with current in-memory token first. If it fails with 400
        (invalid_request - token was invalidated by kiro-cli re-login), reload
        credentials from SQLite and retry once.
        
        This approach handles both scenarios:
        1. Container successfully refreshed token (uses in-memory token)
        2. kiro-cli re-login invalidated token (reloads from SQLite on failure)
        
        Endpoint: https://oidc.{region}.amazonaws.com/token
        Method: POST
        Content-Type: application/x-www-form-urlencoded
        Body: grant_type=refresh_token&client_id=...&client_secret=...&refresh_token=...
        
        Raises:
            ValueError: If required credentials are not set
            httpx.HTTPError: On HTTP request error
        """
        try:
            await self._do_aws_sso_oidc_refresh()
        except httpx.HTTPStatusError as e:
            # 400 = invalid_request, likely stale token after kiro-cli re-login
            if e.response.status_code == 400 and self._sqlite_db:
                logger.warning("Token refresh failed with 400, reloading credentials from SQLite and retrying...")
                self._load_credentials_from_sqlite(self._sqlite_db)
                await self._do_aws_sso_oidc_refresh()
            else:
                raise
    
    async def _do_aws_sso_oidc_refresh(self) -> None:
        """
        Performs the actual AWS SSO OIDC token refresh.
        
        This is the internal implementation called by _refresh_token_aws_sso_oidc().
        It performs a single refresh attempt with current in-memory credentials.
        
        Raises:
            ValueError: If required credentials are not set
            httpx.HTTPStatusError: On HTTP error (including 400 for invalid token)
        """
        if not self._refresh_token:
            raise ValueError("Refresh token is not set")
        if not self._client_id:
            raise ValueError("Client ID is not set (required for AWS SSO OIDC)")
        if not self._client_secret:
            raise ValueError("Client secret is not set (required for AWS SSO OIDC)")
        
        logger.info("Refreshing Kiro token via AWS SSO OIDC...")
        
        # AWS SSO OIDC uses form-urlencoded data
        # Use SSO region for OIDC endpoint (may differ from API region)
        sso_region = self._sso_region or self._region
        url = get_aws_sso_oidc_url(sso_region)
        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }
        
        # Note: scope parameter is NOT sent during refresh per OAuth 2.0 RFC 6749 Section 6
        # AWS SSO OIDC uses the originally granted scopes automatically
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        # Log request details (without secrets) for debugging
        logger.debug(f"AWS SSO OIDC refresh request: url={url}, sso_region={sso_region}, "
                     f"api_region={self._region}, client_id={self._client_id[:8]}...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, data=data, headers=headers)
            
            # Log response details for debugging (especially on errors)
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"AWS SSO OIDC refresh failed: status={response.status_code}, "
                             f"body={error_body}")
                # Try to parse AWS error for more details
                try:
                    error_json = response.json()
                    error_code = error_json.get("error", "unknown")
                    error_desc = error_json.get("error_description", "no description")
                    logger.error(f"AWS SSO OIDC error details: error={error_code}, "
                                 f"description={error_desc}")
                except Exception:
                    pass  # Body wasn't JSON, already logged as text
                response.raise_for_status()
            
            result = response.json()
        
        new_access_token = result.get("accessToken")
        new_refresh_token = result.get("refreshToken")
        expires_in = result.get("expiresIn", 3600)
        
        if not new_access_token:
            raise ValueError(f"AWS SSO OIDC response does not contain accessToken: {result}")
        
        # Update data
        self._access_token = new_access_token
        if new_refresh_token:
            self._refresh_token = new_refresh_token
        
        # Calculate expiration time with buffer (minus 60 seconds)
        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
        
        logger.info(f"Token refreshed via AWS SSO OIDC, expires: {self._expires_at.isoformat()}")

        # Record success for health tracking
        self._record_token_success()

        # Save to file
        self._save_credentials_to_file()
    
    async def get_access_token(self) -> str:
        """
        Returns a valid access_token, refreshing it if necessary.

        Thread-safe method using asyncio.Lock.
        Automatically refreshes the token if it has expired or is about to expire.

        Token Rotation Strategy (for multiple tokens):
        1. Pool check: First tries to get a pre-refreshed token from the pool
        2. Round-robin: Each request uses the next healthy token
        3. Fallback: On failure, automatically tries next healthy token
        4. Health tracking: Failed tokens are temporarily avoided (exponential backoff)

        For SQLite mode (kiro-cli): implements graceful degradation when refresh fails.
        If kiro-cli has been running and refreshing tokens in memory (without persisting
        to SQLite), the refresh_token in SQLite becomes stale. In this case, we fall back
        to using the access_token directly until it actually expires.

        Returns:
            Valid access token

        Raises:
            ValueError: If unable to obtain access token
        """
        async with self._lock:
            self._total_requests += 1

            # Token is valid and not expiring soon - just return it
            if self._access_token and not self.is_token_expiring_soon():
                return self._access_token

            # For multiple tokens: check if any token in the pool has a valid access token
            # This leverages background refresh to avoid on-demand refresh latency
            if len(self._refresh_tokens) > 1:
                for refresh_token in self._refresh_tokens:
                    health = self._token_health.get(refresh_token)
                    if health and health.has_valid_access_token() and not health.is_expiring_soon():
                        # Use the pre-refreshed token from the pool
                        self._access_token = health.access_token
                        self._expires_at = health.expires_at
                        self._refresh_token = refresh_token
                        logger.debug(f"Using pre-refreshed token from pool: {health.masked_token}")
                        return self._access_token

            # SQLite mode: reload credentials first, kiro-cli might have updated them
            if self._sqlite_db and self.is_token_expiring_soon():
                logger.debug("SQLite mode: reloading credentials before refresh attempt")
                self._load_credentials_from_sqlite(self._sqlite_db)
                # Check if reloaded token is now valid
                if self._access_token and not self.is_token_expiring_soon():
                    logger.debug("SQLite reload provided fresh token, no refresh needed")
                    return self._access_token

            # For multiple tokens: select next healthy token using round-robin
            if len(self._refresh_tokens) > 1:
                next_token = self._get_next_healthy_token()
                if next_token:
                    self._refresh_token = next_token

            # Try to refresh with rotation fallback
            last_error: Optional[Exception] = None
            tokens_tried = 0
            max_attempts = len(self._refresh_tokens) if self._refresh_tokens else 1

            while tokens_tried < max_attempts:
                tokens_tried += 1
                try:
                    await self._refresh_token_request()
                    # Success - return the token
                    if not self._access_token:
                        raise ValueError("Failed to obtain access token")
                    return self._access_token

                except httpx.HTTPStatusError as e:
                    last_error = e

                    # Graceful degradation for SQLite mode when refresh fails
                    if e.response.status_code == 400 and self._sqlite_db:
                        logger.warning(
                            "Token refresh failed with 400 after SQLite reload. "
                            "This may happen if kiro-cli refreshed tokens in memory without persisting."
                        )
                        # Check if access_token is still usable
                        if self._access_token and not self.is_token_expired():
                            logger.warning(
                                "Using existing access_token until it expires. "
                                "Run 'kiro-cli login' when convenient to refresh credentials."
                            )
                            return self._access_token

                    # Try rotating to next token (for multi-token setup)
                    if len(self._refresh_tokens) > 1:
                        next_token = self._rotate_to_next_token()
                        if next_token:
                            logger.info(f"Retrying with next token (attempt {tokens_tried + 1}/{max_attempts})")
                            continue

                    # No more tokens to try or single token mode
                    break

                except Exception as e:
                    last_error = e
                    # For non-HTTP errors, try rotating if we have multiple tokens
                    if len(self._refresh_tokens) > 1:
                        next_token = self._rotate_to_next_token()
                        if next_token:
                            logger.info(f"Retrying with next token after error: {e}")
                            continue
                    break

            # All tokens failed
            if last_error:
                if isinstance(last_error, httpx.HTTPStatusError) and last_error.response.status_code == 400:
                    raise ValueError(
                        "Token expired and refresh failed for all tokens. "
                        "Please check your refresh tokens or run 'kiro-cli login'."
                    )
                raise last_error

            if not self._access_token:
                raise ValueError("Failed to obtain access token")

            return self._access_token
    
    async def force_refresh(self) -> str:
        """
        Forces a token refresh.

        Used when receiving a 403 error from the API.
        Supports token rotation - will try all available tokens on failure.

        Returns:
            New access token

        Raises:
            ValueError: If all tokens fail to refresh
        """
        async with self._lock:
            last_error: Optional[Exception] = None
            tokens_tried = 0
            max_attempts = len(self._refresh_tokens) if self._refresh_tokens else 1

            while tokens_tried < max_attempts:
                tokens_tried += 1
                try:
                    await self._refresh_token_request()
                    return self._access_token
                except Exception as e:
                    last_error = e
                    logger.warning(f"Force refresh failed for current token: {e}")

                    # Try rotating to next token
                    if len(self._refresh_tokens) > 1:
                        next_token = self._rotate_to_next_token()
                        if next_token:
                            logger.info(f"Force refresh: trying next token (attempt {tokens_tried + 1}/{max_attempts})")
                            continue
                    break

            if last_error:
                raise last_error
            return self._access_token
    
    @property
    def profile_arn(self) -> Optional[str]:
        """AWS CodeWhisperer profile ARN."""
        return self._profile_arn
    
    @property
    def region(self) -> str:
        """AWS region."""
        return self._region
    
    @property
    def api_host(self) -> str:
        """API host for the current region."""
        return self._api_host
    
    @property
    def q_host(self) -> str:
        """Q API host for the current region."""
        return self._q_host
    
    @property
    def fingerprint(self) -> str:
        """Unique machine fingerprint."""
        return self._fingerprint
    
    @property
    def auth_type(self) -> AuthType:
        """Authentication type (KIRO_DESKTOP or AWS_SSO_OIDC)."""
        return self._auth_type