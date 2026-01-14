# -*- coding: utf-8 -*-

"""
Unit tests for KiroAuthManager.
Tests token management logic for Kiro without real network requests.
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
import httpx

from kiro.auth import KiroAuthManager, AuthType
from kiro.config import TOKEN_REFRESH_THRESHOLD


class TestKiroAuthManagerInitialization:
    """Tests for KiroAuthManager initialization."""

    def test_initialization_stores_credentials(self):
        """
        What it does: Verifies correct storage of credentials during initialization.
        Purpose: Ensure all constructor parameters are stored in private fields.
        """
        print("Setup: Creating KiroAuthManager with test credentials...")
        manager = KiroAuthManager(
            refresh_token="test_refresh_123",
            profile_arn="arn:aws:codewhisperer:us-east-1:123456789:profile/test",
            region="us-east-1",
        )

        print("Verification: All credentials stored correctly...")
        print(
            f"Comparing refresh_token: Expected 'test_refresh_123', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "test_refresh_123"

        print(
            f"Comparing profile_arn: Expected 'arn:aws:...', Got '{manager._profile_arn}'"
        )
        assert (
            manager._profile_arn
            == "arn:aws:codewhisperer:us-east-1:123456789:profile/test"
        )

        print(f"Comparing region: Expected 'us-east-1', Got '{manager._region}'")
        assert manager._region == "us-east-1"

        print("Verification: Token is initially empty...")
        assert manager._access_token is None
        assert manager._expires_at is None

    def test_initialization_sets_correct_urls_for_region(self):
        """
        What it does: Verifies URL formation based on region.
        Purpose: Ensure URLs are dynamically formed with the correct region.
        """
        print("Setup: Creating KiroAuthManager with region eu-west-1...")
        manager = KiroAuthManager(refresh_token="test_token", region="eu-west-1")

        print("Verification: URLs contain correct region...")
        print(
            f"Comparing refresh_url: Expected 'eu-west-1' in URL, Got '{manager._refresh_url}'"
        )
        assert "eu-west-1" in manager._refresh_url

        print(
            f"Comparing api_host: Expected 'eu-west-1' in URL, Got '{manager._api_host}'"
        )
        assert "eu-west-1" in manager._api_host

        print(f"Comparing q_host: Expected 'eu-west-1' in URL, Got '{manager._q_host}'")
        assert "eu-west-1" in manager._q_host

    def test_initialization_generates_fingerprint(self):
        """
        What it does: Verifies unique fingerprint generation.
        Purpose: Ensure fingerprint is generated and has correct format.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test_token")

        print("Verification: Fingerprint generated...")
        print(f"Fingerprint: {manager._fingerprint}")
        assert manager._fingerprint is not None
        assert len(manager._fingerprint) == 64  # SHA256 hex digest


