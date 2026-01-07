# Tests for Kiro OpenAI Gateway

A comprehensive set of unit and integration tests for Kiro OpenAI Gateway, providing full coverage of all system components.

## Testing Philosophy: Complete Network Isolation

**The key principle of this test suite is 100% isolation from real network requests.**

This is achieved through a global, automatically applied fixture `block_all_network_calls` in `tests/conftest.py`. It intercepts and blocks any attempts by `httpx.AsyncClient` to establish connections at the application level.

**Benefits:**
1.  **Reliability**: Tests don't depend on external API availability or network state.
2.  **Speed**: Absence of real network delays makes test execution instant.
3.  **Security**: Guarantees that test runs never use real credentials.

Any attempt to make an unauthorized network call will result in immediate test failure with an error, ensuring strict isolation control.

## Running Tests

### Installing Dependencies

```bash
# Main project dependencies
pip install -r requirements.txt

# Additional testing dependencies
pip install pytest pytest-asyncio hypothesis
```

### Running All Tests

```bash
# Run the entire test suite
pytest

# Run with verbose output
pytest -v

# Run with verbose output and coverage
pytest -v -s --tb=short

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run a specific file
pytest tests/unit/test_auth_manager.py -v

# Run a specific test
pytest tests/unit/test_auth_manager.py::TestKiroAuthManagerInitialization::test_initialization_stores_credentials -v
```

### pytest Options

```bash
# Stop on first failure
pytest -x

# Show local variables on errors
pytest -l

# Run in parallel mode (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and utilities
├── unit/                            # Unit tests for individual components
│   ├── test_auth_manager.py        # KiroAuthManager tests
│   ├── test_cache.py               # ModelInfoCache tests
│   ├── test_config.py              # Configuration tests (LOG_LEVEL, etc.)
│   ├── test_converters.py          # OpenAI <-> Kiro converter tests
│   ├── test_debug_logger.py        # DebugLogger tests (off/errors/all modes)
│   ├── test_parsers.py             # AwsEventStreamParser tests
│   ├── test_streaming.py           # Streaming function tests
│   ├── test_thinking_parser.py     # ThinkingParser tests (FSM for thinking blocks)
│   ├── test_tokenizer.py           # Tokenizer tests (tiktoken)
│   ├── test_http_client.py         # KiroHttpClient tests
│   └── test_routes.py              # API endpoint tests
├── integration/                     # Integration tests for full flow
│   └── test_full_flow.py           # End-to-end tests
└── README.md                        # This file
```

## Test Coverage

### `conftest.py`

Shared fixtures and utilities for all tests:

**Environment Fixtures:**
- **`mock_env_vars()`**: Mocks environment variables (REFRESH_TOKEN, PROXY_API_KEY)
  - **What it does**: Isolates tests from real credentials
  - **Purpose**: Security and test reproducibility

**Data Fixtures:**
- **`valid_kiro_token()`**: Returns a mock Kiro access token
  - **What it does**: Provides a predictable token for tests
  - **Purpose**: Testing without real Kiro requests

- **`mock_kiro_token_response()`**: Factory for creating mock refreshToken responses
  - **What it does**: Generates Kiro auth endpoint response structure
  - **Purpose**: Testing various token refresh scenarios

- **`temp_creds_file()`**: Creates a temporary JSON file with credentials (Kiro Desktop format)
  - **What it does**: Provides a file for testing credentials loading
  - **Purpose**: Testing credentials file operations

- **`temp_aws_sso_creds_file()`**: Creates a temporary JSON file with AWS SSO OIDC credentials
  - **What it does**: Provides a file with clientId and clientSecret for testing AWS SSO auth
  - **Purpose**: Testing AWS SSO OIDC credentials loading

- **`temp_sqlite_db()`**: Creates a temporary SQLite database (kiro-cli format)
  - **What it does**: Provides a database with auth_kv table for testing SQLite loading
  - **Purpose**: Testing kiro-cli SQLite credentials loading

- **`temp_sqlite_db_token_only()`**: Creates SQLite database with token only (no device-registration)
  - **What it does**: Provides a partial database for testing error handling
  - **Purpose**: Testing partial SQLite data loading

- **`temp_sqlite_db_invalid_json()`**: Creates SQLite database with invalid JSON
  - **What it does**: Provides a database with corrupted data for testing error handling
  - **Purpose**: Testing JSON decode error handling

- **`mock_aws_sso_oidc_token_response()`**: Factory for creating mock AWS SSO OIDC token responses
  - **What it does**: Generates AWS SSO OIDC token endpoint response structure
  - **Purpose**: Testing various AWS SSO OIDC token refresh scenarios

- **`sample_openai_chat_request()`**: Factory for creating OpenAI requests
  - **What it does**: Generates valid chat completion requests
  - **Purpose**: Convenient creation of test requests with different parameters

**Security Fixtures:**
- **`valid_proxy_api_key()`**: Valid proxy API key
- **`invalid_proxy_api_key()`**: Invalid key for negative tests
- **`auth_headers()`**: Factory for creating Authorization headers

**HTTP Fixtures:**
- **`mock_httpx_client()`**: Mocked httpx.AsyncClient
  - **What it does**: Isolates tests from real HTTP requests
  - **Purpose**: Test speed and reliability

- **`mock_httpx_response()`**: Factory for creating mock HTTP responses
  - **What it does**: Creates configurable httpx.Response objects
  - **Purpose**: Testing various HTTP scenarios

**Application Fixtures:**
- **`clean_app()`**: Clean FastAPI app instance
  - **What it does**: Returns a "clean" application instance
  - **Purpose**: Ensure application state isolation between tests

- **`test_client()`**: Synchronous FastAPI TestClient
- **`async_test_client()`**: Asynchronous test client for async endpoints

---

### `tests/unit/test_auth_manager.py`

Unit tests for **KiroAuthManager** (Kiro token management).

#### `TestKiroAuthManagerInitialization`

- **`test_initialization_stores_credentials()`**:
  - **What it does**: Verifies correct credential storage during creation
  - **Purpose**: Ensure all constructor parameters are stored in private fields

- **`test_initialization_sets_correct_urls_for_region()`**:
  - **What it does**: Verifies URL formation based on region
  - **Purpose**: Ensure URLs are dynamically formed with the correct region

- **`test_initialization_generates_fingerprint()`**:
  - **What it does**: Verifies unique fingerprint generation
  - **Purpose**: Ensure fingerprint is generated and has correct format

#### `TestKiroAuthManagerCredentialsFile`

- **`test_load_credentials_from_file()`**:
  - **What it does**: Verifies credentials loading from JSON file
  - **Purpose**: Ensure data is correctly read from file

- **`test_load_credentials_file_not_found()`**:
  - **What it does**: Verifies handling of missing credentials file
  - **Purpose**: Ensure application doesn't crash when file is missing

#### `TestKiroAuthManagerTokenExpiration`

- **`test_is_token_expiring_soon_returns_true_when_no_expires_at()`**:
  - **What it does**: Verifies that without expires_at, token is considered expiring
  - **Purpose**: Ensure safe behavior when time information is missing

- **`test_is_token_expiring_soon_returns_true_when_expired()`**:
  - **What it does**: Verifies that expired token is correctly identified
  - **Purpose**: Ensure token in the past is considered expiring

- **`test_is_token_expiring_soon_returns_true_within_threshold()`**:
  - **What it does**: Verifies that token within threshold is considered expiring
  - **Purpose**: Ensure token is refreshed in advance (10 minutes before expiration)

- **`test_is_token_expiring_soon_returns_false_when_valid()`**:
  - **What it does**: Verifies that valid token is not considered expiring
  - **Purpose**: Ensure token far in the future doesn't require refresh

#### `TestKiroAuthManagerTokenRefresh`

- **`test_refresh_token_successful()`**:
  - **What it does**: Tests successful token refresh via Kiro API
  - **Purpose**: Verify correct setting of access_token and expires_at

- **`test_refresh_token_updates_refresh_token()`**:
  - **What it does**: Verifies refresh_token update from response
  - **Purpose**: Ensure new refresh_token is saved

- **`test_refresh_token_missing_access_token_raises()`**:
  - **What it does**: Verifies handling of response without accessToken
  - **Purpose**: Ensure exception is thrown for incorrect response

- **`test_refresh_token_no_refresh_token_raises()`**:
  - **What it does**: Verifies handling of missing refresh_token
  - **Purpose**: Ensure exception is thrown without refresh_token

#### `TestKiroAuthManagerGetAccessToken`

- **`test_get_access_token_refreshes_when_expired()`**:
  - **What it does**: Verifies automatic refresh of expired token
  - **Purpose**: Ensure stale token is refreshed before return

- **`test_get_access_token_returns_valid_without_refresh()`**:
  - **What it does**: Verifies return of valid token without extra requests
  - **Purpose**: Optimization - don't make requests if token is still valid

- **`test_get_access_token_thread_safety()`**:
  - **What it does**: Verifies thread safety via asyncio.Lock
  - **Purpose**: Prevent race conditions during parallel calls

#### `TestKiroAuthManagerForceRefresh`

- **`test_force_refresh_updates_token()`**:
  - **What it does**: Verifies forced token refresh
  - **Purpose**: Ensure force_refresh always refreshes token

#### `TestKiroAuthManagerProperties`

- **`test_profile_arn_property()`**:
  - **What it does**: Verifies profile_arn property
  - **Purpose**: Ensure profile_arn is accessible via property

- **`test_region_property()`**:
  - **What it does**: Verifies region property
  - **Purpose**: Ensure region is accessible via property

- **`test_api_host_property()`**:
  - **What it does**: Verifies api_host property
  - **Purpose**: Ensure api_host is formed correctly

