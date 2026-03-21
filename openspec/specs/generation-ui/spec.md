## ADDED Requirements

### Requirement: Gradio Blocks declarative UI
The UI SHALL be built using Gradio Blocks API in `ui/layout.py`. The layout module SHALL receive `ImageService` and `ConfigManager` as injected dependencies. UI code SHALL NOT import or reference any Provider class directly.

#### Scenario: UI initialization with dependencies
- **GIVEN** `app.py` is preparing to build the UI
- **WHEN** the layout builder is invoked
- **THEN** it SHALL be passed instantiated `ImageService` and `ConfigManager` objects
- **THEN** `ui/layout.py` SHALL NOT contain any imports from `core.providers`

### Requirement: Fixed common parameter area
The UI SHALL display a fixed set of common parameter controls: prompt input (Textbox, multiline), provider selector (Dropdown, populated from ConfigManager), model selector (Dropdown, updated based on selected provider), image count (Slider, dynamically visible based on provider's `max_images`), and aspect ratio (Dropdown, populated from provider's `aspect_ratios` config with an "original" option prepended, plus a "flip" Checkbox).

#### Scenario: Provider dropdown populated from config
- **WHEN** ConfigManager is successfully initialized with 3 providers
- **THEN** the provider Dropdown SHALL list exactly those 3 provider names

#### Scenario: Model dropdown updates on provider change
- **WHEN** the user selects a new provider that has models [X, Y, Z]
- **THEN** the model Dropdown SHALL immediately update to show only models [X, Y, Z]

#### Scenario: Image count hidden when max_images is 1
- **WHEN** the currently selected provider has `max_images: 1` (or unset)
- **THEN** the Image Count slider SHALL be hidden
- **THEN** the generation request SHALL default to 1 image

#### Scenario: Image count visible when max_images greater than 1
- **WHEN** the currently selected provider has `max_images: 4`
- **THEN** the Image Count slider SHALL be visible with maximum set to 4

#### Scenario: Image count updates on provider change
- **WHEN** the user switches from a provider with `max_images: 4` to one with `max_images: 1`
- **THEN** the Image Count slider SHALL become hidden
- **THEN** the image count value SHALL reset to 1

#### Scenario: Aspect ratio populated from provider config
- **WHEN** the currently selected provider has `aspect_ratios: ["1:1", "3:4", "9:16"]`
- **THEN** the Aspect Ratio Dropdown SHALL display choices `["original", "1:1", "3:4", "9:16"]`

#### Scenario: Aspect ratio flip checkbox
- **WHEN** the user selects "3:4" and checks the "翻转宽高" Checkbox
- **THEN** the generation request SHALL send `aspect_ratio: "4:3"` in TaskConfig.params

#### Scenario: Flip checkbox with 1:1 ratio
- **WHEN** the user selects "1:1" and checks the "翻转宽高" Checkbox
- **THEN** the generation request SHALL still send `aspect_ratio: "1:1"` (flipping a square is a no-op)

#### Scenario: Flip checkbox with original ratio
- **WHEN** the user selects "original" and checks the "翻转宽高" Checkbox
- **THEN** the generation request SHALL send `aspect_ratio: "original"` (flip does not apply to non-numeric ratios)

### Requirement: Provider dynamic advanced parameter area
The UI SHALL include an advanced parameter area to accept free-form, provider-specific inputs (e.g., via `gr.JSON` or `gr.Textbox`). To maintain strict data contracts, these free-form values SHALL be injected exclusively into `TaskConfig.extra`, keeping `TaskConfig.params` strictly for standard UI controls.

#### Scenario: User provides advanced parameters
- **GIVEN** the user wants to bypass default safety filters for a specific provider
- **WHEN** the user enters `{"safety_filter_level": "BLOCK_NONE"}` in the advanced parameter JSON area
- **THEN** these exact key-value pairs SHALL be placed into the `extra` dictionary of the constructed `TaskConfig`

#### Scenario: No advanced parameters provided
- **GIVEN** the user only cares about the prompt and basic settings
- **WHEN** the user leaves the advanced parameter area empty
- **THEN** `TaskConfig` SHALL be constructed with an empty `{}` for the `extra` field

### Requirement: UI supports provider token override input
The UI SHALL provide an input control for users to enter an authentication token per provider. The UI SHALL treat this token as an optional override that is passed to the orchestration layer as part of the generation request context.

#### Scenario: User enters token for selected provider
- **WHEN** the user selects provider "google" and enters a non-empty token in the UI
- **THEN** the generation request context SHALL include that token as the UI override for provider "google"

