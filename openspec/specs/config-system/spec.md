## ADDED Requirements

### Requirement: Single-file declarative provider configuration
The system SHALL load all provider definitions from a single `config.yaml` file. Each provider entry SHALL include: `name` (unique identifier), `type` (provider implementation type), `base_url` (API endpoint), `api_key` (credential reference), and `models` (a non-empty list of supported model IDs).

#### Scenario: Valid config with multiple providers
- **GIVEN** a `config.yaml` file exists with correctly formatted YAML
- **WHEN** the config contains two provider entries with distinct names
- **THEN** ConfigManager SHALL load both providers and make them accessible by their names

#### Scenario: Provider with multiple models
- **GIVEN** a valid provider definition named `n1n`
- **WHEN** the provider entry contains a `models` list with 3 distinct model IDs
- **THEN** ConfigManager SHALL return exactly those 3 models when queried for `n1n`'s available models

### Requirement: Environment variable injection for secrets
The system SHALL support `${VAR_NAME}` syntax for string values in `config.yaml`. At load time, ConfigManager SHALL resolve these references by reading from the OS environment (typically populated via a `.env` file). API keys MUST NOT be hardcoded.

#### Scenario: Environment variable resolved successfully
- **GIVEN** the environment contains `MY_API_KEY=sk-abc123`
- **WHEN** the config is loaded and contains `api_key: ${MY_API_KEY}`
- **THEN** ConfigManager SHALL resolve the provider's `api_key` property to `sk-abc123` in memory

#### Scenario: Environment variable not found
- **GIVEN** the environment does NOT contain `MISSING_VAR`
- **WHEN** the config is loaded and references `${MISSING_VAR}`
- **THEN** ConfigManager SHALL raise a configuration error detailing the specific missing variable name

### Requirement: Active provider designation
The system SHALL support a `default_provider` string field at the root level of `config.yaml`. This field SHALL reference a valid provider `name` and serve as the system's default provider for UI initialization. For backward compatibility, if a legacy `active_provider` field is detected and `default_provider` is absent, ConfigManager SHALL log a deprecation warning and automatically map it to `default_provider`.

#### Scenario: Default provider set to valid provider
- **WHEN** `default_provider: n1n` is set at the root level of `config.yaml`
- **THEN** ConfigManager SHALL return the `n1n` provider configuration when queried for the default provider

#### Scenario: Default provider references non-existent provider
- **WHEN** `default_provider: unknown` is set but no provider named `unknown` exists
- **THEN** ConfigManager SHALL raise a validation error at startup

#### Scenario: Legacy active_provider field detected
- **WHEN** `config.yaml` contains `active_provider: n1n` but no `default_provider` field
- **THEN** ConfigManager SHALL log a deprecation warning
- **THEN** ConfigManager SHALL automatically treat `active_provider` as `default_provider`
- **THEN** the application SHALL start normally without error

### Requirement: Runtime provider state management
The system SHALL support updating the `active_provider` state in-memory during runtime (e.g., when a user changes the default in the UI settings). This state mutation SHALL strictly be in-memory and MUST NOT write back or alter the `config.yaml` file on disk.

#### Scenario: Update active provider in memory
- **GIVEN** the current active provider in memory is `n1n`
- **WHEN** the application instructs ConfigManager to set the active provider to `google_official`
- **THEN** subsequent queries to ConfigManager for the active provider SHALL return `google_official`
- **THEN** the underlying `config.yaml` file on disk SHALL remain completely unchanged

### Requirement: Configuration validation at startup
ConfigManager SHALL perform strict schema and logic validation immediately upon loading the configuration. Validation SHALL ensure:
1) All provider names are strictly unique.
2) `default_provider` (or legacy `active_provider`) references an existing provider.
3) All `${VAR}` environment variables resolve successfully.
4) All required fields (`name`, `type`, `base_url`, `api_key`, `models`) are present for every provider.
5) The `models` list for each provider contains at least one valid string entry.
6) Optional provider fields (`max_images`, `api_version`, `supported_params`, `aspect_ratios`) SHALL be validated for correct types if present, but SHALL NOT cause errors if absent.

#### Scenario: Duplicate provider names
- **WHEN** two separate provider entries share the exact same `name`
- **THEN** ConfigManager SHALL raise a validation error halting application startup

#### Scenario: Missing required field or empty models
- **WHEN** a provider entry lacks the `base_url` field OR its `models` list is empty
- **THEN** ConfigManager SHALL raise a precise validation error identifying the faulty provider and the missing requirement

#### Scenario: Optional fields absent
- **WHEN** a provider entry does not include `max_images`, `api_version`, `supported_params`, or `aspect_ratios`
- **THEN** ConfigManager SHALL load successfully using default values for each missing field

#### Scenario: Optional field with invalid type
- **WHEN** a provider entry contains `max_images: "not_a_number"`
- **THEN** ConfigManager SHALL raise a validation error identifying the field and expected type

### Requirement: Provider capability declaration fields
Each provider entry in `config.yaml` SHALL support the following optional fields to declare provider-specific capabilities:

| Field | Type | Default | Description |
|---|---|---|---|
| `max_images` | int | `1` | Maximum number of images per generation request |
| `api_version` | str | `"v1alpha"` | API version string for endpoint configuration |
| `supported_params` | list[str] \| null | `null` (all supported) | List of common parameter names this provider supports |
| `aspect_ratios` | list[str] | `["1:1", "3:4", "9:16", "16:9"]` | Supported aspect ratio options |

ConfigManager SHALL expose these values via query APIs so that the UI and provider layers can read them.

#### Scenario: Provider declares max_images
- **WHEN** a provider entry contains `max_images: 4`
- **THEN** ConfigManager SHALL return `4` when queried for that provider's max_images

#### Scenario: Provider omits max_images
- **WHEN** a provider entry does not include a `max_images` field
- **THEN** ConfigManager SHALL return the default value `1`

#### Scenario: Provider declares supported_params
- **WHEN** a provider entry contains `supported_params: [seed, negative_prompt]`
- **THEN** ConfigManager SHALL return `["seed", "negative_prompt"]` when queried

#### Scenario: Provider omits supported_params
- **WHEN** a provider entry does not include a `supported_params` field
- **THEN** ConfigManager SHALL return `None`, indicating all common parameters are supported

#### Scenario: Provider declares custom aspect_ratios
- **WHEN** a provider entry contains `aspect_ratios: ["1:1", "3:4"]`
- **THEN** ConfigManager SHALL return `["1:1", "3:4"]` when queried for that provider's aspect ratios

#### Scenario: Provider omits aspect_ratios
- **WHEN** a provider entry does not include an `aspect_ratios` field
- **THEN** ConfigManager SHALL return the default list `["1:1", "3:4", "9:16", "16:9"]`
