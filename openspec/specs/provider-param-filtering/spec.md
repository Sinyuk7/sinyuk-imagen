## ADDED Requirements

### Requirement: Common parameter whitelist filtering in base provider
`BaseImageProvider._build_params()` SHALL implement a whitelist-based filtering mechanism for common generation parameters. The method SHALL:
1. Define a set of known common parameters: `{"seed", "negative_prompt", "guidance_scale"}`.
2. Read the provider's `supported_params` from `self._config`.
3. If `supported_params` is declared (non-null list), filter out any common parameter NOT in that list.
4. If `supported_params` is `None` (absent), retain all common parameters.
5. Filter out parameters with `None` values or empty strings, but MUST preserve `0` as a valid value (e.g., `seed=0`).
6. Return the filtered parameters for subclass consumption.

#### Scenario: Provider supports seed and negative_prompt only
- **WHEN** a provider's config declares `supported_params: [seed, negative_prompt]`
- **WHEN** `TaskConfig.params` contains `seed: 42`, `negative_prompt: "blurry"`, `guidance_scale: 7.5`
- **THEN** `_build_params()` SHALL return params including `seed` and `negative_prompt` but excluding `guidance_scale`

#### Scenario: Provider declares no supported_params (supports all)
- **WHEN** a provider's config does not include `supported_params`
- **WHEN** `TaskConfig.params` contains `seed: 42`, `negative_prompt: "blurry"`, `guidance_scale: 7.5`
- **THEN** `_build_params()` SHALL return all three parameters

#### Scenario: Seed value of zero is preserved
- **WHEN** `TaskConfig.params` contains `seed: 0`
- **THEN** `_build_params()` SHALL include `seed: 0` in the returned parameters (NOT filter it out)

#### Scenario: None values are filtered out
- **WHEN** `TaskConfig.params` contains `seed: None`, `negative_prompt: ""`
- **THEN** `_build_params()` SHALL exclude both `seed` and `negative_prompt` from the returned parameters

### Requirement: Google-compatible provider explicit parameter mapping
`GoogleCompatibleProvider._build_params()` SHALL use explicit attribute assignment to construct the SDK's `GenerateImagesConfig` object. It SHALL NOT pass unknown keys as keyword arguments to the SDK. The method SHALL:
1. Call the base class `_build_params()` to get filtered common parameters.
2. Map each recognized parameter to the corresponding SDK field name (e.g., `negative_prompt` → `negative_prompt`, `image_count` → `number_of_images`).
3. Set fixed parameters: `enhance_prompt` defaults to `False` (overridable via `TaskConfig.extra`), `output_mime_type` defaults to `"image/png"` (overridable via `TaskConfig.extra`).
4. Read `api_version` from provider config (default `"v1alpha"`) when constructing the API client.

#### Scenario: Full parameter mapping with all common params
- **WHEN** filtered params contain `seed: 42`, `negative_prompt: "blurry"`, `guidance_scale: 7.5`, `image_count: 2`, `aspect_ratio: "3:4"`
- **THEN** `GenerateImagesConfig` SHALL be constructed with `seed=42`, `negative_prompt="blurry"`, `guidance_scale=7.5`, `number_of_images=2`, `aspect_ratio="3:4"`, `enhance_prompt=False`, `output_mime_type="image/png"`

#### Scenario: Minimal parameters (no common params set)
- **WHEN** filtered params contain only `image_count: 1` and `aspect_ratio: "1:1"`
- **THEN** `GenerateImagesConfig` SHALL be constructed with `number_of_images=1`, `aspect_ratio="1:1"`, `enhance_prompt=False`, `output_mime_type="image/png"` and no seed, negative_prompt, or guidance_scale

#### Scenario: Fixed params overridden via extra
- **WHEN** `TaskConfig.extra` contains `{"enhance_prompt": true, "output_mime_type": "image/jpeg"}`
- **THEN** `GenerateImagesConfig` SHALL be constructed with `enhance_prompt=True` and `output_mime_type="image/jpeg"`

#### Scenario: api_version read from config
- **WHEN** provider config contains `api_version: "v1beta"`
- **THEN** the API client SHALL be initialized with `api_version="v1beta"` in `HttpOptions`

#### Scenario: api_version uses default when absent
- **WHEN** provider config does not contain `api_version`
- **THEN** the API client SHALL be initialized with `api_version="v1alpha"`

#### Scenario: Aspect ratio "original" handling
- **WHEN** `TaskConfig.params` contains `aspect_ratio: "original"`
- **THEN** the provider SHALL NOT set the `aspect_ratio` field on `GenerateImagesConfig` (omit it, letting the API use its default)