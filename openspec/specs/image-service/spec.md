## ADDED Requirements

### Requirement: TaskConfig standard data structure
The system SHALL define a `TaskConfig` dataclass as the standard, strongly-typed generation request object. Fields SHALL be: `prompt` (str, user's raw prompt passed immutably), `provider` (str, provider instance name), `model` (str, model ID), `params` (Dict[str, Any], generic UI-collected parameters), `extra` (Dict[str, Any], strict escape hatch for provider-specific advanced parameters).

#### Scenario: Construct TaskConfig from UI inputs
- **GIVEN** the UI has collected standard inputs (prompt="a cat", provider="n1n", model="gemini-2.5-flash", params={"image_count": 2})
- **WHEN** a `TaskConfig` object is instantiated
- **THEN** it SHALL contain those exact values with the `extra` field defaulting to an empty dictionary `{}`

#### Scenario: TaskConfig with extra fields
- **GIVEN** a specific provider requires an advanced, non-standard parameter like `template_id`
- **WHEN** the user or UI supplies this parameter
- **THEN** it SHALL be mapped exclusively into `TaskConfig.extra = {"template_id": "abc123"}`
- **THEN** the core `TaskConfig` class definition SHALL NOT require any structural modification

### Requirement: GenerationResult standard data structure
The system SHALL define a `GenerationResult` dataclass as the standard generation response object. Fields SHALL be: `images` (List[PIL.Image.Image]), `provider` (str), `model` (str), `metadata` (Dict[str, Any], e.g., for timing/token info), `error` (Optional[str]), and `success` (bool).

#### Scenario: Successful generation result
- **GIVEN** a provider successfully completes a generation task
- **WHEN** the provider returns the result to `ImageService`
- **THEN** the `GenerationResult` SHALL have `success=True`, `images` containing valid PIL Image objects, and `error=None`

#### Scenario: Failed generation result
- **GIVEN** a provider encounters an error (e.g., rate limit, prompt rejection)
- **WHEN** the provider returns the result
- **THEN** the `GenerationResult` SHALL have `success=False`, `images=[]`, and a descriptive `error` string

### Requirement: ImageService as sole generation entry point
The `ImageService.generate(task_config: TaskConfig) -> GenerationResult` method SHALL be the absolute, sole entry point for all image generation requests. No caller (UI, external script, etc.) SHALL instantiate or invoke Provider classes directly.

#### Scenario: UI calls ImageService
- **GIVEN** the user initiates a generation request from the presentation layer
- **WHEN** the UI layer processes the request
- **THEN** it SHALL construct a `TaskConfig` and invoke `ImageService.generate(task_config)`
- **THEN** the UI SHALL NOT bypass the service to call any Provider methods directly

#### Scenario: Service delegates to provider
- **GIVEN** `ImageService` receives a valid `TaskConfig` specifying `provider="n1n"`
- **WHEN** the `generate()` method executes
- **THEN** the Service SHALL locate the `n1n` provider instance and delegate the operation via `provider.generate_image(task_config)`

### Requirement: Provider instance lazy creation and caching
`ImageService` SHALL create Provider instances dynamically on their first use (lazy instantiation) and cache them in memory for subsequent requests. Instantiation SHALL utilize a factory function (e.g., `create_provider()`) fed by the `ConfigManager`.

#### Scenario: First request creates provider
- **GIVEN** `ImageService` is running but its internal provider cache is empty
- **WHEN** `generate()` is called requesting provider `n1n` for the first time
- **THEN** `ImageService` SHALL instantiate the provider using `ConfigManager` data, cache it, and execute the generation

#### Scenario: Subsequent request reuses cached provider
- **GIVEN** the `n1n` provider is already instantiated and cached within `ImageService`
- **WHEN** `generate()` is called requesting `n1n` again
- **THEN** `ImageService` SHALL reuse the existing instance without re-instantiating or re-authenticating

### Requirement: Service-level error wrapping (Safety Net)
`ImageService` SHALL act as the final error boundary. It SHALL catch any catastrophic, unexpected exceptions not properly handled by the underlying Provider, wrap them safely, and prevent application crashes.

#### Scenario: Unexpected error during generation
- **GIVEN** a critical, unhandled exception (e.g., out of memory, malformed network response) occurs during the provider's execution
- **WHEN** the exception bubbles up to `ImageService.generate()`
- **THEN** `ImageService` SHALL catch the exception and return a safe `GenerationResult(images=[], success=False, error="<exception_description>")` rather than crashing the application

### Requirement: Basic input validation
`ImageService` SHALL validate the integrity of `TaskConfig` before delegating to any Provider. Validation SHALL enforce that the `prompt` is non-empty, the requested `provider` exists in the configuration, and the `model` is valid for that provider.

#### Scenario: Empty prompt rejection
- **GIVEN** a `TaskConfig` is passed with an empty or whitespace-only `prompt`
- **WHEN** `generate()` is called
- **THEN** `ImageService` SHALL immediately return `GenerationResult(success=False, error="Prompt must not be empty")` without invoking the provider

#### Scenario: Unknown provider or model rejection
- **GIVEN** a `TaskConfig` requests a provider name (`nonexistent`) or a model not registered in the active configuration
- **WHEN** `generate()` is called
- **THEN** `ImageService` SHALL immediately return a failed `GenerationResult` detailing the configuration mismatch