- **`test_fingerprint_property()`**:
  - **What it does**: Verifies fingerprint property
  - **Purpose**: Ensure fingerprint is accessible via property

#### `TestAuthTypeEnum`

Tests for AuthType enum (AWS SSO OIDC support).

- **`test_auth_type_enum_values()`**:
  - **What it does**: Verifies AuthType enum contains KIRO_DESKTOP and AWS_SSO_OIDC
  - **Purpose**: Ensure enum values are correctly defined

#### `TestKiroAuthManagerDetectAuthType`

Tests for `_detect_auth_type()` method.

- **`test_detect_auth_type_kiro_desktop_when_no_client_credentials()`**:
  - **What it does**: Verifies KIRO_DESKTOP is detected without clientId/clientSecret
  - **Purpose**: Ensure default auth type is KIRO_DESKTOP

- **`test_detect_auth_type_aws_sso_oidc_when_client_credentials_present()`**:
  - **What it does**: Verifies AWS_SSO_OIDC is detected with clientId and clientSecret
  - **Purpose**: Ensure AWS SSO OIDC is auto-detected from credentials

- **`test_detect_auth_type_kiro_desktop_when_only_client_id()`**:
  - **What it does**: Verifies KIRO_DESKTOP when only clientId is present
  - **Purpose**: Ensure both clientId AND clientSecret are required for AWS SSO OIDC

- **`test_detect_auth_type_kiro_desktop_when_only_client_secret()`**:
  - **What it does**: Verifies KIRO_DESKTOP when only clientSecret is present
  - **Purpose**: Ensure both clientId AND clientSecret are required for AWS SSO OIDC

#### `TestKiroAuthManagerAwsSsoCredentialsFile`

Tests for loading AWS SSO OIDC credentials from JSON file.

- **`test_load_credentials_from_file_with_client_id_and_secret()`**:
  - **What it does**: Verifies clientId and clientSecret are loaded from JSON file
  - **Purpose**: Ensure AWS SSO fields are correctly read from file

- **`test_load_credentials_from_file_auto_detects_aws_sso_oidc()`**:
  - **What it does**: Verifies auth_type is auto-detected as AWS_SSO_OIDC after loading
  - **Purpose**: Ensure auth type is automatically determined from file contents

- **`test_load_kiro_desktop_file_stays_kiro_desktop()`**:
  - **What it does**: Verifies Kiro Desktop file doesn't change auth type to AWS SSO
  - **Purpose**: Ensure file without clientId/clientSecret stays KIRO_DESKTOP

#### `TestKiroAuthManagerSqliteCredentials`

Tests for loading credentials from SQLite database (kiro-cli format).

- **`test_load_credentials_from_sqlite_success()`**:
  - **What it does**: Verifies successful credentials loading from SQLite
  - **Purpose**: Ensure all data is correctly read from database

- **`test_load_credentials_from_sqlite_file_not_found()`**:
  - **What it does**: Verifies handling of missing SQLite file
  - **Purpose**: Ensure application doesn't crash when file is missing

- **`test_load_credentials_from_sqlite_loads_token_data()`**:
  - **What it does**: Verifies token data loading from SQLite
  - **Purpose**: Ensure access_token, refresh_token, region are loaded

- **`test_load_credentials_from_sqlite_loads_device_registration()`**:
  - **What it does**: Verifies device registration loading from SQLite
  - **Purpose**: Ensure client_id and client_secret are loaded

- **`test_load_credentials_from_sqlite_auto_detects_aws_sso_oidc()`**:
  - **What it does**: Verifies auth_type is auto-detected as AWS_SSO_OIDC after loading
  - **Purpose**: Ensure auth type is automatically determined from SQLite contents

- **`test_load_credentials_from_sqlite_handles_missing_registration_key()`**:
  - **What it does**: Verifies handling of missing device-registration key
  - **Purpose**: Ensure application doesn't crash without device-registration

- **`test_load_credentials_from_sqlite_handles_invalid_json()`**:
  - **What it does**: Verifies handling of invalid JSON in SQLite
  - **Purpose**: Ensure application doesn't crash with invalid JSON

- **`test_sqlite_takes_priority_over_json_file()`**:
  - **What it does**: Verifies SQLite takes priority over JSON file
  - **Purpose**: Ensure SQLite is loaded instead of JSON when both are specified

#### `TestKiroAuthManagerRefreshTokenRouting`

Tests for `_refresh_token_request()` routing based on auth_type.

- **`test_refresh_token_request_routes_to_kiro_desktop()`**:
  - **What it does**: Verifies KIRO_DESKTOP calls _refresh_token_kiro_desktop
  - **Purpose**: Ensure correct routing for Kiro Desktop auth

- **`test_refresh_token_request_routes_to_aws_sso_oidc()`**:
  - **What it does**: Verifies AWS_SSO_OIDC calls _refresh_token_aws_sso_oidc
  - **Purpose**: Ensure correct routing for AWS SSO OIDC auth

#### `TestKiroAuthManagerAwsSsoOidcRefresh`

Tests for `_refresh_token_aws_sso_oidc()` method.

- **`test_refresh_token_aws_sso_oidc_success()`**:
  - **What it does**: Tests successful token refresh via AWS SSO OIDC
  - **Purpose**: Verify access_token and expires_at are set on success

- **`test_refresh_token_aws_sso_oidc_raises_without_refresh_token()`**:
  - **What it does**: Verifies ValueError is raised without refresh_token
  - **Purpose**: Ensure exception is thrown without refresh_token

- **`test_refresh_token_aws_sso_oidc_raises_without_client_id()`**:
  - **What it does**: Verifies ValueError is raised without client_id
  - **Purpose**: Ensure exception is thrown without client_id

- **`test_refresh_token_aws_sso_oidc_raises_without_client_secret()`**:
  - **What it does**: Verifies ValueError is raised without client_secret
  - **Purpose**: Ensure exception is thrown without client_secret

- **`test_refresh_token_aws_sso_oidc_uses_correct_endpoint()`**:
  - **What it does**: Verifies correct endpoint is used
  - **Purpose**: Ensure request goes to https://oidc.{region}.amazonaws.com/token

- **`test_refresh_token_aws_sso_oidc_uses_form_urlencoded()`**:
  - **What it does**: Verifies form-urlencoded format is used
  - **Purpose**: Ensure Content-Type = application/x-www-form-urlencoded

- **`test_refresh_token_aws_sso_oidc_sends_correct_grant_type()`**:
  - **What it does**: Verifies correct grant_type is sent
  - **Purpose**: Ensure grant_type=refresh_token

- **`test_refresh_token_aws_sso_oidc_updates_tokens()`**:
  - **What it does**: Verifies access_token and refresh_token are updated
  - **Purpose**: Ensure both tokens are updated from response

- **`test_refresh_token_aws_sso_oidc_calculates_expiration()`**:
  - **What it does**: Verifies expiration time is calculated correctly
  - **Purpose**: Ensure expires_at is calculated based on expiresIn