class TestKiroAuthManagerCredentialsFile:
    """Tests for loading credentials from file."""

    def test_load_credentials_from_file(self, temp_creds_file):
        """
        What it does: Verifies loading credentials from JSON file.
        Purpose: Ensure data is correctly read from file.
        """
        print(
            f"Setup: Creating KiroAuthManager with credentials file: {temp_creds_file}"
        )
        manager = KiroAuthManager(creds_file=temp_creds_file)

        print("Verification: Data loaded from file...")
        print(
            f"Comparing access_token: Expected 'file_access_token', Got '{manager._access_token}'"
        )
        assert manager._access_token == "file_access_token"

        print(
            f"Comparing refresh_token: Expected 'file_refresh_token', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "file_refresh_token"

        print(f"Comparing region: Expected 'us-east-1', Got '{manager._region}'")
        assert manager._region == "us-east-1"

        print("Verification: expiresAt parsed correctly...")
        assert manager._expires_at is not None
        assert manager._expires_at.year == 2099

    def test_load_credentials_file_not_found(self, tmp_path):
        """
        What it does: Verifies handling of missing credentials file.
        Purpose: Ensure application doesn't crash when file is missing.
        """
        print("Setup: Creating KiroAuthManager with non-existent file...")
        non_existent_file = str(tmp_path / "non_existent.json")

        manager = KiroAuthManager(
            refresh_token="fallback_token", creds_file=non_existent_file
        )

        print("Verification: Fallback refresh_token is used...")
        print(
            f"Comparing refresh_token: Expected 'fallback_token', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "fallback_token"


class TestKiroAuthManagerTokenExpiration:
    """Tests for token expiration checking."""

    def test_is_token_expiring_soon_returns_true_when_no_expires_at(self):
        """
        What it does: Verifies that without expires_at token is considered expiring.
        Purpose: Ensure safe behavior when time information is missing.
        """
        print("Setup: Creating KiroAuthManager without expires_at...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = None

        print("Verification: is_token_expiring_soon returns True...")
        result = manager.is_token_expiring_soon()
        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    def test_is_token_expiring_soon_returns_true_when_expired(self):
        """
        What it does: Verifies that expired token is correctly identified.
        Purpose: Ensure token in the past is considered expiring.
        """
        print("Setup: Creating KiroAuthManager with expired token...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        print("Verification: is_token_expiring_soon returns True for expired token...")
        result = manager.is_token_expiring_soon()
        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    def test_is_token_expiring_soon_returns_true_within_threshold(self):
        """
        What it does: Verifies that token within threshold is considered expiring.
        Purpose: Ensure token is refreshed in advance (10 minutes before expiration).
        """
        print("Setup: Creating KiroAuthManager with token expiring in 5 minutes...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        print(f"TOKEN_REFRESH_THRESHOLD = {TOKEN_REFRESH_THRESHOLD} seconds")
        print(
            "Verification: is_token_expiring_soon returns True (5 min < 10 min threshold)..."
        )
        result = manager.is_token_expiring_soon()
        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    def test_is_token_expiring_soon_returns_false_when_valid(self):
        """
        What it does: Verifies that valid token is not considered expiring.
        Purpose: Ensure token far in the future doesn't require refresh.
        """
        print("Setup: Creating KiroAuthManager with token expiring in 1 hour...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("Verification: is_token_expiring_soon returns False...")
        result = manager.is_token_expiring_soon()
        print(f"Comparing result: Expected False, Got {result}")
        assert result is False


class TestKiroAuthManagerTokenRefresh:
    """Tests for token refresh mechanism."""

    @pytest.mark.asyncio
    async def test_refresh_token_successful(
        self, valid_kiro_token, mock_kiro_token_response
    ):
        """
        What it does: Tests successful token refresh via Kiro API.
        Purpose: Verify that on successful response token and expiration time are set.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test_refresh", region="us-east-1")

        print("Setup: Mocking successful response from Kiro...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_kiro_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling _refresh_token_request()...")
            await manager._refresh_token_request()

            print("Verification: Token set correctly...")
            print(
                f"Comparing access_token: Expected '{valid_kiro_token}', Got '{manager._access_token}'"
            )
            assert manager._access_token == valid_kiro_token

            print("Verification: Expiration time set...")
            assert manager._expires_at is not None

            print("Verification: POST request was made...")
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_updates_refresh_token(self, mock_kiro_token_response):
        """
        What it does: Verifies refresh_token update from response.
        Purpose: Ensure new refresh_token is saved.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="old_refresh_token")

        print("Setup: Mocking response with new refresh_token...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_kiro_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Refreshing token...")
            await manager._refresh_token_request()

            print("Verification: refresh_token updated...")
            print(
                f"Comparing refresh_token: Expected 'new_refresh_token_xyz', Got '{manager._refresh_token}'"
            )
            assert manager._refresh_token == "new_refresh_token_xyz"

    @pytest.mark.asyncio
    async def test_refresh_token_missing_access_token_raises(self):
        """
        What it does: Verifies handling of response without accessToken.
        Purpose: Ensure exception is raised on invalid response.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test_refresh")

        print("Setup: Mocking response without accessToken...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"expiresIn": 3600})  # No accessToken!
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Attempting token refresh...")
            with pytest.raises(ValueError) as exc_info:
                await manager._refresh_token_request()

            print(f"Verification: ValueError raised with message: {exc_info.value}")
            assert "accessToken" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token_raises(self):
        """
        What it does: Verifies handling of missing refresh_token.
        Purpose: Ensure exception is raised without refresh_token.
        """
        print("Setup: Creating KiroAuthManager without refresh_token...")
        manager = KiroAuthManager()
        manager._refresh_token = None

        print("Action: Attempting token refresh without refresh_token...")
        with pytest.raises(ValueError) as exc_info:
            await manager._refresh_token_request()

        print(f"Verification: ValueError raised: {exc_info.value}")
        assert "Refresh token" in str(exc_info.value)


class TestKiroAuthManagerGetAccessToken:
    """Tests for public get_access_token method."""

    @pytest.mark.asyncio
    async def test_get_access_token_refreshes_when_expired(
        self, valid_kiro_token, mock_kiro_token_response
    ):
        """
        What it does: Verifies automatic refresh of expired token.
        Purpose: Ensure stale token is refreshed before returning.
        """
        print("Setup: Creating KiroAuthManager with expired token...")
        manager = KiroAuthManager(refresh_token="test_refresh")
        manager._access_token = "old_expired_token"
        manager._expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        print("Setup: Mocking successful refresh...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_kiro_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Requesting token via get_access_token()...")
            token = await manager.get_access_token()

            print("Verification: Got new token, not expired one...")
            print(f"Comparing token: Expected '{valid_kiro_token}', Got '{token}'")
            assert token == valid_kiro_token
            assert token != "old_expired_token"

            print("Verification: _refresh_token_request was called...")
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_access_token_returns_valid_without_refresh(
        self, valid_kiro_token
    ):
        """
        What it does: Verifies valid token is returned without refresh.
        Purpose: Ensure no unnecessary requests are made if token is valid.
        """
        print("Setup: Creating KiroAuthManager with valid token...")
        manager = KiroAuthManager(refresh_token="test_refresh")
        manager._access_token = valid_kiro_token
        manager._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("Setup: Mocking httpx to track calls...")
        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock()
            mock_client_class.return_value = mock_client

            print("Action: Requesting valid token...")
            token = await manager.get_access_token()

            print("Verification: Existing token returned...")
            print(f"Comparing token: Expected '{valid_kiro_token}', Got '{token}'")
            assert token == valid_kiro_token

            print(
                "Verification: _refresh_token was NOT called (no network requests)..."
            )
            mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_access_token_thread_safety(
        self, valid_kiro_token, mock_kiro_token_response
    ):
        """
        What it does: Verifies thread safety via asyncio.Lock.
        Purpose: Ensure parallel calls don't cause race conditions.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test_refresh")
        manager._access_token = None
        manager._expires_at = None

        refresh_call_count = 0

        async def mock_refresh():
            nonlocal refresh_call_count
            refresh_call_count += 1
            await asyncio.sleep(0.1)  # Simulate delay
            manager._access_token = valid_kiro_token
            manager._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("Setup: Patching _refresh_token_request to track calls...")
        with patch.object(manager, "_refresh_token_request", side_effect=mock_refresh):
            print("Action: 5 parallel get_access_token() calls...")
            tokens = await asyncio.gather(
                *[manager.get_access_token() for _ in range(5)]
            )

            print("Verification: All calls got the same token...")
            assert all(token == valid_kiro_token for token in tokens)

            print("Verification: _refresh_token called ONLY ONCE (thanks to lock)...")
            print(f"Comparing call count: Expected 1, Got {refresh_call_count}")
            assert refresh_call_count == 1


class TestKiroAuthManagerForceRefresh:
    """Tests for forced token refresh."""

    @pytest.mark.asyncio
    async def test_force_refresh_updates_token(
        self, valid_kiro_token, mock_kiro_token_response
    ):
        """
        What it does: Verifies forced token refresh.
        Purpose: Ensure force_refresh always refreshes the token.
        """
        print("Setup: Creating KiroAuthManager with valid token...")
        manager = KiroAuthManager(refresh_token="test_refresh")
        manager._access_token = "old_but_valid_token"
        manager._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("Setup: Mocking refresh...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_kiro_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Force refreshing token...")
            token = await manager.force_refresh()

            print("Verification: Token refreshed despite old one being valid...")
            print(f"Comparing token: Expected '{valid_kiro_token}', Got '{token}'")
            assert token == valid_kiro_token

            print("Verification: POST request was made...")
            mock_client.post.assert_called_once()


class TestKiroAuthManagerProperties:
    """Tests for KiroAuthManager properties."""

    def test_profile_arn_property(self):
        """
        What it does: Verifies profile_arn property.
        Purpose: Ensure profile_arn is accessible via property.
        """
        print("Setup: Creating KiroAuthManager with profile_arn...")
        manager = KiroAuthManager(
            refresh_token="test", profile_arn="arn:aws:test:profile"
        )

        print("Verification: profile_arn accessible...")
        print(
            f"Comparing profile_arn: Expected 'arn:aws:test:profile', Got '{manager.profile_arn}'"
        )
        assert manager.profile_arn == "arn:aws:test:profile"

    def test_region_property(self):
        """
        What it does: Verifies region property.
        Purpose: Ensure region is accessible via property.
        """
        print("Setup: Creating KiroAuthManager with region...")
        manager = KiroAuthManager(refresh_token="test", region="eu-west-1")

        print("Verification: region accessible...")
        print(f"Comparing region: Expected 'eu-west-1', Got '{manager.region}'")
        assert manager.region == "eu-west-1"

    def test_api_host_property(self):
        """
        What it does: Verifies api_host property.
        Purpose: Ensure api_host is formed correctly.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test", region="us-east-1")

        print("Verification: api_host contains codewhisperer and region...")
        print(f"api_host: {manager.api_host}")
        assert "codewhisperer" in manager.api_host
        assert "us-east-1" in manager.api_host

    def test_fingerprint_property(self):
        """
        What it does: Verifies fingerprint property.
        Purpose: Ensure fingerprint is accessible via property.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(refresh_token="test")

        print("Verification: fingerprint accessible and has correct length...")
        print(f"fingerprint: {manager.fingerprint}")
        assert len(manager.fingerprint) == 64


# =============================================================================
# Tests for AuthType enum
# =============================================================================


class TestAuthTypeEnum:
    """Tests for AuthType enum."""

    def test_auth_type_enum_values(self):
        """
        What it does: Verifies AuthType enum values.
        Purpose: Ensure enum contains KIRO_DESKTOP and AWS_SSO_OIDC.
        """
        print("Verification: AuthType contains KIRO_DESKTOP...")
        assert AuthType.KIRO_DESKTOP.value == "kiro_desktop"

        print("Verification: AuthType contains AWS_SSO_OIDC...")
        assert AuthType.AWS_SSO_OIDC.value == "aws_sso_oidc"

        print(f"Comparing value count: Expected 2, Got {len(AuthType)}")
        assert len(AuthType) == 2


# =============================================================================
# Tests for _detect_auth_type()
# =============================================================================


class TestKiroAuthManagerDetectAuthType:
    """Tests for _detect_auth_type() method."""

    def test_detect_auth_type_kiro_desktop_when_no_client_credentials(self):
        """
        What it does: Verifies KIRO_DESKTOP type detection without client credentials.
        Purpose: Ensure KIRO_DESKTOP is used without clientId/clientSecret.
        """
        print("Setup: Creating KiroAuthManager without client credentials...")
        manager = KiroAuthManager(refresh_token="test_token")

        print("Verification: auth_type = KIRO_DESKTOP...")
        print(f"Comparing auth_type: Expected KIRO_DESKTOP, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.KIRO_DESKTOP

    def test_detect_auth_type_aws_sso_oidc_when_client_credentials_present(self):
        """
        What it does: Verifies AWS_SSO_OIDC type detection with client credentials.
        Purpose: Ensure AWS_SSO_OIDC is used with clientId and clientSecret.
        """
        print("Setup: Creating KiroAuthManager with client credentials...")
        manager = KiroAuthManager(
            refresh_token="test_token",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        print("Verification: auth_type = AWS_SSO_OIDC...")
        print(f"Comparing auth_type: Expected AWS_SSO_OIDC, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.AWS_SSO_OIDC

    def test_detect_auth_type_kiro_desktop_when_only_client_id(self):
        """
        What it does: Verifies type detection with only clientId (no secret).
        Purpose: Ensure KIRO_DESKTOP is used without clientSecret.
        """
        print("Setup: Creating KiroAuthManager with only client_id...")
        manager = KiroAuthManager(
            refresh_token="test_token", client_id="test_client_id"
        )

        print("Verification: auth_type = KIRO_DESKTOP (both id and secret required)...")
        print(f"Comparing auth_type: Expected KIRO_DESKTOP, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.KIRO_DESKTOP


# =============================================================================
# Tests for loading AWS SSO credentials from JSON file
# =============================================================================


class TestKiroAuthManagerAwsSsoCredentialsFile:
    """Tests for loading AWS SSO OIDC credentials from JSON file."""

    def test_load_credentials_from_file_with_client_id_and_secret(
        self, temp_aws_sso_creds_file
    ):
        """
        What it does: Verifies loading clientId and clientSecret from JSON file.
        Purpose: Ensure AWS SSO fields are correctly read from file.
        """
        print(
            f"Setup: Creating KiroAuthManager with AWS SSO file: {temp_aws_sso_creds_file}"
        )
        manager = KiroAuthManager(creds_file=temp_aws_sso_creds_file)

        print("Verification: clientId loaded...")
        print(
            f"Comparing client_id: Expected 'test_client_id_12345', Got '{manager._client_id}'"
        )
        assert manager._client_id == "test_client_id_12345"

        print("Verification: clientSecret loaded...")
        print(
            f"Comparing client_secret: Expected 'test_client_secret_67890', Got '{manager._client_secret}'"
        )
        assert manager._client_secret == "test_client_secret_67890"

    def test_load_credentials_from_file_auto_detects_aws_sso_oidc(
        self, temp_aws_sso_creds_file
    ):
        """
        What it does: Verifies auto-detection of auth type after loading from file.
        Purpose: Ensure auth_type automatically becomes AWS_SSO_OIDC.
        """
        print(
            f"Setup: Creating KiroAuthManager with AWS SSO file: {temp_aws_sso_creds_file}"
        )
        manager = KiroAuthManager(creds_file=temp_aws_sso_creds_file)

        print("Verification: auth_type automatically detected as AWS_SSO_OIDC...")
        print(f"Comparing auth_type: Expected AWS_SSO_OIDC, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.AWS_SSO_OIDC

    def test_load_kiro_desktop_file_stays_kiro_desktop(self, temp_creds_file):
        """
        What it does: Verifies that Kiro Desktop file doesn't change type to AWS SSO.
        Purpose: Ensure file without clientId/clientSecret stays KIRO_DESKTOP.
        """
        print(
            f"Setup: Creating KiroAuthManager with Kiro Desktop file: {temp_creds_file}"
        )
        manager = KiroAuthManager(creds_file=temp_creds_file)

        print("Verification: auth_type stays KIRO_DESKTOP...")
        print(f"Comparing auth_type: Expected KIRO_DESKTOP, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.KIRO_DESKTOP


# =============================================================================
# Tests for loading credentials from SQLite
# =============================================================================


class TestKiroAuthManagerSqliteCredentials:
    """Tests for loading credentials from SQLite database (kiro-cli format)."""

    def test_load_credentials_from_sqlite_success(self, temp_sqlite_db):
        """
        What it does: Verifies successful loading of credentials from SQLite.
        Purpose: Ensure all data is correctly read from database.
        """
        print(f"Setup: Creating KiroAuthManager with SQLite: {temp_sqlite_db}")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: access_token loaded...")
        print(
            f"Comparing access_token: Expected 'sqlite_access_token', Got '{manager._access_token}'"
        )
        assert manager._access_token == "sqlite_access_token"

        print("Verification: refresh_token loaded...")
        print(
            f"Comparing refresh_token: Expected 'sqlite_refresh_token', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "sqlite_refresh_token"

    def test_load_credentials_from_sqlite_file_not_found(self, tmp_path):
        """
        What it does: Verifies handling of missing SQLite file.
        Purpose: Ensure application doesn't crash when file is missing.
        """
        print("Setup: Creating KiroAuthManager with non-existent SQLite file...")
        non_existent_db = str(tmp_path / "non_existent.sqlite3")

        manager = KiroAuthManager(
            refresh_token="fallback_token", sqlite_db=non_existent_db
        )

        print("Verification: Fallback refresh_token is used...")
        print(
            f"Comparing refresh_token: Expected 'fallback_token', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "fallback_token"

    def test_load_credentials_from_sqlite_loads_token_data(self, temp_sqlite_db):
        """
        What it does: Verifies loading token data from SQLite.
        Purpose: Ensure access_token, refresh_token, sso_region are loaded.
        Note: API region stays at us-east-1 (CodeWhisperer API only exists there),
              SSO region is stored separately for OIDC token refresh.
        """
        print(f"Setup: Creating KiroAuthManager with SQLite: {temp_sqlite_db}")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: SSO region loaded from SQLite...")
        print(
            f"Comparing sso_region: Expected 'eu-west-1', Got '{manager._sso_region}'"
        )
        assert manager._sso_region == "eu-west-1"

        print("Verification: API region stays at us-east-1...")
        print(f"Comparing region: Expected 'us-east-1', Got '{manager._region}'")
        assert manager._region == "us-east-1"

        print("Verification: expires_at parsed...")
        assert manager._expires_at is not None
        assert manager._expires_at.year == 2099

    def test_load_credentials_from_sqlite_loads_device_registration(
        self, temp_sqlite_db
    ):
        """
        What it does: Verifies loading device registration from SQLite.
        Purpose: Ensure client_id and client_secret are loaded.
        """
        print(f"Setup: Creating KiroAuthManager with SQLite: {temp_sqlite_db}")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: client_id loaded...")
        print(
            f"Comparing client_id: Expected 'sqlite_client_id', Got '{manager._client_id}'"
        )
        assert manager._client_id == "sqlite_client_id"

        print("Verification: client_secret loaded...")
        print(
            f"Comparing client_secret: Expected 'sqlite_client_secret', Got '{manager._client_secret}'"
        )
        assert manager._client_secret == "sqlite_client_secret"

    def test_load_credentials_from_sqlite_auto_detects_aws_sso_oidc(
        self, temp_sqlite_db
    ):
        """
        What it does: Verifies auto-detection of auth type after loading from SQLite.
        Purpose: Ensure auth_type automatically becomes AWS_SSO_OIDC.
        """
        print(f"Setup: Creating KiroAuthManager with SQLite: {temp_sqlite_db}")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: auth_type automatically detected as AWS_SSO_OIDC...")
        print(f"Comparing auth_type: Expected AWS_SSO_OIDC, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.AWS_SSO_OIDC

    def test_load_credentials_from_sqlite_handles_missing_registration_key(
        self, temp_sqlite_db_token_only
    ):
        """
        What it does: Verifies handling of missing device-registration key.
        Purpose: Ensure application doesn't crash without device-registration.
        """
        print(
            "Setup: Creating KiroAuthManager with SQLite without device-registration..."
        )
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db_token_only)

        print("Verification: refresh_token loaded...")
        assert manager._refresh_token == "partial_refresh_token"

        print("Verification: client_id stayed None...")
        assert manager._client_id is None

        print("Verification: auth_type = KIRO_DESKTOP (no client credentials)...")
        assert manager.auth_type == AuthType.KIRO_DESKTOP

    def test_load_credentials_from_sqlite_handles_invalid_json(
        self, temp_sqlite_db_invalid_json
    ):
        """
        What it does: Verifies handling of invalid JSON in SQLite.
        Purpose: Ensure application doesn't crash on invalid JSON.
        """
        print("Setup: Creating KiroAuthManager with SQLite with invalid JSON...")
        manager = KiroAuthManager(
            refresh_token="fallback_token", sqlite_db=temp_sqlite_db_invalid_json
        )

        print("Verification: Fallback refresh_token is used...")
        print(
            f"Comparing refresh_token: Expected 'fallback_token', Got '{manager._refresh_token}'"
        )
        assert manager._refresh_token == "fallback_token"

    def test_sqlite_takes_priority_over_json_file(
        self, temp_sqlite_db, temp_creds_file
    ):
        """
        What it does: Verifies SQLite priority over JSON file.
        Purpose: Ensure SQLite is loaded instead of JSON when both specified.
        """
        print("Setup: Creating KiroAuthManager with SQLite and JSON file...")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db, creds_file=temp_creds_file)

        print("Verification: Data from SQLite (not from JSON)...")
        print(
            f"Comparing access_token: Expected 'sqlite_access_token', Got '{manager._access_token}'"
        )
        assert manager._access_token == "sqlite_access_token"

        print("Verification: SSO region from SQLite...")
        print(
            f"Comparing sso_region: Expected 'eu-west-1', Got '{manager._sso_region}'"
        )
        assert manager._sso_region == "eu-west-1"

        print("Verification: API region stays at us-east-1...")
        print(f"Comparing region: Expected 'us-east-1', Got '{manager._region}'")
        assert manager._region == "us-east-1"


# =============================================================================
# Tests for _refresh_token_request() routing
# =============================================================================


class TestKiroAuthManagerRefreshTokenRouting:
    """Tests for _refresh_token_request() routing based on auth_type."""

    @pytest.mark.asyncio
    async def test_refresh_token_request_routes_to_kiro_desktop(self):
        """
        What it does: Verifies that KIRO_DESKTOP calls _refresh_token_kiro_desktop.
        Purpose: Ensure correct routing for Kiro Desktop auth.
        """
        print("Setup: Creating KiroAuthManager with KIRO_DESKTOP...")
        manager = KiroAuthManager(refresh_token="test_refresh")
        assert manager.auth_type == AuthType.KIRO_DESKTOP

        print("Setup: Mocking _refresh_token_kiro_desktop...")
        with patch.object(
            manager, "_refresh_token_kiro_desktop", new_callable=AsyncMock
        ) as mock_desktop:
            with patch.object(
                manager, "_refresh_token_aws_sso_oidc", new_callable=AsyncMock
            ) as mock_sso:
                await manager._refresh_token_request()

                print("Verification: _refresh_token_kiro_desktop was called...")
                mock_desktop.assert_called_once()

                print("Verification: _refresh_token_aws_sso_oidc was NOT called...")
                mock_sso.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_token_request_routes_to_aws_sso_oidc(self):
        """
        What it does: Verifies that AWS_SSO_OIDC calls _refresh_token_aws_sso_oidc.
        Purpose: Ensure correct routing for AWS SSO OIDC auth.
        """
        print("Setup: Creating KiroAuthManager with AWS_SSO_OIDC...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert manager.auth_type == AuthType.AWS_SSO_OIDC

        print("Setup: Mocking _refresh_token_aws_sso_oidc...")
        with patch.object(
            manager, "_refresh_token_kiro_desktop", new_callable=AsyncMock
        ) as mock_desktop:
            with patch.object(
                manager, "_refresh_token_aws_sso_oidc", new_callable=AsyncMock
            ) as mock_sso:
                await manager._refresh_token_request()

                print("Verification: _refresh_token_aws_sso_oidc was called...")
                mock_sso.assert_called_once()

                print("Verification: _refresh_token_kiro_desktop was NOT called...")
                mock_desktop.assert_not_called()


# =============================================================================
# Tests for _refresh_token_aws_sso_oidc()
# =============================================================================


class TestKiroAuthManagerAwsSsoOidcRefresh:
    """Tests for _refresh_token_aws_sso_oidc() method."""

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_success(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Tests successful token refresh via AWS SSO OIDC.
        Purpose: Verify that on successful response token and expiration time are set.
        """
        print("Setup: Creating KiroAuthManager with AWS SSO OIDC...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
            region="us-east-1",
        )

        print("Setup: Mocking successful response from AWS SSO OIDC...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling _refresh_token_aws_sso_oidc()...")
            await manager._refresh_token_aws_sso_oidc()

            print("Verification: Token set correctly...")
            print(
                f"Comparing access_token: Expected 'new_aws_sso_access_token', Got '{manager._access_token}'"
            )
            assert manager._access_token == "new_aws_sso_access_token"

            print("Verification: Expiration time set...")
            assert manager._expires_at is not None

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_raises_without_refresh_token(self):
        """
        What it does: Verifies handling of missing refresh_token.
        Purpose: Ensure ValueError is raised without refresh_token.
        """
        print("Setup: Creating KiroAuthManager without refresh_token...")
        manager = KiroAuthManager(
            client_id="test_client_id", client_secret="test_client_secret"
        )
        manager._refresh_token = None

        print("Action: Attempting token refresh without refresh_token...")
        with pytest.raises(ValueError) as exc_info:
            await manager._refresh_token_aws_sso_oidc()

        print(f"Verification: ValueError raised: {exc_info.value}")
        assert "Refresh token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_raises_without_client_id(self):
        """
        What it does: Verifies handling of missing client_id.
        Purpose: Ensure ValueError is raised without client_id.
        """
        print("Setup: Creating KiroAuthManager without client_id...")
        manager = KiroAuthManager(
            refresh_token="test_refresh", client_secret="test_client_secret"
        )
        manager._client_id = None
        manager._auth_type = AuthType.AWS_SSO_OIDC

        print("Action: Attempting token refresh without client_id...")
        with pytest.raises(ValueError) as exc_info:
            await manager._refresh_token_aws_sso_oidc()

        print(f"Verification: ValueError raised: {exc_info.value}")
        assert "Client ID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_raises_without_client_secret(self):
        """
        What it does: Verifies handling of missing client_secret.
        Purpose: Ensure ValueError is raised without client_secret.
        """
        print("Setup: Creating KiroAuthManager without client_secret...")
        manager = KiroAuthManager(
            refresh_token="test_refresh", client_id="test_client_id"
        )
        manager._client_secret = None
        manager._auth_type = AuthType.AWS_SSO_OIDC

        print("Action: Attempting token refresh without client_secret...")
        with pytest.raises(ValueError) as exc_info:
            await manager._refresh_token_aws_sso_oidc()

        print(f"Verification: ValueError raised: {exc_info.value}")
        assert "Client secret" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_uses_correct_endpoint(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies correct endpoint usage.
        Purpose: Ensure request goes to https://oidc.{region}.amazonaws.com/token.
        """
        print("Setup: Creating KiroAuthManager with region=eu-west-1...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
            region="eu-west-1",
        )

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: POST request to correct URL...")
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            expected_url = "https://oidc.eu-west-1.amazonaws.com/token"
            print(f"Comparing URL: Expected '{expected_url}', Got '{url}'")
            assert url == expected_url

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_uses_form_urlencoded(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies form-urlencoded format usage.
        Purpose: Ensure Content-Type = application/x-www-form-urlencoded.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: Content-Type = application/x-www-form-urlencoded...")
            call_args = mock_client.post.call_args
            headers = call_args[1].get("headers", {})
            print(
                f"Comparing Content-Type: Expected 'application/x-www-form-urlencoded', Got '{headers.get('Content-Type')}'"
            )
            assert headers.get("Content-Type") == "application/x-www-form-urlencoded"

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_sends_correct_grant_type(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies correct grant_type is sent.
        Purpose: Ensure grant_type=refresh_token.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: grant_type = refresh_token...")
            call_args = mock_client.post.call_args
            data = call_args[1].get("data", {})
            print(
                f"Comparing grant_type: Expected 'refresh_token', Got '{data.get('grant_type')}'"
            )
            assert data.get("grant_type") == "refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_updates_tokens(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies access_token and refresh_token update.
        Purpose: Ensure both tokens are updated from response.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(
            refresh_token="old_refresh_token",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: access_token updated...")
            assert manager._access_token == "new_aws_sso_access_token"

            print("Verification: refresh_token updated...")
            assert manager._refresh_token == "new_aws_sso_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_calculates_expiration(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies correct expiration time calculation.
        Purpose: Ensure expires_at is calculated based on expiresIn.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        print("Setup: Mocking HTTP client with expiresIn=7200...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(
            return_value=mock_aws_sso_oidc_token_response(expires_in=7200)
        )
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: expires_at set...")
            assert manager._expires_at is not None

            print("Verification: expires_at in the future...")
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            assert manager._expires_at > now

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_does_not_send_scopes(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies that scopes are NOT sent in refresh request.
        Purpose: Per OAuth 2.0 RFC 6749 Section 6, scope is optional in refresh and
                 AWS SSO OIDC returns invalid_request if scope is sent.
        """
        print("Setup: Creating KiroAuthManager with scopes...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        # Simulate scopes loaded from SQLite (this is what caused the bug)
        manager._scopes = ["codewhisperer:completions", "codewhisperer:analysis"]

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: scope NOT in request data...")
            call_args = mock_client.post.call_args
            data = call_args[1].get("data", {})
            print(f"Request data keys: {list(data.keys())}")
            assert "scope" not in data, "scope should NOT be sent in refresh request"

            print("Verification: only required fields sent...")
            expected_keys = {
                "grant_type",
                "client_id",
                "client_secret",
                "refresh_token",
            }
            print(f"Comparing keys: Expected {expected_keys}, Got {set(data.keys())}")
            assert set(data.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_works_without_scopes(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies refresh works when scopes are None.
        Purpose: Ensure backward compatibility with credentials that don't have scopes.
        """
        print("Setup: Creating KiroAuthManager without scopes...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        # Explicitly set scopes to None (default state)
        manager._scopes = None

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: Token refreshed successfully...")
            assert manager._access_token == "new_aws_sso_access_token"

            print("Verification: scope NOT in request data...")
            call_args = mock_client.post.call_args
            data = call_args[1].get("data", {})
            assert "scope" not in data


# =============================================================================
# Tests for auth_type property and constructor with new parameters
# =============================================================================


class TestKiroAuthManagerAuthTypeProperty:
    """Tests for auth_type property and constructor."""

    def test_auth_type_property_returns_correct_value(self):
        """
        What it does: Verifies that auth_type property returns correct value.
        Purpose: Ensure property works correctly.
        """
        print("Setup: Creating KiroAuthManager with KIRO_DESKTOP...")
        manager_desktop = KiroAuthManager(refresh_token="test")

        print("Verification: auth_type = KIRO_DESKTOP...")
        assert manager_desktop.auth_type == AuthType.KIRO_DESKTOP

        print("Setup: Creating KiroAuthManager with AWS_SSO_OIDC...")
        manager_sso = KiroAuthManager(
            refresh_token="test", client_id="id", client_secret="secret"
        )

        print("Verification: auth_type = AWS_SSO_OIDC...")
        assert manager_sso.auth_type == AuthType.AWS_SSO_OIDC

    def test_init_with_client_id_and_secret(self):
        """
        What it does: Verifies initialization with client_id and client_secret.
        Purpose: Ensure parameters are stored in private fields.
        """
        print("Setup: Creating KiroAuthManager with client credentials...")
        manager = KiroAuthManager(
            refresh_token="test",
            client_id="my_client_id",
            client_secret="my_client_secret",
        )

        print("Verification: client_id stored...")
        assert manager._client_id == "my_client_id"

        print("Verification: client_secret stored...")
        assert manager._client_secret == "my_client_secret"

    def test_init_with_sqlite_db_parameter(self, temp_sqlite_db):
        """
        What it does: Verifies initialization with sqlite_db parameter.
        Purpose: Ensure data is loaded from SQLite.
        """
        print(f"Setup: Creating KiroAuthManager with sqlite_db: {temp_sqlite_db}")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: Data loaded from SQLite...")
        assert manager._access_token == "sqlite_access_token"
        assert manager._refresh_token == "sqlite_refresh_token"

    def test_detect_auth_type_kiro_desktop_when_only_client_secret(self):
        """
        What it does: Verifies type detection with only clientSecret (no id).
        Purpose: Ensure KIRO_DESKTOP is used without clientId.
        """
        print("Setup: Creating KiroAuthManager with only client_secret...")
        manager = KiroAuthManager(
            refresh_token="test_token", client_secret="test_client_secret"
        )

        print("Verification: auth_type = KIRO_DESKTOP (both id and secret required)...")
        print(f"Comparing auth_type: Expected KIRO_DESKTOP, Got {manager.auth_type}")
        assert manager.auth_type == AuthType.KIRO_DESKTOP


# =============================================================================
# Tests for SSO region separation (Issue #16)
# =============================================================================


class TestKiroAuthManagerSsoRegionSeparation:
    """Tests for SSO region separation from API region (Issue #16 fix).

    Background: CodeWhisperer API only exists in us-east-1, but users may have
    SSO credentials from other regions (e.g., ap-southeast-1 for Singapore).
    The fix separates SSO region (for OIDC token refresh) from API region.
    """

    def test_api_region_stays_us_east_1_when_loading_from_sqlite(self, temp_sqlite_db):
        """
        What it does: Verifies API region doesn't change when loading from SQLite.
        Purpose: Ensure CodeWhisperer API calls go to us-east-1 regardless of SSO region.
        """
        print("Setup: Creating KiroAuthManager with SQLite (region=eu-west-1)...")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: API region stays at us-east-1...")
        print(f"Comparing _region: Expected 'us-east-1', Got '{manager._region}'")
        assert manager._region == "us-east-1"

        print("Verification: api_host contains us-east-1...")
        print(f"api_host: {manager._api_host}")
        assert "us-east-1" in manager._api_host

        print("Verification: q_host contains us-east-1...")
        print(f"q_host: {manager._q_host}")
        assert "us-east-1" in manager._q_host

    def test_sso_region_stored_separately_from_api_region(self, temp_sqlite_db):
        """
        What it does: Verifies SSO region is stored in _sso_region field.
        Purpose: Ensure SSO region is available for OIDC token refresh.
        """
        print("Setup: Creating KiroAuthManager with SQLite (region=eu-west-1)...")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: SSO region stored in _sso_region...")
        print(
            f"Comparing _sso_region: Expected 'eu-west-1', Got '{manager._sso_region}'"
        )
        assert manager._sso_region == "eu-west-1"

        print("Verification: API region is different from SSO region...")
        assert manager._region != manager._sso_region

    def test_sso_region_none_when_not_loaded_from_sqlite(self):
        """
        What it does: Verifies _sso_region is None when not loading from SQLite.
        Purpose: Ensure backward compatibility with direct credential initialization.
        """
        print("Setup: Creating KiroAuthManager with direct credentials...")
        manager = KiroAuthManager(refresh_token="test_token", region="us-east-1")

        print("Verification: _sso_region is None...")
        print(f"Comparing _sso_region: Expected None, Got '{manager._sso_region}'")
        assert manager._sso_region is None

    @pytest.mark.asyncio
    async def test_oidc_refresh_uses_sso_region(self, mock_aws_sso_oidc_token_response):
        """
        What it does: Verifies OIDC token refresh uses SSO region, not API region.
        Purpose: Ensure token refresh goes to correct regional OIDC endpoint.
        """
        print("Setup: Creating KiroAuthManager with SSO region=ap-southeast-1...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
            region="us-east-1",  # API region
        )
        # Simulate SSO region loaded from SQLite
        manager._sso_region = "ap-southeast-1"

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: OIDC request went to SSO region (ap-southeast-1)...")
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            expected_url = "https://oidc.ap-southeast-1.amazonaws.com/token"
            print(f"Comparing URL: Expected '{expected_url}', Got '{url}'")
            assert url == expected_url
            assert "ap-southeast-1" in url
            assert "us-east-1" not in url

    @pytest.mark.asyncio
    async def test_oidc_refresh_falls_back_to_api_region_when_no_sso_region(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies OIDC refresh uses API region when SSO region not set.
        Purpose: Ensure backward compatibility when _sso_region is None.
        """
        print("Setup: Creating KiroAuthManager without SSO region...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
            region="eu-west-1",  # API region (also used for OIDC when no SSO region)
        )
        # Ensure _sso_region is None
        manager._sso_region = None

        print("Setup: Mocking HTTP client...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await manager._refresh_token_aws_sso_oidc()

            print("Verification: OIDC request fell back to API region (eu-west-1)...")
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            expected_url = "https://oidc.eu-west-1.amazonaws.com/token"
            print(f"Comparing URL: Expected '{expected_url}', Got '{url}'")
            assert url == expected_url

    def test_api_hosts_not_updated_when_loading_from_sqlite(self, temp_sqlite_db):
        """
        What it does: Verifies API hosts don't change when loading from SQLite.
        Purpose: Ensure all API calls go to us-east-1 where CodeWhisperer exists.
        """
        print("Setup: Creating KiroAuthManager with SQLite (region=eu-west-1)...")
        manager = KiroAuthManager(sqlite_db=temp_sqlite_db)

        print("Verification: _api_host points to us-east-1...")
        assert "us-east-1" in manager._api_host
        assert "eu-west-1" not in manager._api_host

        print("Verification: _q_host points to us-east-1...")
        assert "us-east-1" in manager._q_host
        assert "eu-west-1" not in manager._q_host

        print("Verification: _refresh_url points to us-east-1...")
        assert "us-east-1" in manager._refresh_url
        assert "eu-west-1" not in manager._refresh_url

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_uses_memory_token_first(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies that in-memory token is used first, not SQLite.
        Purpose: Ensure container's successfully refreshed token is used (not overwritten by SQLite).
        """
        print("Setup: Creating KiroAuthManager with in-memory credentials...")
        manager = KiroAuthManager(
            refresh_token="memory_refresh_token",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        # Simulate SQLite path being set (but we won't actually use it)
        manager._sqlite_db = "/fake/path/data.sqlite3"

        print("Setup: Mocking HTTP client for successful refresh...")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_aws_sso_oidc_token_response())
        mock_response.raise_for_status = Mock()

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Patch _load_credentials_from_sqlite to track if it's called
            with patch.object(manager, "_load_credentials_from_sqlite") as mock_load:
                await manager._refresh_token_aws_sso_oidc()

                print("Verification: SQLite was NOT reloaded (success on first try)...")
                mock_load.assert_not_called()

                print("Verification: Request used in-memory token...")
                call_args = mock_client.post.call_args
                data = call_args[1].get("data", {})
                print(f"Refresh token sent: {data.get('refresh_token')}")
                assert data.get("refresh_token") == "memory_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_reloads_sqlite_on_400_error(
        self, tmp_path, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies SQLite is reloaded and retry happens on 400 error.
        Purpose: Pick up fresh tokens after kiro-cli re-login when in-memory token is stale.
        """
        import sqlite3
        import json

        # Setup: Create initial SQLite database
        db_file = tmp_path / "data.sqlite3"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE auth_kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Initial token data (will become stale)
        initial_token_data = {
            "access_token": "old_access_token",
            "refresh_token": "old_refresh_token",
            "expires_at": "2099-01-01T00:00:00Z",
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:token", json.dumps(initial_token_data)),
        )

        registration_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:device-registration", json.dumps(registration_data)),
        )

        conn.commit()
        conn.close()

        print("Setup: Creating KiroAuthManager with SQLite...")
        manager = KiroAuthManager(sqlite_db=str(db_file))

        print("Verification: Initial refresh_token loaded...")
        assert manager._refresh_token == "old_refresh_token"

        # Simulate kiro-cli updating the SQLite with fresh tokens
        print("Action: Simulating kiro-cli token refresh (updating SQLite)...")
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        new_token_data = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token_from_kiro_cli",
            "expires_at": "2099-01-01T00:00:00Z",
            "region": "us-east-1",
        }
        cursor.execute(
            "UPDATE auth_kv SET value = ? WHERE key = ?",
            (json.dumps(new_token_data), "codewhisperer:odic:token"),
        )
        conn.commit()
        conn.close()

        # Manager still has old token in memory
        print("Verification: Manager still has old refresh_token in memory...")
        assert manager._refresh_token == "old_refresh_token"

        # Mock HTTP client: first call fails with 400, second succeeds
        print("Setup: Mocking HTTP client (first=400, second=200)...")

        # First response: 400 error (stale token)
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.text = (
            '{"error":"invalid_request","error_description":"Invalid request"}'
        )
        mock_error_response.json = Mock(return_value={"error": "invalid_request"})
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_error_response
            )
        )

        # Second response: success
        mock_success_response = AsyncMock()
        mock_success_response.status_code = 200
        mock_success_response.json = Mock(
            return_value=mock_aws_sso_oidc_token_response()
        )
        mock_success_response.raise_for_status = Mock()

        call_count = 0
        sent_tokens = []

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            sent_tokens.append(kwargs.get("data", {}).get("refresh_token"))
            if call_count == 1:
                return mock_error_response
            return mock_success_response

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling _refresh_token_aws_sso_oidc...")
            await manager._refresh_token_aws_sso_oidc()

            print("Verification: Two requests were made (retry on 400)...")
            print(f"Call count: {call_count}")
            assert call_count == 2, "Should retry after 400 error"

            print("Verification: First request used OLD token from memory...")
            print(f"First token sent: {sent_tokens[0]}")
            assert sent_tokens[0] == "old_refresh_token"

            print("Verification: Second request used NEW token from SQLite...")
            print(f"Second token sent: {sent_tokens[1]}")
            assert sent_tokens[1] == "new_refresh_token_from_kiro_cli"

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_no_retry_on_non_400_error(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies that non-400 errors are not retried.
        Purpose: Ensure only 400 (invalid_request) triggers SQLite reload.
        """
        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        manager._sqlite_db = "/fake/path/data.sqlite3"

        print("Setup: Mocking HTTP client with 500 error...")
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 500
        mock_error_response.text = "Internal Server Error"
        mock_error_response.json = Mock(side_effect=Exception("Not JSON"))
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=Mock(),
                response=mock_error_response,
            )
        )

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch.object(manager, "_load_credentials_from_sqlite") as mock_load:
                print(
                    "Action: Calling _refresh_token_aws_sso_oidc (expecting 500 error)..."
                )
                with pytest.raises(httpx.HTTPStatusError) as exc_info:
                    await manager._refresh_token_aws_sso_oidc()

                print("Verification: 500 error was raised (not retried)...")
                assert exc_info.value.response.status_code == 500

                print("Verification: SQLite was NOT reloaded (500 != 400)...")
                mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_token_aws_sso_oidc_no_retry_without_sqlite_db(
        self, mock_aws_sso_oidc_token_response
    ):
        """
        What it does: Verifies that 400 error is not retried when sqlite_db is not set.
        Purpose: Ensure retry only happens when SQLite source is available.
        """
        print("Setup: Creating KiroAuthManager WITHOUT sqlite_db...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        # Explicitly ensure no sqlite_db
        manager._sqlite_db = None

        print("Setup: Mocking HTTP client with 400 error...")
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.text = '{"error":"invalid_request"}'
        mock_error_response.json = Mock(return_value={"error": "invalid_request"})
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_error_response
            )
        )

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print(
                "Action: Calling _refresh_token_aws_sso_oidc (expecting 400 error)..."
            )
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await manager._refresh_token_aws_sso_oidc()

            print("Verification: 400 error was raised (no retry without sqlite_db)...")
            assert exc_info.value.response.status_code == 400

            print("Verification: Only one request was made...")
            assert mock_client.post.call_count == 1


# =============================================================================
# Tests for is_token_expired() method
# =============================================================================


class TestKiroAuthManagerIsTokenExpired:
    """Tests for is_token_expired() method.

    This method checks if the token has actually expired (not just expiring soon).
    Used for graceful degradation when refresh fails.
    """

    def test_is_token_expired_returns_true_when_no_expires_at(self):
        """
        What it does: Verifies that without expires_at token is considered expired.
        Purpose: Ensure safe behavior when time information is missing.
        """
        print("Setup: Creating KiroAuthManager without expires_at...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = None

        print("Verification: is_token_expired returns True...")
        result = manager.is_token_expired()
        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    def test_is_token_expired_returns_true_when_expired(self):
        """
        What it does: Verifies that expired token is correctly identified.
        Purpose: Ensure token in the past is considered expired.
        """
        print("Setup: Creating KiroAuthManager with expired token...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        print("Verification: is_token_expired returns True for expired token...")
        result = manager.is_token_expired()
        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    def test_is_token_expired_returns_false_when_valid(self):
        """
        What it does: Verifies that valid token is not considered expired.
        Purpose: Ensure token in the future is not considered expired.
        """
        print("Setup: Creating KiroAuthManager with valid token...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("Verification: is_token_expired returns False...")
        result = manager.is_token_expired()
        print(f"Comparing result: Expected False, Got {result}")
        assert result is False

    def test_is_token_expired_returns_false_when_expiring_soon_but_not_expired(self):
        """
        What it does: Verifies difference between expiring soon and actually expired.
        Purpose: Ensure token expiring in 5 minutes is NOT considered expired yet.
        """
        print("Setup: Creating KiroAuthManager with token expiring in 5 minutes...")
        manager = KiroAuthManager(refresh_token="test_token")
        manager._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        print("Verification: is_token_expiring_soon returns True (within threshold)...")
        assert manager.is_token_expiring_soon() is True

        print("Verification: is_token_expired returns False (not actually expired)...")
        result = manager.is_token_expired()
        print(f"Comparing result: Expected False, Got {result}")
        assert result is False


# =============================================================================
# Tests for graceful degradation in get_access_token() (SQLite mode)
# =============================================================================


class TestKiroAuthManagerGracefulDegradation:
    """Tests for graceful degradation when refresh fails in SQLite mode.

    Background: When kiro-cli refreshes tokens in memory without persisting to SQLite,
    the refresh_token in SQLite becomes stale. The gateway should gracefully fall back
    to using the access_token directly until it actually expires.
    """

    @pytest.mark.asyncio
    async def test_get_access_token_reloads_sqlite_when_expiring_soon(self, tmp_path):
        """
        What it does: Verifies SQLite is reloaded when token is expiring soon.
        Purpose: Pick up fresh tokens from kiro-cli before attempting refresh.
        """
        import sqlite3
        import json

        print("Setup: Creating SQLite database with fresh token...")
        db_file = tmp_path / "data.sqlite3"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE auth_kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Token that expires in 1 hour (fresh)
        fresh_token_data = {
            "access_token": "fresh_access_token",
            "refresh_token": "fresh_refresh_token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:token", json.dumps(fresh_token_data)),
        )

        registration_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:device-registration", json.dumps(registration_data)),
        )
        conn.commit()
        conn.close()

        print("Setup: Creating KiroAuthManager with expiring token...")
        manager = KiroAuthManager(sqlite_db=str(db_file))
        # Simulate token expiring soon (within threshold)
        manager._access_token = "old_expiring_token"
        manager._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        print("Verification: Token is expiring soon...")
        assert manager.is_token_expiring_soon() is True

        print("Action: Calling get_access_token()...")
        token = await manager.get_access_token()

        print("Verification: Got fresh token from SQLite reload...")
        print(f"Comparing token: Expected 'fresh_access_token', Got '{token}'")
        assert token == "fresh_access_token"

    @pytest.mark.asyncio
    async def test_get_access_token_graceful_fallback_when_refresh_fails_but_token_valid(
        self, tmp_path
    ):
        """
        What it does: Verifies graceful fallback when refresh fails with 400 but access_token still valid.
        Purpose: Use existing access_token until it actually expires when kiro-cli owns refresh.
        """
        import sqlite3
        import json

        print("Setup: Creating SQLite database...")
        db_file = tmp_path / "data.sqlite3"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE auth_kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Token that is expiring soon but NOT expired yet
        token_data = {
            "access_token": "still_valid_access_token",
            "refresh_token": "stale_refresh_token",
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=5)
            ).isoformat(),
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:token", json.dumps(token_data)),
        )

        registration_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:device-registration", json.dumps(registration_data)),
        )
        conn.commit()
        conn.close()

        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(sqlite_db=str(db_file))

        print("Verification: Token is expiring soon but NOT expired...")
        assert manager.is_token_expiring_soon() is True
        assert manager.is_token_expired() is False

        print("Setup: Mocking HTTP client to return 400 twice (stale refresh token)...")
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.text = '{"error":"invalid_request"}'
        mock_error_response.json = Mock(return_value={"error": "invalid_request"})
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_error_response
            )
        )

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling get_access_token() (expecting graceful fallback)...")
            token = await manager.get_access_token()

            print("Verification: Got existing access_token (graceful fallback)...")
            print(
                f"Comparing token: Expected 'still_valid_access_token', Got '{token}'"
            )
            assert token == "still_valid_access_token"

    @pytest.mark.asyncio
    async def test_get_access_token_raises_when_refresh_fails_and_token_expired(
        self, tmp_path
    ):
        """
        What it does: Verifies error is raised when refresh fails and access_token is expired.
        Purpose: Clear error message when user needs to run 'kiro-cli login'.
        """
        import sqlite3
        import json

        print("Setup: Creating SQLite database with expired token...")
        db_file = tmp_path / "data.sqlite3"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE auth_kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Token that is already expired
        token_data = {
            "access_token": "expired_access_token",
            "refresh_token": "stale_refresh_token",
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:token", json.dumps(token_data)),
        )

        registration_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "region": "us-east-1",
        }
        cursor.execute(
            "INSERT INTO auth_kv (key, value) VALUES (?, ?)",
            ("codewhisperer:odic:device-registration", json.dumps(registration_data)),
        )
        conn.commit()
        conn.close()

        print("Setup: Creating KiroAuthManager...")
        manager = KiroAuthManager(sqlite_db=str(db_file))

        print("Verification: Token is expired...")
        assert manager.is_token_expired() is True

        print("Setup: Mocking HTTP client to return 400 (stale refresh token)...")
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.text = '{"error":"invalid_request"}'
        mock_error_response.json = Mock(return_value={"error": "invalid_request"})
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_error_response
            )
        )

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling get_access_token() (expecting ValueError)...")
            with pytest.raises(ValueError) as exc_info:
                await manager.get_access_token()

            print(
                f"Verification: ValueError raised with helpful message: {exc_info.value}"
            )
            assert "kiro-cli login" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_access_token_non_sqlite_mode_propagates_400_error(self):
        """
        What it does: Verifies 400 error is propagated in non-SQLite mode.
        Purpose: Ensure graceful degradation only applies to SQLite mode.
        """
        print("Setup: Creating KiroAuthManager WITHOUT sqlite_db...")
        manager = KiroAuthManager(
            refresh_token="test_refresh",
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        manager._access_token = "expiring_token"
        manager._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        print("Verification: No sqlite_db set...")
        assert manager._sqlite_db is None

        print("Setup: Mocking HTTP client to return 400...")
        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.text = '{"error":"invalid_request"}'
        mock_error_response.json = Mock(return_value={"error": "invalid_request"})
        mock_error_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_error_response
            )
        )

        with patch("kiro.auth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            print("Action: Calling get_access_token() (expecting HTTPStatusError)...")
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await manager.get_access_token()

            print("Verification: 400 error was propagated (no graceful degradation)...")
            assert exc_info.value.response.status_code == 400