#### Scenario: User leaves token empty
- **WHEN** the user does not enter a token (empty string)
- **THEN** the generation request context SHALL NOT include a UI override token

### Requirement: UI never displays tokens in plaintext
The UI SHALL NOT display authentication tokens in plaintext in any visible output, including status messages and debug output.

#### Scenario: Token field is masked
- **WHEN** the user types a token into the token input control
- **THEN** the UI SHALL mask the token value (e.g., password-style input)

#### Scenario: Status output contains no token
- **GIVEN** a generation attempt has completed (success or failure)
- **WHEN** the UI renders the status bar message
- **THEN** the status bar SHALL NOT contain the token value

### Requirement: Model dropdown uses display names while requests use real model names
The UI SHALL display model choices using the configured display names. The UI SHALL pass the selected display name through the request without attempting to map it to a real model name.

#### Scenario: UI shows display names
- **GIVEN** the selected provider has models mapping {"Fast": "real-model-a", "HQ": "real-model-b"}
- **WHEN** the model dropdown is rendered
- **THEN** the dropdown choices SHALL be ["Fast", "HQ"]

#### Scenario: UI passes display name unchanged
- **WHEN** the user selects model display name "HQ" and clicks Generate
- **THEN** the constructed TaskConfig (or request object) SHALL carry model identifier "HQ" (display name) without mapping

### Requirement: Flip checkbox label is renamed to Swap Width/Height
The UI SHALL rename the aspect ratio flip checkbox label from "翻转宽高" to "交换宽高（Swap Width/Height）" while preserving the existing flip behavior.

#### Scenario: Label updated with same behavior
- **WHEN** the user checks "交换宽高（Swap Width/Height）" with aspect ratio "3:4"
- **THEN** the generation request SHALL send `aspect_ratio: "4:3"` in TaskConfig.params

### Requirement: Advanced Settings includes dry run and debug mode
The UI SHALL include controls in the "Advanced Settings" section for enabling dry run and debug mode.

#### Scenario: User enables debug mode
- **WHEN** the user enables debug mode and clicks Generate
- **THEN** the request context SHALL indicate debug mode is enabled

### Requirement: Debug output panel below Generate Images
The UI SHALL render a debug output panel below the "Generate Images" area. When debug mode is enabled, the UI SHALL display a pretty-printed JSON snapshot returned by the orchestration layer.

#### Scenario: Debug panel placement
- **WHEN** the UI is rendered
- **THEN** the debug output panel SHALL appear below the Generate Images section

#### Scenario: Debug output is pretty JSON
- **GIVEN** debug mode is enabled
- **WHEN** the orchestration layer returns a debug snapshot object
- **THEN** the UI SHALL display it as pretty-printed JSON (human readable)

### Requirement: Advanced settings with common generation parameters
The UI SHALL display an Accordion section labeled "Advanced Settings" containing common generation parameter controls:

| Parameter | Component | Type | Description |
|---|---|---|---|
| `negative_prompt` | `gr.Textbox` | str | Negative prompt describing unwanted elements |
| `seed` | `gr.Number` | int \| None | Random seed for reproducibility. Empty means random |
| `guidance_scale` | `gr.Checkbox` + `gr.Slider` | float \| None | Guidance strength controlling prompt adherence (range: 1.0–20.0, default: 7.5). Gated by a checkbox; when disabled, passes None |

These controls SHALL always be rendered regardless of the selected provider. Values SHALL be collected into `TaskConfig.params`. Provider-level filtering of unsupported parameters is NOT the UI's responsibility.

#### Scenario: User sets seed value
- **WHEN** the user enters `42` in the seed Number field
- **THEN** `TaskConfig.params` SHALL contain `"seed": 42`

#### Scenario: User leaves seed empty
- **WHEN** the user leaves the seed Number field empty (None)
- **THEN** `TaskConfig.params` SHALL contain `"seed": None`

#### Scenario: User sets negative prompt
- **WHEN** the user enters "blurry, low quality" in the negative prompt Textbox
- **THEN** `TaskConfig.params` SHALL contain `"negative_prompt": "blurry, low quality"`

#### Scenario: User adjusts guidance scale
- **WHEN** the user enables the guidance checkbox and moves the Slider to 12.0
- **THEN** `TaskConfig.params` SHALL contain `"guidance_scale": 12.0`

#### Scenario: User leaves guidance scale disabled
- **WHEN** the user does not check the "启用 Guidance Scale" checkbox
- **THEN** `TaskConfig.params` SHALL contain `"guidance_scale": None`