- **`test_refresh_token_aws_sso_oidc_does_not_send_scopes()`**:
  - **What it does**: Verifies that scopes are NOT sent in refresh request even when loaded from SQLite
  - **Purpose**: Per OAuth 2.0 RFC 6749 Section 6, scope is optional in refresh and AWS SSO OIDC returns invalid_request if scope is sent (fix for issue #12 with @mzazon)

- **`test_refresh_token_aws_sso_oidc_works_without_scopes()`**:
  - **What it does**: Verifies refresh works when scopes are None
  - **Purpose**: Ensure backward compatibility with credentials that don't have scopes (JSON file users like @uratmangun)

#### `TestKiroAuthManagerAuthTypeProperty`

Tests for auth_type property and constructor with new parameters.

- **`test_auth_type_property_returns_correct_value()`**:
  - **What it does**: Verifies auth_type property returns correct value
  - **Purpose**: Ensure property works correctly

- **`test_init_with_client_id_and_secret()`**:
  - **What it does**: Verifies initialization with client_id and client_secret
  - **Purpose**: Ensure parameters are stored in private fields

- **`test_init_with_sqlite_db_parameter()`**:
  - **What it does**: Verifies initialization with sqlite_db parameter
  - **Purpose**: Ensure data is loaded from SQLite

---

### `tests/unit/test_cache.py`

Unit tests for **ModelInfoCache** (model metadata cache). **23 tests.**

#### `TestModelInfoCacheInitialization`

- **`test_initialization_creates_empty_cache()`**:
  - **What it does**: Verifies that cache is created empty
  - **Purpose**: Ensure correct initialization

- **`test_initialization_with_custom_ttl()`**:
  - **What it does**: Verifies cache creation with custom TTL
  - **Purpose**: Ensure TTL can be configured

- **`test_initialization_last_update_is_none()`**:
  - **What it does**: Verifies that last_update_time is initially None
  - **Purpose**: Ensure update time is not set before first update

#### `TestModelInfoCacheUpdate`

- **`test_update_populates_cache()`**:
  - **What it does**: Verifies cache population with data
  - **Purpose**: Ensure update() correctly saves models

- **`test_update_sets_last_update_time()`**:
  - **What it does**: Verifies setting of last update time
  - **Purpose**: Ensure last_update_time is set after update

- **`test_update_replaces_existing_data()`**:
  - **What it does**: Verifies data replacement on repeated update
  - **Purpose**: Ensure old data is completely replaced

- **`test_update_with_empty_list()`**:
  - **What it does**: Verifies update with empty list
  - **Purpose**: Ensure cache is cleared on empty update

#### `TestModelInfoCacheGet`

- **`test_get_returns_model_info()`**:
  - **What it does**: Verifies retrieval of model information
  - **Purpose**: Ensure get() returns correct data

- **`test_get_returns_none_for_unknown_model()`**:
  - **What it does**: Verifies None return for unknown model
  - **Purpose**: Ensure get() doesn't crash when model is missing

- **`test_get_from_empty_cache()`**:
  - **What it does**: Verifies get() from empty cache
  - **Purpose**: Ensure empty cache doesn't cause errors

#### `TestModelInfoCacheGetMaxInputTokens`

- **`test_get_max_input_tokens_returns_value()`**:
  - **What it does**: Verifies retrieval of maxInputTokens for model
  - **Purpose**: Ensure value is extracted from tokenLimits

- **`test_get_max_input_tokens_returns_default_for_unknown()`**:
  - **What it does**: Verifies default return for unknown model
  - **Purpose**: Ensure DEFAULT_MAX_INPUT_TOKENS is returned

- **`test_get_max_input_tokens_returns_default_when_no_token_limits()`**:
  - **What it does**: Verifies default return when tokenLimits is missing
  - **Purpose**: Ensure model without tokenLimits doesn't break logic

- **`test_get_max_input_tokens_returns_default_when_max_input_is_none()`**:
  - **What it does**: Verifies default return when maxInputTokens=None
  - **Purpose**: Ensure None in tokenLimits is handled correctly

#### `TestModelInfoCacheIsEmpty` and `TestModelInfoCacheIsStale`

- **`test_is_empty_returns_true_for_new_cache()`**: Verifies is_empty() for new cache
- **`test_is_empty_returns_false_after_update()`**: Verifies is_empty() after population
- **`test_is_stale_returns_true_for_new_cache()`**: Verifies is_stale() for new cache
- **`test_is_stale_returns_false_after_recent_update()`**: Verifies is_stale() right after update
- **`test_is_stale_returns_true_after_ttl_expires()`**: Verifies is_stale() after TTL expiration

#### `TestModelInfoCacheGetAllModelIds`

- **`test_get_all_model_ids_returns_empty_for_new_cache()`**: Verifies get_all_model_ids() for empty cache
- **`test_get_all_model_ids_returns_all_ids()`**: Verifies get_all_model_ids() for populated cache

#### `TestModelInfoCacheThreadSafety`

- **`test_concurrent_updates_dont_corrupt_cache()`**:
  - **What it does**: Verifies thread safety during parallel updates
  - **Purpose**: Ensure asyncio.Lock protects against race conditions

- **`test_concurrent_reads_are_safe()`**:
  - **What it does**: Verifies safety of parallel reads
  - **Purpose**: Ensure multiple get() calls don't cause issues

---

### `tests/unit/test_config.py`

Unit tests for **configuration module** (loading settings from environment variables). **13 tests.**

#### `TestLogLevelConfig`

Tests for LOG_LEVEL configuration.

- **`test_default_log_level_is_info()`**:
  - **What it does**: Verifies that default LOG_LEVEL is INFO
  - **Purpose**: Ensure INFO is used without environment variable

- **`test_log_level_from_environment()`**:
  - **What it does**: Verifies LOG_LEVEL loading from environment variable
  - **Purpose**: Ensure value from environment is used

- **`test_log_level_uppercase_conversion()`**:
  - **What it does**: Verifies LOG_LEVEL conversion to uppercase
  - **Purpose**: Ensure lowercase value is converted to uppercase

- **`test_log_level_trace()`**:
  - **What it does**: Verifies LOG_LEVEL=TRACE setting
  - **Purpose**: Ensure TRACE level is supported

- **`test_log_level_error()`**:
  - **What it does**: Verifies LOG_LEVEL=ERROR setting
  - **Purpose**: Ensure ERROR level is supported

- **`test_log_level_critical()`**:
  - **What it does**: Verifies LOG_LEVEL=CRITICAL setting
  - **Purpose**: Ensure CRITICAL level is supported

#### `TestToolDescriptionMaxLengthConfig`

Tests for TOOL_DESCRIPTION_MAX_LENGTH configuration.

- **`test_default_tool_description_max_length()`**:
  - **What it does**: Verifies default value for TOOL_DESCRIPTION_MAX_LENGTH
  - **Purpose**: Ensure default is 10000

- **`test_tool_description_max_length_from_environment()`**:
  - **What it does**: Verifies TOOL_DESCRIPTION_MAX_LENGTH loading from environment
  - **Purpose**: Ensure value from environment is used

- **`test_tool_description_max_length_zero_disables()`**:
  - **What it does**: Verifies that 0 disables the feature
  - **Purpose**: Ensure TOOL_DESCRIPTION_MAX_LENGTH=0 works

#### `TestTimeoutConfigurationWarning`

Tests for `_warn_timeout_configuration()` function.

- **`test_no_warning_when_first_token_less_than_streaming()`**:
  - **What it does**: Verifies no warning when FIRST_TOKEN_TIMEOUT < STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure correct configuration doesn't trigger warning

- **`test_warning_when_first_token_equals_streaming()`**:
  - **What it does**: Verifies warning when FIRST_TOKEN_TIMEOUT == STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure equal timeouts trigger warning

- **`test_warning_when_first_token_greater_than_streaming()`**:
  - **What it does**: Verifies warning when FIRST_TOKEN_TIMEOUT > STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure suboptimal configuration triggers warning with timeout values

- **`test_warning_contains_recommendation()`**:
  - **What it does**: Verifies warning contains recommendation text
  - **Purpose**: Ensure user gets helpful information about correct configuration

#### `TestAwsSsoOidcUrlConfig`

Tests for AWS SSO OIDC URL configuration.

- **`test_aws_sso_oidc_url_template_exists()`**:
  - **What it does**: Verifies AWS_SSO_OIDC_URL_TEMPLATE constant exists
  - **Purpose**: Ensure the template is defined in config

- **`test_get_aws_sso_oidc_url_returns_correct_url()`**:
  - **What it does**: Verifies get_aws_sso_oidc_url returns correct URL
  - **Purpose**: Ensure the function formats URL correctly

- **`test_get_aws_sso_oidc_url_with_different_regions()`**:
  - **What it does**: Verifies URL generation for different regions
  - **Purpose**: Ensure the function works with various AWS regions

#### `TestKiroCliDbFileConfig`

Tests for KIRO_CLI_DB_FILE configuration.

- **`test_kiro_cli_db_file_config_exists()`**:
  - **What it does**: Verifies KIRO_CLI_DB_FILE constant exists
  - **Purpose**: Ensure the config parameter is defined

- **`test_kiro_cli_db_file_from_environment()`**:
  - **What it does**: Verifies loading KIRO_CLI_DB_FILE from environment variable
  - **Purpose**: Ensure the value from environment is used

---

### `tests/unit/test_debug_logger.py`

Unit tests for **DebugLogger** (debug request logging). **26 tests.**

#### `TestDebugLoggerModeOff`

Tests for DEBUG_MODE=off mode.

- **`test_prepare_new_request_does_nothing()`**:
  - **What it does**: Verifies that prepare_new_request does nothing in off mode
  - **Purpose**: Ensure directory is not created in off mode

- **`test_log_request_body_does_nothing()`**:
  - **What it does**: Verifies that log_request_body does nothing in off mode
  - **Purpose**: Ensure data is not written

#### `TestDebugLoggerModeAll`

Tests for DEBUG_MODE=all mode.

- **`test_prepare_new_request_clears_directory()`**:
  - **What it does**: Verifies that prepare_new_request clears directory in all mode
  - **Purpose**: Ensure old logs are deleted

- **`test_log_request_body_writes_immediately()`**:
  - **What it does**: Verifies that log_request_body writes immediately to file in all mode
  - **Purpose**: Ensure data is written immediately

- **`test_log_kiro_request_body_writes_immediately()`**:
  - **What it does**: Verifies that log_kiro_request_body writes immediately to file in all mode
  - **Purpose**: Ensure Kiro payload is written immediately

- **`test_log_raw_chunk_appends_to_file()`**:
  - **What it does**: Verifies that log_raw_chunk appends to file in all mode
  - **Purpose**: Ensure chunks accumulate

#### `TestDebugLoggerModeErrors`

Tests for DEBUG_MODE=errors mode.

- **`test_log_request_body_buffers_data()`**:
  - **What it does**: Verifies that log_request_body buffers data in errors mode
  - **Purpose**: Ensure data is not written immediately

- **`test_flush_on_error_writes_buffers()`**:
  - **What it does**: Verifies that flush_on_error writes buffers to files
  - **Purpose**: Ensure data is saved on error

- **`test_flush_on_error_clears_buffers()`**:
  - **What it does**: Verifies that flush_on_error clears buffers after writing
  - **Purpose**: Ensure buffers don't accumulate between requests

- **`test_discard_buffers_clears_without_writing()`**:
  - **What it does**: Verifies that discard_buffers clears buffers without writing
  - **Purpose**: Ensure successful requests don't leave logs

- **`test_flush_on_error_writes_error_info_in_mode_all()`**:
  - **What it does**: Verifies that flush_on_error writes error_info.json in all mode
  - **Purpose**: Ensure error information is saved in both modes

#### `TestDebugLoggerLogErrorInfo`

Tests for log_error_info() method.

- **`test_log_error_info_writes_in_mode_all()`**:
  - **What it does**: Verifies that log_error_info writes file in all mode
  - **Purpose**: Ensure error_info.json is created on errors

- **`test_log_error_info_writes_in_mode_errors()`**:
  - **What it does**: Verifies that log_error_info writes file in errors mode
  - **Purpose**: Ensure method works in both modes

- **`test_log_error_info_does_nothing_in_mode_off()`**:
  - **What it does**: Verifies that log_error_info does nothing in off mode
  - **Purpose**: Ensure files are not created in off mode

#### `TestDebugLoggerHelperMethods`

Tests for DebugLogger helper methods.

- **`test_is_enabled_returns_true_for_errors()`**: Verifies _is_enabled() for errors mode
- **`test_is_enabled_returns_true_for_all()`**: Verifies _is_enabled() for all mode
- **`test_is_enabled_returns_false_for_off()`**: Verifies _is_enabled() for off mode
- **`test_is_immediate_write_returns_true_for_all()`**: Verifies _is_immediate_write() for all mode
- **`test_is_immediate_write_returns_false_for_errors()`**: Verifies _is_immediate_write() for errors mode

#### `TestDebugLoggerJsonHandling`

Tests for JSON handling in DebugLogger.

- **`test_log_request_body_formats_json_pretty()`**:
  - **What it does**: Verifies that JSON is formatted prettily
  - **Purpose**: Ensure JSON is readable in file

- **`test_log_request_body_handles_invalid_json()`**:
  - **What it does**: Verifies handling of invalid JSON
  - **Purpose**: Ensure invalid JSON is written as-is

#### `TestDebugLoggerAppLogsCapture`

Tests for application log capture (app_logs.txt).

- **`test_prepare_new_request_sets_up_log_capture()`**:
  - **What it does**: Verifies that prepare_new_request sets up log capture
  - **Purpose**: Ensure sink for logs is created

- **`test_flush_on_error_writes_app_logs_in_mode_errors()`**:
  - **What it does**: Verifies that flush_on_error writes app_logs.txt in errors mode
  - **Purpose**: Ensure application logs are saved on errors

- **`test_discard_buffers_saves_logs_in_mode_all()`**:
  - **What it does**: Verifies that discard_buffers saves logs in all mode
  - **Purpose**: Ensure even successful requests save logs in all mode

- **`test_discard_buffers_does_not_save_logs_in_mode_errors()`**:
  - **What it does**: Verifies that discard_buffers does NOT save logs in errors mode
  - **Purpose**: Ensure successful requests don't leave logs in errors mode

- **`test_clear_app_logs_buffer_removes_sink()`**:
  - **What it does**: Verifies that _clear_app_logs_buffer removes sink
  - **Purpose**: Ensure sink is correctly removed

- **`test_app_logs_not_saved_when_empty()`**:
  - **What it does**: Verifies that empty logs don't create file
  - **Purpose**: Ensure app_logs.txt is not created if there are no logs

---

### `tests/unit/test_converters.py`

Unit tests for **OpenAI <-> Kiro** converters. **84 tests.**

#### `TestExtractTextContent`

- **`test_extracts_from_string()`**: Verifies text extraction from string
- **`test_extracts_from_none()`**: Verifies None handling
- **`test_extracts_from_list_with_text_type()`**: Verifies extraction from list with type=text
- **`test_extracts_from_list_with_text_key()`**: Verifies extraction from list with text key
- **`test_extracts_from_list_with_strings()`**: Verifies extraction from list of strings
- **`test_extracts_from_mixed_list()`**: Verifies extraction from mixed list
- **`test_converts_other_types_to_string()`**: Verifies conversion of other types to string
- **`test_handles_empty_list()`**: Verifies empty list handling

#### `TestMergeAdjacentMessages`

- **`test_merges_adjacent_user_messages()`**: Verifies merging of adjacent user messages
- **`test_preserves_alternating_messages()`**: Verifies preservation of alternating messages
- **`test_handles_empty_list()`**: Verifies empty list handling
- **`test_handles_single_message()`**: Verifies single message handling
- **`test_merges_multiple_adjacent_groups()`**: Verifies merging of multiple groups

**New tests for tool message handling (role="tool"):**

- **`test_converts_tool_message_to_user_with_tool_result()`**:
  - **What it does**: Verifies conversion of tool message to user message with tool_result
  - **Purpose**: Ensure role="tool" is converted to user message with tool_results content

- **`test_converts_multiple_tool_messages_to_single_user_message()`**:
  - **What it does**: Verifies merging of multiple tool messages into single user message
  - **Purpose**: Ensure multiple tool results are merged into one user message

- **`test_tool_message_followed_by_user_message()`**:
  - **What it does**: Verifies tool message before user message
  - **Purpose**: Ensure tool results and user message are merged

- **`test_assistant_tool_user_sequence()`**:
  - **What it does**: Verifies assistant -> tool -> user sequence
  - **Purpose**: Ensure tool message is correctly inserted between assistant and user

- **`test_tool_message_with_empty_content()`**:
  - **What it does**: Verifies tool message with empty content
  - **Purpose**: Ensure empty result is replaced with "(empty result)"

- **`test_tool_message_with_none_tool_call_id()`**:
  - **What it does**: Verifies tool message without tool_call_id
  - **Purpose**: Ensure missing tool_call_id is replaced with empty string

- **`test_merges_list_contents_correctly()`**:
  - **What it does**: Verifies list contents merging
  - **Purpose**: Ensure lists are merged correctly

- **`test_merges_adjacent_assistant_tool_calls()`**:
  - **What it does**: Verifies tool_calls merging when merging adjacent assistant messages
  - **Purpose**: Ensure tool_calls from all assistant messages are preserved when merging

- **`test_merges_three_adjacent_assistant_tool_calls()`**:
  - **What it does**: Verifies tool_calls merging from three assistant messages
  - **Purpose**: Ensure all tool_calls are preserved when merging more than two messages

- **`test_merges_assistant_with_and_without_tool_calls()`**:
  - **What it does**: Verifies merging assistant with and without tool_calls
  - **Purpose**: Ensure tool_calls are correctly initialized when merging

#### `TestBuildKiroPayloadToolCallsIntegration`

Integration tests for full tool_calls flow from OpenAI to Kiro format.

- **`test_multiple_assistant_tool_calls_with_results()`**:
  - **What it does**: Verifies full scenario with multiple assistant tool_calls and their results
  - **Purpose**: Ensure all toolUses and toolResults are correctly linked in Kiro payload

#### `TestBuildKiroHistory`

- **`test_builds_user_message()`**: Verifies user message building
- **`test_builds_assistant_message()`**: Verifies assistant message building
- **`test_ignores_system_messages()`**: Verifies system message ignoring
- **`test_builds_conversation_history()`**: Verifies full conversation history building
- **`test_handles_empty_list()`**: Verifies empty list handling

#### `TestExtractToolResults` and `TestExtractToolUses`

- **`test_extracts_tool_results_from_list()`**: Verifies tool results extraction from list
- **`test_returns_empty_for_string_content()`**: Verifies empty list return for string
- **`test_extracts_from_tool_calls_field()`**: Verifies extraction from tool_calls field
- **`test_extracts_from_content_list()`**: Verifies extraction from content list

#### `TestProcessToolsWithLongDescriptions`

Tests for tools processing function with long descriptions (Tool Documentation Reference Pattern).

- **`test_returns_none_and_empty_string_for_none_tools()`**:
  - **What it does**: Verifies handling of None instead of tools list
  - **Purpose**: Ensure None returns (None, "")

- **`test_returns_none_and_empty_string_for_empty_list()`**:
  - **What it does**: Verifies handling of empty tools list
  - **Purpose**: Ensure empty list returns (None, "")

- **`test_short_description_unchanged()`**:
  - **What it does**: Verifies that short descriptions are not changed
  - **Purpose**: Ensure tools with short descriptions remain as-is

- **`test_long_description_moved_to_system_prompt()`**:
  - **What it does**: Verifies moving long description to system prompt
  - **Purpose**: Ensure long descriptions are moved correctly with reference in tool

- **`test_mixed_short_and_long_descriptions()`**:
  - **What it does**: Verifies handling of mixed tools list
  - **Purpose**: Ensure short ones stay, long ones are moved

- **`test_preserves_tool_parameters()`**:
  - **What it does**: Verifies parameters preservation when moving description
  - **Purpose**: Ensure parameters are not lost

- **`test_disabled_when_limit_is_zero()`**:
  - **What it does**: Verifies feature disabling when limit is 0
  - **Purpose**: Ensure tools are not changed when TOOL_DESCRIPTION_MAX_LENGTH=0

- **`test_non_function_tools_unchanged()`**:
  - **What it does**: Verifies that non-function tools are not changed
  - **Purpose**: Ensure only function tools are processed

- **`test_multiple_long_descriptions_all_moved()`**:
  - **What it does**: Verifies moving multiple long descriptions
  - **Purpose**: Ensure all long descriptions are moved

- **`test_empty_description_unchanged()`**:
  - **What it does**: Verifies handling of empty description
  - **Purpose**: Ensure empty description doesn't cause errors

- **`test_none_description_unchanged()`**:
  - **What it does**: Verifies handling of None description
  - **Purpose**: Ensure None description doesn't cause errors

#### `TestSanitizeJsonSchema`

Tests for `_sanitize_json_schema` function that cleans JSON Schema from fields not supported by Kiro API.

- **`test_returns_empty_dict_for_none()`**:
  - **What it does**: Verifies None handling
  - **Purpose**: Ensure None returns empty dict

- **`test_returns_empty_dict_for_empty_dict()`**:
  - **What it does**: Verifies empty dict handling
  - **Purpose**: Ensure empty dict is returned as-is

- **`test_removes_empty_required_array()`**:
  - **What it does**: Verifies removal of empty required array
  - **Purpose**: Ensure `required: []` is removed from schema (critical test for Cline bug)

- **`test_preserves_non_empty_required_array()`**:
  - **What it does**: Verifies preservation of non-empty required array
  - **Purpose**: Ensure required with elements is preserved

- **`test_removes_additional_properties()`**:
  - **What it does**: Verifies additionalProperties removal
  - **Purpose**: Ensure additionalProperties is removed from schema

- **`test_removes_both_empty_required_and_additional_properties()`**:
  - **What it does**: Verifies removal of both problematic fields
  - **Purpose**: Ensure both fields are removed simultaneously (real scenario from Cline)

- **`test_recursively_sanitizes_nested_properties()`**:
  - **What it does**: Verifies recursive cleaning of nested properties
  - **Purpose**: Ensure nested schemas are also cleaned

- **`test_recursively_sanitizes_dict_values()`**:
  - **What it does**: Verifies recursive cleaning of dict values
  - **Purpose**: Ensure any nested dicts are cleaned

- **`test_sanitizes_items_in_lists()`**:
  - **What it does**: Verifies cleaning of items in lists (anyOf, oneOf)
  - **Purpose**: Ensure list items are also cleaned

- **`test_preserves_non_dict_list_items()`**:
  - **What it does**: Verifies preservation of non-dict items in lists
  - **Purpose**: Ensure strings and other types in lists are preserved

- **`test_complex_real_world_schema()`**:
  - **What it does**: Verifies cleaning of real complex schema from Cline
  - **Purpose**: Ensure real schemas are processed correctly

#### `TestBuildUserInputContext`

- **`test_builds_tools_context()`**: Verifies context building with tools
- **`test_returns_empty_for_no_tools()`**: Verifies empty context return without tools

**New tests for empty description placeholder (Cline bug fix):**

- **`test_empty_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies empty description replacement with placeholder
  - **Purpose**: Ensure empty description is replaced with "Tool: {name}" (critical test for Cline bug with focus_chain)

- **`test_whitespace_only_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies whitespace-only description replacement with placeholder
  - **Purpose**: Ensure description with only spaces is replaced

- **`test_none_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies None description replacement with placeholder
  - **Purpose**: Ensure None description is replaced with "Tool: {name}"

- **`test_non_empty_description_preserved()`**:
  - **What it does**: Verifies non-empty description preservation
  - **Purpose**: Ensure normal description is not changed

- **`test_sanitizes_tool_parameters()`**:
  - **What it does**: Verifies parameters cleaning from problematic fields
  - **Purpose**: Ensure _sanitize_json_schema is applied to parameters

- **`test_mixed_tools_with_empty_and_normal_descriptions()`**:
  - **What it does**: Verifies handling of mixed tools list
  - **Purpose**: Ensure empty descriptions are replaced while normal ones are preserved (real scenario from Cline)

#### `TestInjectThinkingTags`

Tests for inject_thinking_tags function with thinking instruction.

- **`test_returns_original_content_when_disabled()`**:
  - **What it does**: Verifies that content is returned unchanged when fake reasoning is disabled
  - **Purpose**: Ensure no modification occurs when FAKE_REASONING_ENABLED=False

- **`test_injects_tags_when_enabled()`**:
  - **What it does**: Verifies that thinking tags are injected when enabled
  - **Purpose**: Ensure tags are prepended to content when FAKE_REASONING_ENABLED=True

- **`test_injects_thinking_instruction_tag()`**:
  - **What it does**: Verifies that thinking_instruction tag is injected
  - **Purpose**: Ensure the quality improvement prompt is included

- **`test_thinking_instruction_contains_english_directive()`**:
  - **What it does**: Verifies that thinking instruction includes English language directive
  - **Purpose**: Ensure model is instructed to think in English for better reasoning quality

- **`test_thinking_instruction_contains_systematic_approach()`**:
  - **What it does**: Verifies that thinking instruction includes systematic approach guidance
  - **Purpose**: Ensure model is instructed to think systematically

- **`test_thinking_instruction_contains_understanding_step()`**:
  - **What it does**: Verifies that thinking instruction includes understanding step
  - **Purpose**: Ensure model is instructed to understand the problem first

- **`test_thinking_instruction_contains_alternatives_consideration()`**:
  - **What it does**: Verifies that thinking instruction includes alternatives consideration
  - **Purpose**: Ensure model is instructed to consider multiple approaches

- **`test_thinking_instruction_contains_edge_cases()`**:
  - **What it does**: Verifies that thinking instruction includes edge cases consideration
  - **Purpose**: Ensure model is instructed to think about edge cases and potential issues

- **`test_thinking_instruction_contains_verification_step()`**:
  - **What it does**: Verifies that thinking instruction includes verification step
  - **Purpose**: Ensure model is instructed to verify reasoning before concluding

- **`test_thinking_instruction_contains_assumptions_challenge()`**:
  - **What it does**: Verifies that thinking instruction includes assumptions challenge
  - **Purpose**: Ensure model is instructed to challenge initial assumptions

- **`test_thinking_instruction_contains_quality_over_speed()`**:
  - **What it does**: Verifies that thinking instruction emphasizes quality over speed
  - **Purpose**: Ensure model is instructed to prioritize quality of thought

- **`test_uses_configured_max_tokens()`**:
  - **What it does**: Verifies that FAKE_REASONING_MAX_TOKENS config value is used
  - **Purpose**: Ensure the configured max tokens value is injected into the tag

- **`test_preserves_empty_content()`**:
  - **What it does**: Verifies that empty content is handled correctly
  - **Purpose**: Ensure empty string doesn't cause issues

- **`test_preserves_multiline_content()`**:
  - **What it does**: Verifies that multiline content is preserved correctly
  - **Purpose**: Ensure newlines in original content are not corrupted

- **`test_preserves_special_characters()`**:
  - **What it does**: Verifies that special characters in content are preserved
  - **Purpose**: Ensure XML-like content in user message doesn't break injection

- **`test_tag_order_is_correct()`**:
  - **What it does**: Verifies that tags are in the correct order
  - **Purpose**: Ensure thinking_mode comes first, then max_thinking_length, then instruction, then content

#### `TestBuildKiroPayload`

- **`test_builds_simple_payload()`**: Verifies simple payload building
- **`test_includes_system_prompt_in_first_message()`**: Verifies system prompt addition
- **`test_builds_history_for_multi_turn()`**: Verifies history building for multi-turn
- **`test_handles_assistant_as_last_message()`**: Verifies handling of assistant as last message
- **`test_raises_for_empty_messages()`**: Verifies exception throwing for empty messages
- **`test_uses_continue_for_empty_content()`**: Verifies "Continue" usage for empty content
- **`test_maps_model_id_correctly()`**: Verifies external model ID mapping to internal
- **`test_long_tool_description_added_to_system_prompt()`**:
  - **What it does**: Verifies long tool descriptions integration in payload
  - **Purpose**: Ensure long descriptions are added to system prompt in payload

---

### `tests/unit/test_parsers.py`

Unit tests for **AwsEventStreamParser** and helper parsing functions. **52 tests.**

#### `TestFindMatchingBrace`

- **`test_simple_json_object()`**: Verifies closing brace search for simple JSON
- **`test_nested_json_object()`**: Verifies search for nested JSON
- **`test_json_with_braces_in_string()`**: Verifies ignoring braces inside strings
- **`test_json_with_escaped_quotes()`**: Verifies handling of escaped quotes
- **`test_incomplete_json()`**: Verifies handling of incomplete JSON
- **`test_invalid_start_position()`**: Verifies handling of invalid start position
- **`test_start_position_out_of_bounds()`**: Verifies handling of position beyond text

#### `TestParseBracketToolCalls`

- **`test_parses_single_tool_call()`**: Verifies parsing of single tool call
- **`test_parses_multiple_tool_calls()`**: Verifies parsing of multiple tool calls
- **`test_returns_empty_for_no_tool_calls()`**: Verifies empty list return without tool calls
- **`test_returns_empty_for_empty_string()`**: Verifies empty string handling
- **`test_returns_empty_for_none()`**: Verifies None handling
- **`test_handles_nested_json_in_args()`**: Verifies parsing of nested JSON in arguments
- **`test_generates_unique_ids()`**: Verifies unique ID generation for tool calls

#### `TestDeduplicateToolCalls`

- **`test_removes_duplicates()`**: Verifies duplicate removal
- **`test_preserves_first_occurrence()`**: Verifies first occurrence preservation
- **`test_handles_empty_list()`**: Verifies empty list handling

**New tests for improved deduplication by id:**

- **`test_deduplicates_by_id_keeps_one_with_arguments()`**:
  - **What it does**: Verifies deduplication by id keeping tool call with arguments
  - **Purpose**: Ensure when duplicates by id, the one with arguments is kept

- **`test_deduplicates_by_id_prefers_longer_arguments()`**:
  - **What it does**: Verifies that duplicates by id prefer longer arguments
  - **Purpose**: Ensure tool call with more complete arguments is kept

- **`test_deduplicates_empty_arguments_replaced_by_non_empty()`**:
  - **What it does**: Verifies empty arguments replacement with non-empty
  - **Purpose**: Ensure "{}" is replaced with real arguments

- **`test_handles_tool_calls_without_id()`**:
  - **What it does**: Verifies handling of tool calls without id
  - **Purpose**: Ensure tool calls without id are deduplicated by name+arguments

- **`test_mixed_with_and_without_id()`**:
  - **What it does**: Verifies mixed list with and without id
  - **Purpose**: Ensure both types are handled correctly

#### `TestAwsEventStreamParserInitialization`

- **`test_initialization_creates_empty_state()`**: Verifies initial parser state

#### `TestAwsEventStreamParserFeed`

- **`test_parses_content_event()`**: Verifies content event parsing
- **`test_parses_multiple_content_events()`**: Verifies multiple content events parsing
- **`test_deduplicates_repeated_content()`**: Verifies repeated content deduplication
- **`test_parses_usage_event()`**: Verifies usage event parsing
- **`test_parses_context_usage_event()`**: Verifies context_usage event parsing
- **`test_handles_incomplete_json()`**: Verifies incomplete JSON handling
- **`test_completes_json_across_chunks()`**: Verifies JSON assembly from multiple chunks
- **`test_decodes_escape_sequences()`**: Verifies escape sequence decoding
- **`test_handles_invalid_bytes()`**: Verifies invalid bytes handling

#### `TestAwsEventStreamParserToolCalls`

- **`test_parses_tool_start_event()`**: Verifies tool call start parsing
- **`test_parses_tool_input_event()`**: Verifies tool call input parsing
- **`test_parses_tool_stop_event()`**: Verifies tool call completion
- **`test_get_tool_calls_returns_all()`**: Verifies getting all tool calls
- **`test_get_tool_calls_finalizes_current()`**: Verifies incomplete tool call finalization

#### `TestAwsEventStreamParserReset`

- **`test_reset_clears_state()`**: Verifies parser state reset

#### `TestAwsEventStreamParserFinalizeToolCall`

**New tests for _finalize_tool_call method with different input types:**

- **`test_finalize_with_string_arguments()`**:
  - **What it does**: Verifies tool call finalization with string arguments
  - **Purpose**: Ensure JSON string is parsed and serialized back

- **`test_finalize_with_dict_arguments()`**:
  - **What it does**: Verifies tool call finalization with dict arguments
  - **Purpose**: Ensure dict is serialized to JSON string

- **`test_finalize_with_empty_string_arguments()`**:
  - **What it does**: Verifies tool call finalization with empty string arguments
  - **Purpose**: Ensure empty string is replaced with "{}"

- **`test_finalize_with_whitespace_only_arguments()`**:
  - **What it does**: Verifies tool call finalization with whitespace arguments
  - **Purpose**: Ensure whitespace string is replaced with "{}"

- **`test_finalize_with_invalid_json_arguments()`**:
  - **What it does**: Verifies tool call finalization with invalid JSON
  - **Purpose**: Ensure invalid JSON is replaced with "{}"

- **`test_finalize_with_none_current_tool_call()`**:
  - **What it does**: Verifies finalization when current_tool_call is None
  - **Purpose**: Ensure nothing happens with None

- **`test_finalize_clears_current_tool_call()`**:
  - **What it does**: Verifies that finalization clears current_tool_call
  - **Purpose**: Ensure current_tool_call = None after finalization

#### `TestAwsEventStreamParserEdgeCases`

- **`test_handles_followup_prompt()`**: Verifies followupPrompt ignoring
- **`test_handles_mixed_events()`**: Verifies mixed events parsing
- **`test_handles_garbage_between_events()`**: Verifies garbage handling between events
- **`test_handles_empty_chunk()`**: Verifies empty chunk handling

---

### `tests/unit/test_thinking_parser.py`

Unit tests for **ThinkingParser** (FSM-based parser for thinking blocks in streaming responses). **63 tests.**

#### `TestParserStateEnum`

- **`test_pre_content_value()`**: Verifies PRE_CONTENT enum value is 0
- **`test_in_thinking_value()`**: Verifies IN_THINKING enum value is 1
- **`test_streaming_value()`**: Verifies STREAMING enum value is 2

#### `TestThinkingParseResult`

- **`test_default_values()`**: Verifies default values of ThinkingParseResult dataclass
- **`test_custom_values()`**: Verifies custom values can be set in ThinkingParseResult

#### `TestThinkingParserInitialization`

- **`test_default_initialization()`**: Verifies parser starts in PRE_CONTENT state with empty buffers
- **`test_custom_handling_mode()`**: Verifies handling_mode can be overridden
- **`test_custom_open_tags()`**: Verifies open_tags can be overridden
- **`test_custom_initial_buffer_size()`**: Verifies initial_buffer_size can be overridden
- **`test_max_tag_length_calculated()`**: Verifies max_tag_length is calculated from open_tags

#### `TestThinkingParserFeedPreContent`

- **`test_empty_content_returns_empty_result()`**: Verifies empty content doesn't change state
- **`test_detects_thinking_tag()`**: Verifies `<thinking>` tag detection and state transition
- **`test_detects_think_tag()`**: Verifies `<think>` tag detection
- **`test_detects_reasoning_tag()`**: Verifies `<reasoning>` tag detection
- **`test_detects_thought_tag()`**: Verifies `<thought>` tag detection
- **`test_strips_leading_whitespace_for_tag_detection()`**: Verifies leading whitespace is stripped
- **`test_buffers_partial_tag()`**: Verifies partial tag is buffered
- **`test_completes_partial_tag()`**: Verifies partial tag is completed across chunks
- **`test_no_tag_transitions_to_streaming()`**: Verifies transition to STREAMING when no tag found
- **`test_buffer_exceeds_limit_transitions_to_streaming()`**: Verifies transition when buffer exceeds limit

#### `TestThinkingParserFeedInThinking`

- **`test_accumulates_thinking_content()`**: Verifies thinking content is accumulated
- **`test_detects_closing_tag()`**: Verifies closing tag detection and state transition
- **`test_regular_content_after_closing_tag()`**: Verifies content after closing tag is regular_content
- **`test_strips_whitespace_after_closing_tag()`**: Verifies whitespace is stripped after closing tag
- **`test_cautious_buffering()`**: Verifies cautious buffering keeps last max_tag_length chars
- **`test_split_closing_tag()`**: Verifies split closing tag is handled

#### `TestThinkingParserFeedStreaming`

- **`test_passes_content_through()`**: Verifies content is passed through in STREAMING state
- **`test_ignores_thinking_tags_in_streaming()`**: Verifies thinking tags are ignored in STREAMING state

#### `TestThinkingParserFinalize`

- **`test_flushes_thinking_buffer()`**: Verifies thinking buffer is flushed on finalize
- **`test_flushes_initial_buffer()`**: Verifies initial buffer is flushed on finalize
- **`test_clears_buffers_after_finalize()`**: Verifies buffers are cleared after finalize

#### `TestThinkingParserReset`

- **`test_resets_to_initial_state()`**: Verifies reset returns parser to initial state

#### `TestThinkingParserFoundThinkingBlock`

- **`test_false_initially()`**: Verifies found_thinking_block is False initially
- **`test_true_after_tag_detection()`**: Verifies found_thinking_block is True after tag detection
- **`test_false_when_no_tag()`**: Verifies found_thinking_block is False when no tag found

#### `TestThinkingParserProcessForOutput`

- **`test_as_reasoning_content_mode()`**: Verifies as_reasoning_content mode returns content as-is
- **`test_remove_mode()`**: Verifies remove mode returns None
- **`test_pass_mode_first_chunk()`**: Verifies pass mode adds opening tag to first chunk
- **`test_pass_mode_last_chunk()`**: Verifies pass mode adds closing tag to last chunk
- **`test_pass_mode_first_and_last_chunk()`**: Verifies pass mode adds both tags when first and last
- **`test_pass_mode_middle_chunk()`**: Verifies pass mode returns content as-is for middle chunk
- **`test_strip_tags_mode()`**: Verifies strip_tags mode returns content without tags
- **`test_none_content_returns_none()`**: Verifies None content returns None
- **`test_empty_content_returns_none()`**: Verifies empty content returns None

#### `TestThinkingParserFullFlow`

Integration tests for full parsing flow.

- **`test_complete_thinking_block()`**: Verifies complete thinking block parsing
- **`test_multi_chunk_thinking_block()`**: Verifies thinking block split across multiple chunks
- **`test_no_thinking_block()`**: Verifies handling of content without thinking block
- **`test_thinking_block_with_newlines()`**: Verifies thinking block with newlines after closing tag
- **`test_empty_thinking_block()`**: Verifies empty thinking block handling
- **`test_thinking_block_only_whitespace_after()`**: Verifies thinking block with only whitespace after

#### `TestThinkingParserEdgeCases`

- **`test_nested_tags_not_supported()`**: Verifies nested tags are not specially handled
- **`test_tag_in_middle_of_content()`**: Verifies tag in middle of content is not detected
- **`test_malformed_closing_tag()`**: Verifies malformed closing tag is not detected
- **`test_unicode_content()`**: Verifies Unicode content is handled correctly
- **`test_very_long_thinking_content()`**: Verifies very long thinking content is handled
- **`test_special_characters_in_content()`**: Verifies special characters are handled
- **`test_multiple_feeds_after_streaming()`**: Verifies multiple feeds in STREAMING state

#### `TestThinkingParserConfigIntegration`

- **`test_uses_config_handling_mode()`**: Verifies parser uses FAKE_REASONING_HANDLING from config
- **`test_uses_config_open_tags()`**: Verifies parser uses FAKE_REASONING_OPEN_TAGS from config
- **`test_default_initial_buffer_size_from_config()`**: Verifies parser uses default initial_buffer_size from config

#### `TestInjectThinkingTags`

Tests for inject_thinking_tags function in converters.

- **`test_injects_tags_when_enabled()`**: Verifies tags are injected when FAKE_REASONING_ENABLED is True
- **`test_no_injection_when_disabled()`**: Verifies tags are not injected when FAKE_REASONING_ENABLED is False
- **`test_injection_preserves_content()`**: Verifies original content is preserved after injection

---

### `tests/unit/test_tokenizer.py`

Unit tests for **tokenizer module** (token counting with tiktoken). **32 tests.**

#### `TestCountTokens`

Tests for count_tokens function.

- **`test_empty_string_returns_zero()`**:
  - **What it does**: Verifies that empty string returns 0 tokens
  - **Purpose**: Ensure correct edge case handling

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_simple_text_returns_positive()`**:
  - **What it does**: Verifies that simple text returns positive token count
  - **Purpose**: Ensure basic counting functionality

- **`test_longer_text_returns_more_tokens()`**:
  - **What it does**: Verifies that longer text returns more tokens
  - **Purpose**: Ensure correct counting proportionality

- **`test_claude_correction_applied_by_default()`**:
  - **What it does**: Verifies that Claude correction factor is applied by default
  - **Purpose**: Ensure apply_claude_correction=True by default

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

- **`test_unicode_text()`**:
  - **What it does**: Verifies token counting for Unicode text
  - **Purpose**: Ensure correct non-ASCII character handling

- **`test_multiline_text()`**:
  - **What it does**: Verifies token counting for multiline text
  - **Purpose**: Ensure correct newline handling

- **`test_json_text()`**:
  - **What it does**: Verifies token counting for JSON string
  - **Purpose**: Ensure correct JSON handling

#### `TestCountTokensFallback`

Tests for fallback logic when tiktoken is unavailable.

- **`test_fallback_when_tiktoken_unavailable()`**:
  - **What it does**: Verifies fallback counting when tiktoken is unavailable
  - **Purpose**: Ensure system works without tiktoken

- **`test_fallback_without_correction()`**:
  - **What it does**: Verifies fallback without correction factor
  - **Purpose**: Ensure fallback works with apply_claude_correction=False

#### `TestCountMessageTokens`

Tests for count_message_tokens function.

- **`test_empty_list_returns_zero()`**:
  - **What it does**: Verifies that empty list returns 0 tokens
  - **Purpose**: Ensure correct empty list handling

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_single_user_message()`**:
  - **What it does**: Verifies token counting for single user message
  - **Purpose**: Ensure basic functionality

- **`test_multiple_messages()`**:
  - **What it does**: Verifies token counting for multiple messages
  - **Purpose**: Ensure tokens are summed correctly

- **`test_message_with_tool_calls()`**:
  - **What it does**: Verifies token counting for message with tool_calls
  - **Purpose**: Ensure tool_calls are counted

- **`test_message_with_tool_call_id()`**:
  - **What it does**: Verifies token counting for tool response message
  - **Purpose**: Ensure tool_call_id is counted

- **`test_message_with_list_content()`**:
  - **What it does**: Verifies token counting for multimodal content
  - **Purpose**: Ensure list content is handled

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

- **`test_message_with_empty_content()`**:
  - **What it does**: Verifies counting for message with empty content
  - **Purpose**: Ensure empty content doesn't break counting

- **`test_message_with_none_content()`**:
  - **What it does**: Verifies counting for message with None content
  - **Purpose**: Ensure None content doesn't break counting

#### `TestCountToolsTokens`

Tests for count_tools_tokens function.

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_empty_list_returns_zero()`**:
  - **What it does**: Verifies that empty list returns 0 tokens
  - **Purpose**: Ensure correct empty list handling

- **`test_single_tool()`**:
  - **What it does**: Verifies token counting for single tool
  - **Purpose**: Ensure basic functionality

- **`test_multiple_tools()`**:
  - **What it does**: Verifies token counting for multiple tools
  - **Purpose**: Ensure tokens are summed

- **`test_tool_with_complex_parameters()`**:
  - **What it does**: Verifies counting for tool with complex parameters
  - **Purpose**: Ensure JSON schema parameters are counted

- **`test_tool_without_parameters()`**:
  - **What it does**: Verifies counting for tool without parameters
  - **Purpose**: Ensure missing parameters doesn't break counting

- **`test_tool_with_empty_description()`**:
  - **What it does**: Verifies counting for tool with empty description
  - **Purpose**: Ensure empty description doesn't break counting

- **`test_non_function_tool_type()`**:
  - **What it does**: Verifies handling of tool with type != "function"
  - **Purpose**: Ensure non-function tools are handled

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

#### `TestEstimateRequestTokens`

Tests for estimate_request_tokens function.

- **`test_messages_only()`**:
  - **What it does**: Verifies token estimation for messages only
  - **Purpose**: Ensure basic functionality

- **`test_messages_with_tools()`**:
  - **What it does**: Verifies token estimation for messages with tools
  - **Purpose**: Ensure tools are counted

- **`test_messages_with_system_prompt()`**:
  - **What it does**: Verifies token estimation with separate system prompt
  - **Purpose**: Ensure system_prompt is counted

- **`test_full_request()`**:
  - **What it does**: Verifies token estimation for full request
  - **Purpose**: Ensure all components are summed

- **`test_empty_messages()`**:
  - **What it does**: Verifies estimation for empty message list
  - **Purpose**: Ensure correct edge case handling

#### `TestClaudeCorrectionFactor`

Tests for Claude correction factor.

- **`test_correction_factor_value()`**:
  - **What it does**: Verifies correction factor value
  - **Purpose**: Ensure factor equals 1.15

- **`test_correction_increases_token_count()`**:
  - **What it does**: Verifies that correction increases token count
  - **Purpose**: Ensure factor is applied correctly

#### `TestGetEncoding`

Tests for _get_encoding function.

- **`test_returns_encoding_when_tiktoken_available()`**:
  - **What it does**: Verifies that _get_encoding returns encoding when tiktoken is available
  - **Purpose**: Ensure correct tiktoken initialization

- **`test_caches_encoding()`**:
  - **What it does**: Verifies that encoding is cached
  - **Purpose**: Ensure lazy initialization

- **`test_handles_import_error()`**:
  - **What it does**: Verifies ImportError handling when tiktoken is missing
  - **Purpose**: Ensure system works without tiktoken

#### `TestTokenizerIntegration`

Integration tests for tokenizer.

- **`test_realistic_chat_request()`**:
  - **What it does**: Verifies token counting for realistic chat request
  - **Purpose**: Ensure correct operation on real data

- **`test_large_context()`**:
  - **What it does**: Verifies token counting for large context
  - **Purpose**: Ensure performance on large data

- **`test_consistency_across_calls()`**:
  - **What it does**: Verifies counting consistency across repeated calls
  - **Purpose**: Ensure results are deterministic

---

### `tests/unit/test_streaming.py`

Unit tests for **streaming module** (Kiro to OpenAI format stream conversion). **23 tests.**

#### `TestStreamingToolCallsIndex`

Tests for adding index to tool_calls in streaming responses.

- **`test_tool_calls_have_index_field()`**:
  - **What it does**: Verifies that tool_calls in streaming response contain index field
  - **Purpose**: Ensure OpenAI API spec is followed for streaming tool calls

- **`test_multiple_tool_calls_have_sequential_indices()`**:
  - **What it does**: Verifies that multiple tool_calls have sequential indices
  - **Purpose**: Ensure indices start from 0 and go sequentially

#### `TestStreamingToolCallsNoneProtection`

Tests for None value protection in tool_calls.

- **`test_handles_none_function_name()`**:
  - **What it does**: Verifies None handling in function.name
  - **Purpose**: Ensure None is replaced with empty string

- **`test_handles_none_function_arguments()`**:
  - **What it does**: Verifies None handling in function.arguments
  - **Purpose**: Ensure None is replaced with "{}"

- **`test_handles_none_function_object()`**:
  - **What it does**: Verifies None handling instead of function object
  - **Purpose**: Ensure None function is handled without errors

#### `TestCollectStreamResponseToolCalls`

Tests for collect_stream_response with tool_calls.

- **`test_collected_tool_calls_have_no_index()`**:
  - **What it does**: Verifies that collected tool_calls don't contain index field
  - **Purpose**: Ensure index is removed for non-streaming response

- **`test_collected_tool_calls_have_required_fields()`**:
  - **What it does**: Verifies that collected tool_calls contain all required fields
  - **Purpose**: Ensure id, type, function are present

- **`test_handles_none_in_collected_tool_calls()`**:
  - **What it does**: Verifies None value handling in collected tool_calls
  - **Purpose**: Ensure None values are replaced with defaults

#### `TestStreamingErrorHandling`

Tests for error handling in streaming module (bug #8 fix).

- **`test_generator_exit_handled_gracefully()`**:
  - **What it does**: Verifies that GeneratorExit is handled without logging as error
  - **Purpose**: Ensure client disconnect doesn't cause ERROR in logs

- **`test_exception_with_empty_message_logged_with_type()`**:
  - **What it does**: Verifies that exception with empty message is logged with type
  - **Purpose**: Ensure exception type is visible in logs even if str(e) is empty

- **`test_exception_propagated_to_caller()`**:
  - **What it does**: Verifies that exceptions are propagated up
  - **Purpose**: Ensure errors are not "swallowed" inside generator

- **`test_response_closed_on_error()`**:
  - **What it does**: Verifies that response is closed even on error
  - **Purpose**: Ensure resources are released in finally block

- **`test_response_closed_on_success()`**:
  - **What it does**: Verifies that response is closed on successful completion
  - **Purpose**: Ensure resources are released in finally block

- **`test_aclose_error_does_not_mask_original_error()`**:
  - **What it does**: Verifies that aclose() error doesn't mask original error
  - **Purpose**: Ensure original exception is propagated even if aclose() fails

#### `TestFirstTokenTimeoutError`

Tests for FirstTokenTimeoutError and first token timeout logging.

- **`test_first_token_timeout_not_caught_by_general_handler()`**:
  - **What it does**: Verifies that FirstTokenTimeoutError is propagated for retry
  - **Purpose**: Ensure first token timeout is not handled as regular error

- **`test_first_token_timeout_logged_with_correct_format()`**:
  - **What it does**: Verifies that first token timeout is logged with [FirstTokenTimeout] prefix
  - **Purpose**: Ensure consistent logging format for first token timeout

- **`test_first_token_timeout_includes_timeout_value()`**:
  - **What it does**: Verifies that first token timeout log includes the timeout value
  - **Purpose**: Ensure timeout value is visible in logs for debugging

- **`test_first_token_received_logged_on_success()`**:
  - **What it does**: Verifies that successful first token receipt is logged
  - **Purpose**: Ensure debug log shows when first token is received

#### `TestStreamWithFirstTokenRetry`

Tests for stream_with_first_token_retry function.

- **`test_retry_on_first_token_timeout()`**:
  - **What it does**: Verifies that request is retried on first token timeout
  - **Purpose**: Ensure retry logic works for first token timeout

- **`test_all_retries_exhausted_raises_504()`**:
  - **What it does**: Verifies that 504 is raised after all retries exhausted
  - **Purpose**: Ensure proper error handling when model never responds

- **`test_retry_logs_attempt_number()`**:
  - **What it does**: Verifies that retry attempts are logged with attempt number
  - **Purpose**: Ensure logs show which attempt failed (e.g., "1/3", "2/3", "3/3")

---

### `tests/unit/test_http_client.py`

Unit tests for **KiroHttpClient** (HTTP client with retry logic). **29 tests.**

#### `TestKiroHttpClientInitialization`

- **`test_initialization_stores_auth_manager()`**: Verifies auth_manager storage during initialization
- **`test_initialization_client_is_none()`**: Verifies that HTTP client is initially None

#### `TestKiroHttpClientGetClient`

- **`test_get_client_creates_new_client()`**: Verifies new HTTP client creation
- **`test_get_client_reuses_existing_client()`**: Verifies existing client reuse
- **`test_get_client_recreates_closed_client()`**: Verifies closed client recreation

#### `TestKiroHttpClientClose`

- **`test_close_closes_client()`**: Verifies HTTP client closing
- **`test_close_does_nothing_for_none_client()`**: Verifies close() doesn't crash for None client
- **`test_close_does_nothing_for_closed_client()`**: Verifies close() doesn't crash for closed client

#### `TestKiroHttpClientRequestWithRetry`

- **`test_successful_request_returns_response()`**: Verifies successful request
- **`test_403_triggers_token_refresh()`**: Verifies token refresh on 403
- **`test_429_triggers_backoff()`**: Verifies exponential backoff on 429
- **`test_5xx_triggers_backoff()`**: Verifies exponential backoff on 5xx
- **`test_timeout_triggers_backoff()`**: Verifies exponential backoff on timeout
- **`test_request_error_triggers_backoff()`**: Verifies exponential backoff on request error
- **`test_max_retries_exceeded_raises_502()`**: Verifies HTTPException after retries exhausted
- **`test_other_status_codes_returned_as_is()`**: Verifies other status codes return without retry
- **`test_streaming_request_uses_send()`**: Verifies send() usage for streaming

#### `TestKiroHttpClientContextManager`

- **`test_context_manager_returns_self()`**: Verifies __aenter__ returns self
- **`test_context_manager_closes_on_exit()`**: Verifies client closing on context exit

#### `TestKiroHttpClientExponentialBackoff`

- **`test_backoff_delay_increases_exponentially()`**: Verifies exponential delay increase

#### `TestKiroHttpClientStreamingTimeout`

Tests for streaming timeout logic (httpx timeouts, not FIRST_TOKEN_TIMEOUT).

- **`test_streaming_uses_streaming_read_timeout()`**:
  - **What it does**: Verifies that streaming requests use STREAMING_READ_TIMEOUT for read timeout
  - **Purpose**: Ensure httpx.Timeout is configured with connect=30s and read=STREAMING_READ_TIMEOUT

- **`test_streaming_uses_first_token_max_retries()`**:
  - **What it does**: Verifies that streaming requests use FIRST_TOKEN_MAX_RETRIES
  - **Purpose**: Ensure separate retry counter is used for stream=True

- **`test_streaming_timeout_retry_without_delay()`**:
  - **What it does**: Verifies that streaming timeout retry happens without delay
  - **Purpose**: Ensure no exponential backoff on streaming timeout

- **`test_non_streaming_uses_default_timeout()`**:
  - **What it does**: Verifies that non-streaming requests use httpx.Timeout(timeout=300)
  - **Purpose**: Ensure unified 300s timeout for all operations in non-streaming mode

- **`test_connect_timeout_logged_correctly()`**:
  - **What it does**: Verifies that ConnectTimeout is logged with [ConnectTimeout] prefix
  - **Purpose**: Ensure timeout type is visible in logs for debugging

- **`test_read_timeout_logged_correctly()`**:
  - **What it does**: Verifies that ReadTimeout is logged with [ReadTimeout] prefix and STREAMING_READ_TIMEOUT value
  - **Purpose**: Ensure timeout type and value are visible in logs

- **`test_streaming_timeout_returns_504_with_error_type()`**:
  - **What it does**: Verifies that streaming timeout returns 504 with error type in detail
  - **Purpose**: Ensure 504 Gateway Timeout includes error type (e.g., "ReadTimeout")

- **`test_non_streaming_timeout_returns_502()`**:
  - **What it does**: Verifies that non-streaming timeout returns 502
  - **Purpose**: Ensure old logic with 502 is used for non-streaming

---

### `tests/unit/test_routes.py`

Unit tests for **API endpoints** (/v1/models, /v1/chat/completions). **22 tests.**

#### `TestVerifyApiKey`

- **`test_valid_api_key_returns_true()`**: Verifies successful validation of correct key
- **`test_invalid_api_key_raises_401()`**: Verifies invalid key rejection
- **`test_missing_api_key_raises_401()`**: Verifies missing key rejection
- **`test_empty_api_key_raises_401()`**: Verifies empty key rejection
- **`test_wrong_format_raises_401()`**: Verifies key without Bearer rejection

#### `TestRootEndpoint`

- **`test_root_returns_status_ok()`**: Verifies root endpoint response
- **`test_root_returns_version()`**: Verifies version presence in response

#### `TestHealthEndpoint`

- **`test_health_returns_healthy()`**: Verifies health endpoint response
- **`test_health_returns_timestamp()`**: Verifies timestamp presence in response
- **`test_health_returns_version()`**: Verifies version presence in response

#### `TestModelsEndpoint`

- **`test_models_requires_auth()`**: Verifies authorization requirement
- **`test_models_returns_list()`**: Verifies model list return
- **`test_models_returns_available_models()`**: Verifies available models presence
- **`test_models_format_is_openai_compatible()`**: Verifies response format OpenAI compatibility

#### `TestChatCompletionsEndpoint`

- **`test_chat_completions_requires_auth()`**: Verifies authorization requirement
- **`test_chat_completions_validates_messages()`**: Verifies empty messages validation
- **`test_chat_completions_validates_model()`**: Verifies missing model validation

#### `TestChatCompletionsWithMockedKiro`

- **`test_chat_completions_accepts_valid_request_format()`**: Verifies valid request format acceptance

#### `TestChatCompletionsErrorHandling`

- **`test_invalid_json_returns_422()`**: Verifies invalid JSON handling
- **`test_missing_content_in_message_returns_200()`**: Verifies message without content handling

#### `TestRouterIntegration`

- **`test_router_has_all_endpoints()`**: Verifies all endpoints presence in router
- **`test_router_methods()`**: Verifies endpoint HTTP methods

---

### `tests/integration/test_full_flow.py`

Integration tests for **full end-to-end flow**. **12 tests (11 passed, 1 skipped).**

#### `TestFullChatCompletionFlow`

- **`test_full_flow_health_to_models_to_chat()`**: Verifies full flow from health check to chat completions
- **`test_authentication_flow()`**: Verifies authentication flow
- **`test_openai_compatibility_format()`**: Verifies response format compatibility with OpenAI API

#### `TestRequestValidationFlow`

- **`test_chat_completions_request_validation()`**: Verifies various request format validation
- **`test_complex_message_formats()`**: Verifies complex message format handling

#### `TestErrorHandlingFlow`

- **`test_invalid_json_handling()`**: Verifies invalid JSON handling
- **`test_wrong_content_type_handling()`**: SKIPPED - bug discovered in validation_exception_handler

#### `TestModelsEndpointIntegration`

- **`test_models_returns_all_available_models()`**: Verifies all models from config are returned
- **`test_models_caching_behavior()`**: Verifies model caching behavior

#### `TestStreamingFlagHandling`

- **`test_stream_true_accepted()`**: Verifies stream=true acceptance
- **`test_stream_false_accepted()`**: Verifies stream=false acceptance

#### `TestHealthEndpointIntegration`

- **`test_root_and_health_consistency()`**: Verifies / and /health consistency

---

## Testing Philosophy

### Principles

1. **Isolation**: Each test is completely isolated from external services through mocks
2. **Detail**: Abundant print() for understanding test flow during debugging
3. **Coverage**: Tests cover not only happy path, but also edge cases and errors
4. **Security**: All tests use mock credentials, never real ones

### Test Structure (Arrange-Act-Assert)

Each test follows the pattern:
1. **Arrange** (Setup): Prepare mocks and data
2. **Act** (Action): Execute the tested action
3. **Assert** (Verify): Verify result with explicit comparison

### Test Types

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Verify component interactions
- **Security tests**: Verify security system
- **Edge case tests**: Paranoid edge case checks

## Adding New Tests

When adding new tests:

1. Follow existing class structure (`Test*Success`, `Test*Errors`, `Test*EdgeCases`)
2. Use descriptive names: `test_<what_it_does>_<expected_result>`
3. Add docstring with "What it does" and "Purpose"
4. Use print() for logging test steps
5. Update this README with new test description

## Troubleshooting

### Tests fail with ImportError

```bash
# Make sure you're in project root
cd /path/to/kiro-openai-gateway

# pytest.ini already contains pythonpath = .
# Just run pytest
pytest
```

### Tests pass locally but fail in CI

- Check dependency versions in requirements.txt
- Ensure all mocks correctly isolate external calls

### Async tests don't work

```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Check for @pytest.mark.asyncio decorator
```

## Coverage Metrics

To check code coverage:

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest --cov=kiro_gateway --cov-report=html

# View report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## Contacts and Support

If you find bugs or have suggestions for test improvements, create an issue in the project repository.
