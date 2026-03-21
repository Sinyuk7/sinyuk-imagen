## ADDED Requirements

### Requirement: Unified provider interface
All image generation providers SHALL implement the `BaseImageProvider` abstract base class (ABC). The interface SHALL explicitly define: `generate_image(task_config: TaskConfig) -> GenerationResult` as the primary execution method, `validate_config() -> bool` for startup validation, and `_build_params(task_config: TaskConfig) -> dict` as an overridable internal method for lightweight, provider-specific payload formatting.

#### Scenario: Provider implements abstract interface
- **GIVEN** a new integration (e.g., `StableDiffusionProvider`) inherits from `BaseImageProvider`
- **WHEN** the class is loaded by the Python interpreter
- **THEN** it MUST explicitly implement `generate_image()` and `validate_config()`
- **THEN** it MAY optionally override `_build_params()` to handle field renaming or default values

#### Scenario: Provider missing required methods
- **GIVEN** a developer creates a subclass of `BaseImageProvider`
- **WHEN** the subclass fails to implement the abstract `generate_image()` method
- **THEN** the Python interpreter SHALL raise a `TypeError` immediately upon instantiation

### Requirement: Provider receives TaskConfig directly
Each provider's `generate_image()` method SHALL receive the complete, immutable `TaskConfig` object. The provider SHALL internally invoke `_build_params()` to transform the UI-agnostic `TaskConfig` into a provider-specific API payload. Absolutely NO external mapping layer SHALL exist between the Service and Provider boundaries.

#### Scenario: Provider adapts parameters internally
- **GIVEN** `GoogleProvider` receives a `TaskConfig` where `params={"image_count": 2}`
- **WHEN** the provider begins execution
- **THEN** it SHALL internally call `self._build_params(task_config)` to translate `image_count` into the Google-specific `number_of_images` payload key
- **THEN** it SHALL merge any advanced keys found in `task_config.extra` into the final payload

#### Scenario: Default _build_params passthrough
- **GIVEN** a simple provider class that does not override `_build_params()`
- **WHEN** `self._build_params(task_config)` is invoked
- **THEN** the base class implementation SHALL return a merged dictionary of `task_config.params` and `task_config.extra` as-is

### Requirement: Provider registry with decorator pattern
The system SHALL maintain a globally accessible provider type registry (`Dict[str, Type]`). Provider implementation classes SHALL dynamically register themselves using a `@register_provider("type_name")` decorator. The factory function `create_provider(provider_config)` SHALL use this registry to instantiate the correct class based on the config's `type` field.

#### Scenario: Register and create provider dynamically
- **GIVEN** the `GoogleProvider` class is decorated with `@register_provider("google")`
- **WHEN** `create_provider({"type": "google", "api_key": "..."})` is called by the Service layer
- **THEN** the registry SHALL successfully look up "google" and return a fully instantiated `GoogleProvider`

#### Scenario: Unknown provider type requested
- **GIVEN** the active configuration requests a provider type named `anthropic_image`
- **WHEN** `create_provider({"type": "anthropic_image", ...})` executes
- **THEN** the registry SHALL raise a clear `KeyError` or custom exception indicating the provider type is not registered

### Requirement: Provider as strict API error boundary
Each provider SHALL act as a strict isolation boundary for network and API-level errors. It MUST catch all exceptions raised by its specific external HTTP client or SDK, parse them, and return a standardized `GenerationResult` with `success=False` and a descriptive `error` message. Raw API exceptions MUST NOT leak to the Service layer.

#### Scenario: API call fails with network/timeout error
- **GIVEN** a provider is attempting to contact its upstream API
- **WHEN** the connection times out or the DNS fails
- **THEN** the provider SHALL catch the specific network exception and safely return `GenerationResult(success=False, error="Connection timeout to provider endpoint.")`

#### Scenario: API returns specific error payload
- **GIVEN** a provider successfully connects but the API rejects the request (e.g., HTTP 429 or 400 Safety Violation)
- **WHEN** the API client throws a rate-limit or safety exception
- **THEN** the provider SHALL catch it, extract the human-readable reason, and return `GenerationResult(success=False, error="Rate limited: Please try again later.")`

### Requirement: Built-in Google provider implementation
The system SHALL include a native `GoogleProvider` implementation utilizing the official `google-genai` SDK. It SHALL support models declared in the config (e.g., `gemini-2.5-flash-preview-image-generation`). Its internal `_build_params()` SHALL accurately map `TaskConfig` fields to the Google GenAI `GenerateImagesConfig` schema.

#### Scenario: Generate image via Google SDK
- **GIVEN** `GoogleProvider` is successfully initialized with a valid Google API key
- **WHEN** `generate_image()` is invoked with a standard `TaskConfig`
- **THEN** the provider SHALL construct the correct SDK request, execute it, and wrap the returned `PIL.Image` objects into a successful `GenerationResult`

### Requirement: Built-in OpenAI-compatible provider implementation
The system SHALL include an `OpenAICompatibleProvider` that interfaces with any endpoint conforming to the standard OpenAI image generation REST protocol (e.g., `n1n.ai` or standard OpenAI API). Its `_build_params()` SHALL map `TaskConfig` fields to the standard OpenAI JSON body (e.g., `prompt`, `n`, `size`).

#### Scenario: Generate image via OpenAI-compatible endpoint
- **GIVEN** the provider is initialized with a `base_url` pointing to `https://api.n1n.ai/v1`
- **WHEN** `generate_image()` is invoked
- **THEN** the provider SHALL format the payload to OpenAI specs, make an HTTP POST request to the specified endpoint, and return the decoded images wrapped in a `GenerationResult`