#### Scenario: Advanced settings co-exist with Advanced JSON
- **WHEN** the user fills in both seed (42) in Advanced Settings AND `{"safety_filter_level": "BLOCK_NONE"}` in the Advanced JSON area
- **THEN** `TaskConfig.params` SHALL contain `"seed": 42`
- **THEN** `TaskConfig.extra` SHALL contain `{"safety_filter_level": "BLOCK_NONE"}`

### Requirement: Generate button triggers service call
The Generate button callback SHALL: collect all UI parameter values (including advanced params), apply aspect ratio flip logic, construct a `TaskConfig` object, call `ImageService.generate(task_config)`, and manage the visual result. On success, images SHALL be displayed in a Gallery component and metadata SHALL be shown in the status bar. On failure, a friendly error message SHALL be displayed in the status bar.

#### Scenario: Successful generation
- **WHEN** the user clicks Generate and the service returns `GenerationResult(success=True, images=[...], metadata={...})`
- **THEN** the UI SHALL display the returned images in the Gallery component
- **THEN** the status bar SHALL display generation metadata (elapsed time, provider name, model name)

#### Scenario: Failed generation
- **WHEN** `ImageService.generate()` returns `GenerationResult(success=False, error="Rate limited")`
- **THEN** the status bar SHALL display a friendly error message
- **THEN** the UI SHALL NOT crash or show a raw exception traceback

### Requirement: Generation progress feedback
The Generate button event SHALL use Gradio's built-in `show_progress="full"` to display a loading animation and elapsed timer on the Gallery output component during generation.

#### Scenario: Progress shown during generation
- **WHEN** the user clicks Generate and the API call is in progress
- **THEN** a spinner animation SHALL be visible on the Gallery component
- **THEN** an elapsed time counter SHALL be displayed

#### Scenario: Progress hidden after completion
- **WHEN** the generation completes (success or failure)
- **THEN** the spinner animation SHALL disappear
- **THEN** the Gallery SHALL display results (or remain empty on failure)

### Requirement: Generation metadata status bar
The UI SHALL include a `gr.Markdown` status bar below the Gallery component to display generation results metadata.

#### Scenario: Metadata displayed on success
- **WHEN** a generation completes successfully with `metadata: {"elapsed_seconds": 3.42}`, provider "n1n", model "gemini-2.5-flash"
- **THEN** the status bar SHALL display formatted text including image count, elapsed time, provider name, and model name

#### Scenario: Error displayed on failure
- **WHEN** a generation fails with `error: "API error (n1n): ConnectionError: timeout"`
- **THEN** the status bar SHALL display a user-friendly error message including the error type and description

#### Scenario: Status bar empty on initial load
- **WHEN** the UI is first loaded and no generation has been triggered
- **THEN** the status bar SHALL display an empty string (no visual presence)

### Requirement: Provider change updates all dynamic controls
When the user selects a different provider in the provider Dropdown, the UI SHALL update ALL provider-dependent controls in a single event handler: model Dropdown (choices and value), Image Count Slider (visibility and maximum), and Aspect Ratio Dropdown (choices). It SHALL also sync the in-memory active provider state via `ConfigManager.set_active_provider()`.

#### Scenario: Full dynamic update on provider switch
- **WHEN** the user switches from provider "n1n" (max_images=4, aspect_ratios=["1:1","3:4"]) to provider "google_official" (max_images=1, aspect_ratios=["1:1","9:16","16:9"])
- **THEN** the model Dropdown SHALL update to google_official's models
- **THEN** the Image Count slider SHALL become hidden (max_images=1)
- **THEN** the Aspect Ratio Dropdown SHALL update to ["original", "1:1", "9:16", "16:9"]

### Requirement: UI contains zero business logic
UI callbacks SHALL only: collect parameter values, construct TaskConfig, call ImageService, and display results. UI SHALL NOT perform parameter transformation, API calls, error parsing, or provider-specific logic. The only exception is the aspect ratio flip operation, which is a pure string manipulation for UI convenience.

#### Scenario: All logic delegated to service
- **GIVEN** the user triggers a generation task
- **WHEN** the Generate callback executes
- **THEN** it SHALL contain no conditional `if/else` logic based on the selected provider type
- **THEN** it SHALL NOT access any API client or SDK directly

### Requirement: App entry point is minimal
`app.py` SHALL only: initialize ConfigManager, initialize ImageService (with ConfigManager injected), build the Gradio app via `ui/layout.py`, and call `app.launch()`. No business logic SHALL exist in `app.py`.

#### Scenario: App startup sequence
- **GIVEN** the terminal command `python app.py` is executed
- **WHEN** the script runs
- **THEN** ConfigManager SHALL load and validate the config
- **THEN** ImageService SHALL be instantiated with the ConfigManager
- **THEN** the Gradio app SHALL be built and launched