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
from contextvars import ContextVar
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

try:
    import certifi
except ImportError:
    certifi = None

from kiro.config import (
    TOKEN_REFRESH_THRESHOLD,
    get_kiro_refresh_url,
    get_kiro_api_host,
    get_kiro_q_host,
    get_aws_sso_oidc_url,
)
from kiro.utils import get_machine_fingerprint


# Supported SQLite token keys (searched in priority order)
SQLITE_TOKEN_KEYS = [
    "kirocli:social:token",      # Social login (Google, GitHub, Microsoft, etc.)
    "kirocli:odic:token",        # AWS SSO OIDC (kiro-cli corporate)
    "codewhisperer:odic:token",  # Legacy AWS SSO OIDC
]

# Device registration keys (for AWS SSO OIDC only)
SQLITE_REGISTRATION_KEYS = [
    "kirocli:odic:device-registration",
    "codewhisperer:odic:device-registration",
]

MONGODB_TOKEN_KEYS = SQLITE_TOKEN_KEYS

# Default quarantine window for failing accounts in round-robin pool.
DEFAULT_ACCOUNT_QUARANTINE_SECONDS = 60


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


class KiroAuthManager:
    """
    Manages the token lifecycle for accessing Kiro API.
    
    Supports:
    - Loading credentials from .env or JSON file
    - Automatic token refresh on expiration
    - Expiration time validation (expiresAt)
    - Saving updated tokens to file
    - Both Kiro Desktop Auth and AWS SSO OIDC (kiro-cli) authentication
    
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
        
        >>> # AWS SSO OIDC (kiro-cli) - auto-detected from credentials file
        >>> auth_manager = KiroAuthManager(
        ...     creds_file="~/.aws/sso/cache/your-cache.json"
        ... )
        >>> token = await auth_manager.get_access_token()
    """
    
    def __init__(
        self,
        refresh_token: Optional[str] = None,
        profile_arn: Optional[str] = None,
        region: str = "us-east-1",
        creds_file: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        sqlite_db: Optional[str] = None,
        auth_source: str = "auto",
        mongodb_uri: Optional[str] = None,
        mongodb_db_name: str = "fproxy",
        mongodb_collection: str = "auth_kv",
    ):
        """
        Initializes the authentication manager.
        
        Args:
            refresh_token: Refresh token for obtaining access token
            profile_arn: AWS CodeWhisperer profile ARN
            region: AWS region (default: us-east-1)
            creds_file: Path to JSON file with credentials (optional)
            client_id: OAuth client ID (for AWS SSO OIDC, optional)
            client_secret: OAuth client secret (for AWS SSO OIDC, optional)
            sqlite_db: Path to kiro-cli SQLite database (optional)
                       Default location: ~/.local/share/kiro-cli/data.sqlite3
            auth_source: Credential source selector (auto/sqlite/file/env/mongodb)
            mongodb_uri: MongoDB URI for auth_kv credential source
            mongodb_db_name: MongoDB database name for auth_kv source
            mongodb_collection: MongoDB collection name for auth key-value data
        """
        self._refresh_token = refresh_token
        self._profile_arn = profile_arn
        self._region = region
        self._creds_file = creds_file
        self._sqlite_db = sqlite_db
        self._auth_source = auth_source
        self._mongodb_uri = mongodb_uri
        self._mongodb_db_name = mongodb_db_name
        self._mongodb_collection = mongodb_collection
        self._mongodb_client: Optional[Any] = None
        
        # AWS SSO OIDC specific fields
        self._client_id: Optional[str] = client_id
        self._client_secret: Optional[str] = client_secret
        self._scopes: Optional[list] = None  # OAuth scopes for AWS SSO OIDC
        self._sso_region: Optional[str] = None  # SSO region for OIDC token refresh (may differ from API region)
        
        # Enterprise Kiro IDE specific fields
        self._client_id_hash: Optional[str] = None  # clientIdHash from Enterprise Kiro IDE
        
        # Track which SQLite key we loaded credentials from (for saving back to correct location)
        self._sqlite_token_key: Optional[str] = None

        # Multi-account pool loaded from SQLite (single-account mode keeps this empty).
        self._account_pool: List[Dict[str, Any]] = []
        self._round_robin_index: int = -1
        self._account_quarantine_seconds: int = DEFAULT_ACCOUNT_QUARANTINE_SECONDS
        self._request_account_key: ContextVar[Optional[str]] = ContextVar("request_account_key", default=None)
        
        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
        # Auth type will be determined after loading credentials
        self._auth_type: AuthType = AuthType.KIRO_DESKTOP
        
        # Dynamic URLs based on region
        self._refresh_url = get_kiro_refresh_url(region)
        self._api_host = get_kiro_api_host(region)
        self._q_host = get_kiro_q_host(region)
        
        # Log initialized endpoints for diagnostics (helps with DNS issues like #58)
        logger.info(f"Auth manager initialized: region={region}, api_host={self._api_host}, q_host={self._q_host}")
        
        # Fingerprint for User-Agent
        self._fingerprint = get_machine_fingerprint()
        
        # Load credentials from configured source.
        normalized_source = (self._auth_source or "auto").strip().lower()
        if normalized_source == "mongodb":
            self._load_credentials_from_mongodb()
        elif normalized_source == "sqlite" and sqlite_db:
            self._load_credentials_from_sqlite(sqlite_db)
        elif normalized_source == "file" and creds_file:
            self._load_credentials_from_file(creds_file)
        elif normalized_source == "env":
            logger.info("Using environment credential source for Kiro auth")
        else:
            # Auto mode preserves existing priority: sqlite > file > env.
            if sqlite_db:
                self._load_credentials_from_sqlite(sqlite_db)
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

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse RFC3339/ISO datetime values from credential payloads."""
        if not isinstance(value, str) or not value:
            return None

        try:
            if value.endswith('Z'):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _token_key_prefix(base_key: str) -> str:
        """Build key prefix used for multi-account entries in auth_kv."""
        return f"{base_key}:"

    @staticmethod
    def _normalize_suffix(key: str, prefix: str) -> str:
        """Extract suffix from key for matching registration entries."""
        if key == prefix:
            return ""
        if key.startswith(f"{prefix}:"):
            return key[len(prefix):]
        return ""

    def _iter_auth_kv_rows(self, cursor: sqlite3.Cursor, base_keys: List[str]) -> List[tuple[str, str]]:
        """
        Read all auth_kv rows for base keys, including multi-account suffix keys.

        Args:
            cursor: SQLite cursor.
            base_keys: Base auth_kv keys.

        Returns:
            Ordered list of (key, value) pairs.
        """
        rows: List[tuple[str, str]] = []
        seen: set[str] = set()

        for base_key in base_keys:
            cursor.execute(
                "SELECT key, value FROM auth_kv WHERE key = ? OR key LIKE ? ORDER BY key ASC",
                (base_key, f"{self._token_key_prefix(base_key)}%"),
            )
            for key, value in cursor.fetchall():
                if key in seen:
                    continue
                seen.add(key)
                rows.append((key, value))

        return rows

    @staticmethod
    def _iter_mongodb_auth_docs(collection: Any, base_keys: List[str]) -> List[tuple[str, Dict[str, Any]]]:
        """
        Read auth_kv documents from MongoDB for base and suffixed keys.

        Args:
            collection: MongoDB collection object.
            base_keys: Base token keys.

        Returns:
            Ordered list of (key, token_payload) pairs.
        """
        rows: List[tuple[str, Dict[str, Any]]] = []
        seen: set[str] = set()

        for base_key in base_keys:
            cursor = collection.find(
                {
                    "$or": [
                        {"key": base_key},
                        {"key": {"$regex": f"^{base_key}:"}},
                    ]
                },
                {"_id": 0, "key": 1, "value": 1},
            ).sort("key", 1)

            for doc in cursor:
                key = doc.get("key")
                value = doc.get("value")
                if not isinstance(key, str) or key in seen:
                    continue
                if not isinstance(value, dict):
                    continue
                seen.add(key)
                rows.append((key, value))

        return rows

    def _registration_candidates_for_token_key(self, token_key: str) -> List[str]:
        """
        Build registration-key candidates for a token key.

        Args:
            token_key: Token key from auth_kv.

        Returns:
            Candidate registration keys in lookup priority order.
        """
        if token_key.startswith("kirocli:social:token"):
            return []

        candidates: List[str] = []
        if token_key.startswith("kirocli:odic:token"):
            suffix = self._normalize_suffix(token_key, "kirocli:odic:token")
            if suffix:
                candidates.append(f"kirocli:odic:device-registration{suffix}")
            candidates.append("kirocli:odic:device-registration")
            candidates.append("codewhisperer:odic:device-registration")
        elif token_key.startswith("codewhisperer:odic:token"):
            suffix = self._normalize_suffix(token_key, "codewhisperer:odic:token")
            if suffix:
                candidates.append(f"codewhisperer:odic:device-registration{suffix}")
            candidates.append("codewhisperer:odic:device-registration")
            candidates.append("kirocli:odic:device-registration")

        return candidates

    def _build_account_from_sqlite_row(
        self,
        token_key: str,
        token_data: Dict[str, Any],
        registration_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build an in-memory account object from SQLite token and registration payloads.

        Args:
            token_key: auth_kv token key.
            token_data: Parsed token payload JSON.
            registration_map: Registration payloads keyed by auth_kv key.

        Returns:
            Account dictionary used by round-robin selection.
        """
        registration_data: Dict[str, Any] = {}
        for reg_key in self._registration_candidates_for_token_key(token_key):
            candidate = registration_map.get(reg_key)
            if candidate:
                registration_data = candidate
                break

        expires_at = self._parse_datetime(token_data.get("expires_at"))
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        profile_arn = token_data.get("profile_arn")
        sso_region = token_data.get("region")
        scopes = token_data.get("scopes")
        provider = token_data.get("provider")
        client_id = registration_data.get("client_id")
        client_secret = registration_data.get("client_secret")

        auth_type = AuthType.AWS_SSO_OIDC if client_id and client_secret else AuthType.KIRO_DESKTOP

        return {
            "key": token_key,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "profile_arn": profile_arn,
            "expires_at": expires_at,
            "sso_region": sso_region,
            "scopes": scopes,
            "provider": provider,
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_type": auth_type,
            "quarantine_until": None,
        }

    def _set_active_account(self, account: Dict[str, Any]) -> None:
        """
        Copy selected account data into active fields.

        Args:
            account: Account dictionary.
        """
        self._sqlite_token_key = account.get("key")
        self._access_token = account.get("access_token")
        self._refresh_token = account.get("refresh_token")
        self._profile_arn = account.get("profile_arn")
        self._expires_at = account.get("expires_at")
        self._sso_region = account.get("sso_region")
        self._scopes = account.get("scopes")
        self._client_id = account.get("client_id")
        self._client_secret = account.get("client_secret")
        self._auth_type = account.get("auth_type", AuthType.KIRO_DESKTOP)

    def _sync_active_account_state(self) -> None:
        """Persist active scalar fields back into the current account object."""
        if not self._sqlite_token_key:
            return

        for account in self._account_pool:
            if account.get("key") != self._sqlite_token_key:
                continue
            account["access_token"] = self._access_token
            account["refresh_token"] = self._refresh_token
            account["profile_arn"] = self._profile_arn
            account["expires_at"] = self._expires_at
            account["sso_region"] = self._sso_region
            account["scopes"] = self._scopes
            account["client_id"] = self._client_id
            account["client_secret"] = self._client_secret
            account["auth_type"] = self._auth_type
            break

    def _find_account_by_key(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find an account in the pool by SQLite key."""
        if not key:
            return None
        for account in self._account_pool:
            if account.get("key") == key:
                return account
        return None

    def _is_account_eligible(self, account: Dict[str, Any]) -> bool:
        """Check whether account is eligible for round-robin selection."""
        quarantine_until = account.get("quarantine_until")
        if quarantine_until is None:
            return True
        return quarantine_until <= datetime.now(timezone.utc)

    def _select_next_account_locked(self) -> Optional[Dict[str, Any]]:
        """
        Select next eligible account in deterministic round-robin order.

        Returns:
            Selected account dictionary or None if account pool is empty.
        """
        if not self._account_pool:
            return None

        total = len(self._account_pool)
        for _ in range(total):
            self._round_robin_index = (self._round_robin_index + 1) % total
            candidate = self._account_pool[self._round_robin_index]
            if self._is_account_eligible(candidate):
                return candidate

        for account in self._account_pool:
            account["quarantine_until"] = None
        self._round_robin_index = (self._round_robin_index + 1) % total
        return self._account_pool[self._round_robin_index]

    def _get_or_select_request_account_locked(self, force_next: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get request-scoped account or select next one in round-robin.

        Args:
            force_next: If True, always select a new account.

        Returns:
            Selected account or None when no pool exists.
        """
        if not self._account_pool:
            return None

        if not force_next:
            current_key = self._request_account_key.get()
            current_account = self._find_account_by_key(current_key)
            if current_account and self._is_account_eligible(current_account):
                return current_account

        selected = self._select_next_account_locked()
        if selected:
            self._request_account_key.set(selected.get("key"))
        return selected

    def _mark_current_account_unhealthy_locked(self) -> None:
        """Temporarily quarantine current request account after refresh failure."""
        current_key = self._request_account_key.get()
        account = self._find_account_by_key(current_key)
        if not account:
            return

        account["quarantine_until"] = datetime.now(timezone.utc) + timedelta(
            seconds=self._account_quarantine_seconds
        )
        logger.warning(
            "Account key %s quarantined for %ss after auth failure",
            current_key,
            self._account_quarantine_seconds,
        )

    def _mark_current_account_healthy_locked(self) -> None:
        """Clear quarantine status for the current request account after success."""
        current_key = self._request_account_key.get()
        account = self._find_account_by_key(current_key)
        if not account:
            return
        account["quarantine_until"] = None

    def clear_request_account(self) -> None:
        """Clear request-scoped selected account key."""
        self._request_account_key.set(None)

    async def get_profile_arn_for_request(self) -> Optional[str]:
        """
        Resolve profile ARN for current request account.

        Returns:
            Profile ARN for request-selected account, or fallback profile ARN.
        """
        async with self._lock:
            if self._account_pool:
                account = self._get_or_select_request_account_locked()
                if account:
                    self._set_active_account(account)
            return self._profile_arn

    def _reload_active_account_from_sqlite_locked(self) -> None:
        """
        Reload currently selected account from SQLite.

        This pulls fresh values for only the active account key.
        """
        if not self._sqlite_db or not self._sqlite_token_key:
            return

        path = Path(self._sqlite_db).expanduser()
        if not path.exists():
            return

        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM auth_kv WHERE key = ?", (self._sqlite_token_key,))
            token_row = cursor.fetchone()
            if not token_row:
                return

            token_data = json.loads(token_row[0])
            registration_rows = self._iter_auth_kv_rows(cursor, SQLITE_REGISTRATION_KEYS)
            registration_map: Dict[str, Dict[str, Any]] = {}
            for reg_key, reg_value in registration_rows:
                try:
                    registration_map[reg_key] = json.loads(reg_value)
                except json.JSONDecodeError:
                    continue

            refreshed_account = self._build_account_from_sqlite_row(
                self._sqlite_token_key,
                token_data,
                registration_map,
            )
            for idx, account in enumerate(self._account_pool):
                if account.get("key") == self._sqlite_token_key:
                    refreshed_account["quarantine_until"] = account.get("quarantine_until")
                    self._account_pool[idx] = refreshed_account
                    self._set_active_account(refreshed_account)
                    return
        finally:
            conn.close()

    def _get_mongodb_collection(self) -> Optional[Any]:
        """
        Get MongoDB auth collection.

        Returns:
            MongoDB collection object or None when unavailable.
        """
        if not self._mongodb_uri:
            return None
        if MongoClient is None:
            logger.warning("pymongo is not installed; MongoDB auth source is unavailable")
            return None

        try:
            if self._mongodb_client is None:
                client_kwargs: Dict[str, Any] = {"serverSelectionTimeoutMS": 5000}
                if certifi is not None:
                    client_kwargs["tlsCAFile"] = certifi.where()
                else:
                    logger.warning("certifi is not installed; MongoDB TLS may fail on some systems")

                self._mongodb_client = MongoClient(self._mongodb_uri, **client_kwargs)

            return self._mongodb_client[self._mongodb_db_name][self._mongodb_collection]
        except Exception as error:
            logger.error(f"Failed to initialize MongoDB auth collection: {error}")
            return None

    def _load_credentials_from_mongodb(self) -> None:
        """
        Load credentials from MongoDB auth_kv collection.

        Document format:
            {"key": "kirocli:social:token", "value": { ...token payload... }}
        """
        collection = self._get_mongodb_collection()
        if collection is None:
            return

        try:
            token_docs = self._iter_mongodb_auth_docs(collection, MONGODB_TOKEN_KEYS)
        except Exception as error:
            logger.error(f"Failed to query MongoDB auth documents: {error}")
            return

        parsed_accounts: List[Dict[str, Any]] = []
        registration_map: Dict[str, Dict[str, Any]] = {}
        for token_key, token_value in token_docs:
            account = self._build_account_from_sqlite_row(token_key, token_value, registration_map)
            if not account.get("refresh_token"):
                logger.warning(f"Skipping MongoDB auth key {token_key}: missing refresh_token")
                continue
            parsed_accounts.append(account)

        if not parsed_accounts:
            logger.warning("No valid credentials loaded from MongoDB auth_kv collection")
            return

        self._account_pool = parsed_accounts
        self._round_robin_index = -1
        self._set_active_account(self._account_pool[0])
        logger.info(
            f"Loaded {len(self._account_pool)} account(s) from MongoDB collection: "
            f"{self._mongodb_db_name}.{self._mongodb_collection}"
        )

    def _reload_active_account_from_mongodb_locked(self) -> None:
        """Reload active account payload from MongoDB by key."""
        if not self._sqlite_token_key:
            return

        collection = self._get_mongodb_collection()
        if collection is None:
            return

        try:
            doc = collection.find_one({"key": self._sqlite_token_key}, {"_id": 0, "value": 1})
        except Exception as error:
            logger.warning(f"Failed to reload MongoDB auth key {self._sqlite_token_key}: {error}")
            return

        if not doc or not isinstance(doc.get("value"), dict):
            return

        refreshed_account = self._build_account_from_sqlite_row(
            self._sqlite_token_key,
            doc["value"],
            {},
        )
        for idx, account in enumerate(self._account_pool):
            if account.get("key") == self._sqlite_token_key:
                refreshed_account["quarantine_until"] = account.get("quarantine_until")
                self._account_pool[idx] = refreshed_account
                self._set_active_account(refreshed_account)
                return

    def _save_credentials_to_mongodb(self) -> None:
        """Persist active account credentials back to MongoDB auth_kv."""
        collection = self._get_mongodb_collection()
        if collection is None:
            return

        candidate_keys: List[str] = []
        if self._sqlite_token_key:
            candidate_keys.append(self._sqlite_token_key)

        current_request_key = self._request_account_key.get()
        if current_request_key and current_request_key not in candidate_keys:
            candidate_keys.append(current_request_key)

        for account in self._account_pool:
            account_key = account.get("key")
            if account_key and account_key not in candidate_keys:
                candidate_keys.append(account_key)

        for fallback_key in MONGODB_TOKEN_KEYS:
            if fallback_key not in candidate_keys:
                candidate_keys.append(fallback_key)

        for key in candidate_keys:
            doc = collection.find_one({"key": key}, {"_id": 0, "value": 1})
            if not doc or not isinstance(doc.get("value"), dict):
                continue

            existing_data = dict(doc["value"])
            existing_data["access_token"] = self._access_token
            existing_data["refresh_token"] = self._refresh_token
            existing_data["expires_at"] = self._expires_at.isoformat() if self._expires_at else None
            existing_data["region"] = self._sso_region or self._region
            if self._scopes:
                existing_data["scopes"] = self._scopes
            if self._profile_arn:
                existing_data["profile_arn"] = self._profile_arn

            result = collection.update_one(
                {"key": key},
                {"$set": {"value": existing_data}},
                upsert=False,
            )
            if result.modified_count > 0 or result.matched_count > 0:
                self._sqlite_token_key = key
                self._sync_active_account_state()
                logger.debug(f"Credentials saved to MongoDB auth key: {key}")
                return

        logger.warning("Failed to save credentials to MongoDB: no matching keys found")
    
    def _load_credentials_from_sqlite(self, db_path: str) -> None:
        """
        Loads credentials from kiro-cli SQLite database.
        
        The database contains an auth_kv table with key-value pairs.
        Supports multiple authentication types:
        
        Token keys (searched in priority order):
        - 'kirocli:social:token': Social login (Google, GitHub, etc.)
        - 'kirocli:odic:token': AWS SSO OIDC (kiro-cli corporate)
        - 'codewhisperer:odic:token': Legacy AWS SSO OIDC
        
        Device registration keys (for AWS SSO OIDC only):
        - 'kirocli:odic:device-registration': Client ID and secret
        - 'codewhisperer:odic:device-registration': Legacy format
        
        The method remembers which key was used for loading, so credentials
        can be saved back to the correct location after refresh.
        
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

            registration_rows = self._iter_auth_kv_rows(cursor, SQLITE_REGISTRATION_KEYS)
            registration_map: Dict[str, Dict[str, Any]] = {}
            for reg_key, reg_value in registration_rows:
                try:
                    registration_map[reg_key] = json.loads(reg_value)
                except json.JSONDecodeError as reg_error:
                    logger.warning(f"Invalid registration JSON in key {reg_key}: {reg_error}")

            token_rows = self._iter_auth_kv_rows(cursor, SQLITE_TOKEN_KEYS)
            parsed_accounts: List[Dict[str, Any]] = []

            for token_key, token_value in token_rows:
                try:
                    token_data = json.loads(token_value)
                except json.JSONDecodeError as parse_error:
                    logger.warning(f"Invalid token JSON in key {token_key}: {parse_error}")
                    continue

                if not isinstance(token_data, dict):
                    logger.warning(f"Unexpected token payload type for key {token_key}: {type(token_data)}")
                    continue

                account = self._build_account_from_sqlite_row(token_key, token_data, registration_map)
                if not account.get("refresh_token"):
                    logger.warning(f"Skipping SQLite key {token_key}: missing refresh_token")
                    continue
                parsed_accounts.append(account)

            conn.close()

            if parsed_accounts:
                self._account_pool = parsed_accounts
                self._round_robin_index = -1
                first_account = self._account_pool[0]
                self._set_active_account(first_account)
                logger.info(
                    f"Loaded {len(self._account_pool)} account(s) from SQLite database: {db_path}"
                )
            else:
                logger.warning(f"No valid credentials found in SQLite database: {db_path}")
            
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
        
        For Enterprise Kiro IDE:
        - clientIdHash: Hash of client ID (Enterprise Kiro IDE)
        - When clientIdHash is present, automatically loads clientId and clientSecret
          from ~/.aws/sso/cache/{clientIdHash}.json (device registration file)
        
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
                logger.info(f"Region updated from credentials file: region={self._region}, api_host={self._api_host}, q_host={self._q_host}")
            
            # Load clientIdHash and device registration for Enterprise Kiro IDE
            if 'clientIdHash' in data:
                self._client_id_hash = data['clientIdHash']
                if isinstance(self._client_id_hash, str) and self._client_id_hash:
                    self._load_enterprise_device_registration(self._client_id_hash)
            
            # Load AWS SSO OIDC specific fields (if directly in credentials file)
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
    
    def _load_enterprise_device_registration(self, client_id_hash: str) -> None:
        """
        Loads clientId and clientSecret from Enterprise Kiro IDE device registration file.
        
        Enterprise Kiro IDE uses AWS SSO OIDC authentication. Device registration is stored at:
        ~/.aws/sso/cache/{clientIdHash}.json
        
        Args:
            client_id_hash: Client ID hash used to locate the device registration file
        """
        try:
            device_reg_path = Path.home() / ".aws" / "sso" / "cache" / f"{client_id_hash}.json"
            
            if not device_reg_path.exists():
                logger.warning(f"Enterprise device registration file not found: {device_reg_path}")
                return
            
            with open(device_reg_path, 'r', encoding='utf-8') as f:
                device_data = json.load(f)
            
            if 'clientId' in device_data:
                self._client_id = device_data['clientId']
            
            if 'clientSecret' in device_data:
                self._client_secret = device_data['clientSecret']
            
            logger.info(f"Enterprise device registration loaded from {device_reg_path}")
            
        except Exception as e:
            logger.error(f"Error loading enterprise device registration: {e}")
    
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
    
    def _save_credentials_to_sqlite(self) -> None:
        """
        Saves updated credentials back to SQLite database.
        
        This ensures that tokens refreshed by the gateway are persisted
        and available after gateway restart or for other processes reading
        the same SQLite database.
        
        Strategy:
        1. If we know which key we loaded from (_sqlite_token_key), save to that key
        2. If that fails or key is unknown, try all supported keys as fallback
        
        This approach ensures credentials are saved to the correct location
        regardless of authentication type (social login, AWS SSO OIDC, legacy).
        
        Updates the auth_kv table with fresh access_token, refresh_token,
        and expires_at values after successful token refresh.
        """
        if not self._sqlite_db:
            return
        
        try:
            path = Path(self._sqlite_db).expanduser()
            if not path.exists():
                logger.warning(f"SQLite database not found for writing: {self._sqlite_db}")
                return
            
            # Use timeout to avoid blocking if database is locked
            conn = sqlite3.connect(str(path), timeout=5.0)
            cursor = conn.cursor()
            
            candidate_keys: List[str] = []
            if self._sqlite_token_key:
                candidate_keys.append(self._sqlite_token_key)

            current_request_key = self._request_account_key.get()
            if current_request_key and current_request_key not in candidate_keys:
                candidate_keys.append(current_request_key)

            for account in self._account_pool:
                account_key = account.get("key")
                if account_key and account_key not in candidate_keys:
                    candidate_keys.append(account_key)

            for fallback_key in SQLITE_TOKEN_KEYS:
                if fallback_key not in candidate_keys:
                    candidate_keys.append(fallback_key)

            for key in candidate_keys:
                cursor.execute("SELECT value FROM auth_kv WHERE key = ?", (key,))
                row = cursor.fetchone()
                if not row:
                    continue

                try:
                    existing_data = json.loads(row[0])
                    if not isinstance(existing_data, dict):
                        existing_data = {}
                except json.JSONDecodeError:
                    existing_data = {}

                existing_data["access_token"] = self._access_token
                existing_data["refresh_token"] = self._refresh_token
                existing_data["expires_at"] = self._expires_at.isoformat() if self._expires_at else None
                existing_data["region"] = self._sso_region or self._region
                if self._scopes:
                    existing_data["scopes"] = self._scopes
                if self._profile_arn:
                    existing_data["profile_arn"] = self._profile_arn

                cursor.execute(
                    "UPDATE auth_kv SET value = ? WHERE key = ?",
                    (json.dumps(existing_data), key),
                )
                if cursor.rowcount > 0:
                    conn.commit()
                    conn.close()
                    self._sqlite_token_key = key
                    self._sync_active_account_state()
                    logger.debug(f"Credentials saved to SQLite key: {key}")
                    return

            conn.close()
            logger.warning("Failed to save credentials to SQLite: no matching keys found")
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error saving credentials: {e}")
        except Exception as e:
            logger.error(f"Error saving credentials to SQLite: {e}")
    
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
        
        # Save refreshed credentials to active configured source.
        if self._auth_source == "mongodb":
            self._save_credentials_to_mongodb()
        elif self._sqlite_db:
            self._save_credentials_to_sqlite()
        else:
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
            if e.response.status_code == 400 and (self._sqlite_db or self._auth_source == "mongodb"):
                logger.warning("Token refresh failed with 400, reloading credentials and retrying...")
                if self._auth_source == "mongodb":
                    self._reload_active_account_from_mongodb_locked()
                else:
                    self._reload_active_account_from_sqlite_locked()
                await self._do_aws_sso_oidc_refresh()
            else:
                raise
    
    async def _do_aws_sso_oidc_refresh(self) -> None:
        """
        Performs the actual AWS SSO OIDC token refresh.
        
        This is the internal implementation called by _refresh_token_aws_sso_oidc().
        It performs a single refresh attempt with current in-memory credentials.
        
        Uses AWS SSO OIDC CreateToken API format:
        - Content-Type: application/json (not form-urlencoded)
        - Parameter names: camelCase (clientId, not client_id)
        - Payload: JSON object
        
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
        
        # AWS SSO OIDC CreateToken API uses JSON with camelCase parameters
        # Use SSO region for OIDC endpoint (may differ from API region)
        sso_region = self._sso_region or self._region
        url = get_aws_sso_oidc_url(sso_region)
        
        # IMPORTANT: AWS SSO OIDC CreateToken API requires:
        # 1. JSON payload (not form-urlencoded)
        # 2. camelCase parameter names (clientId, not client_id)
        payload = {
            "grantType": "refresh_token",
            "clientId": self._client_id,
            "clientSecret": self._client_secret,
            "refreshToken": self._refresh_token,
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Log request details (without secrets) for debugging
        logger.debug(f"AWS SSO OIDC refresh request: url={url}, sso_region={sso_region}, "
                     f"api_region={self._region}, client_id={self._client_id[:8]}...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            
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
        
        # AWS SSO OIDC CreateToken API returns camelCase fields
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
        
        # Save refreshed credentials to active configured source.
        if self._auth_source == "mongodb":
            self._save_credentials_to_mongodb()
        elif self._sqlite_db:
            self._save_credentials_to_sqlite()
        else:
            self._save_credentials_to_file()
    
    async def get_access_token(self) -> str:
        """
        Returns a valid access_token, refreshing it if necessary.
        
        Thread-safe method using asyncio.Lock.
        Automatically refreshes the token if it has expired or is about to expire.
        
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
            account_attempts = max(len(self._account_pool), 1)
            last_error: Optional[Exception] = None

            for attempt in range(account_attempts):
                force_next = attempt > 0
                selected_account = self._get_or_select_request_account_locked(force_next=force_next)
                if selected_account:
                    self._set_active_account(selected_account)

                # Token is valid and not expiring soon - just return it
                if self._access_token and not self.is_token_expiring_soon():
                    self._mark_current_account_healthy_locked()
                    self._sync_active_account_state()
                    return self._access_token
            
                # DB-backed mode: reload selected credentials first in case another client updated them.
                if (self._sqlite_db or self._auth_source == "mongodb") and self.is_token_expiring_soon():
                    logger.debug("DB-backed mode: reloading selected credentials before refresh attempt")
                    if self._auth_source == "mongodb":
                        self._reload_active_account_from_mongodb_locked()
                    else:
                        self._reload_active_account_from_sqlite_locked()
                    # Check if reloaded token is now valid
                    if self._access_token and not self.is_token_expiring_soon():
                        logger.debug("Credential reload provided fresh token, no refresh needed")
                        self._mark_current_account_healthy_locked()
                        self._sync_active_account_state()
                        return self._access_token
            
                # Try to refresh the token
                try:
                    await self._refresh_token_request()
                except httpx.HTTPStatusError as e:
                    # Graceful degradation for SQLite mode when refresh fails twice
                    # This happens when kiro-cli refreshed tokens in memory without persisting
                    if e.response.status_code == 400 and (self._sqlite_db or self._auth_source == "mongodb"):
                        logger.warning(
                            "Token refresh failed with 400 after credential reload. "
                            "This may happen if external clients refreshed tokens without persisting."
                        )
                        # Check if access_token is still usable
                        if self._access_token and not self.is_token_expired():
                            logger.warning(
                                "Using existing access_token until it expires. "
                                "Run 'kiro-cli login' when convenient to refresh credentials."
                            )
                            self._mark_current_account_healthy_locked()
                            self._sync_active_account_state()
                            return self._access_token
                        degraded_error = ValueError(
                            "Token expired and refresh failed. "
                            "Please run 'kiro-cli login' to refresh your credentials."
                        )
                        last_error = degraded_error
                        if len(self._account_pool) > 1:
                            self._mark_current_account_unhealthy_locked()
                            continue
                        raise degraded_error

                    last_error = e
                    if len(self._account_pool) > 1:
                        self._mark_current_account_unhealthy_locked()
                        continue
                    raise
                except ValueError as e:
                    last_error = e
                    if len(self._account_pool) > 1:
                        self._mark_current_account_unhealthy_locked()
                        continue
                    raise

                if self._access_token:
                    self._mark_current_account_healthy_locked()
                    self._sync_active_account_state()
                    return self._access_token

                last_error = ValueError("Failed to obtain access token")
                if len(self._account_pool) > 1:
                    self._mark_current_account_unhealthy_locked()
                    continue
                raise last_error

            if last_error:
                raise last_error
            raise ValueError("Failed to obtain access token")
    
    async def force_refresh(self) -> str:
        """
        Forces a token refresh.
        
        Used when receiving a 403 error from the API.
        
        Returns:
            New access token
        """
        async with self._lock:
            await self._refresh_token_request()
            if not self._access_token:
                raise ValueError("Failed to obtain access token during force refresh")
            refreshed_token = self._access_token
            return refreshed_token
    
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
