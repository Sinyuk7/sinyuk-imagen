# Image Slider Flow

## Files

- `app.py`: entry only
- `ui/components/basic_params.py`: reference image input
- `ui/components/output.py`: slider definition and slider state mapping
- `ui/app.py`: event binding
- `ui/handlers/generate_handler.py`: generation result -> slider update

## Component Contract

Defined in `ui/components/output.py`:

```python
gr.ImageSlider(label="Before / After", type="filepath")
```

Slider value is produced by:

```python
OutputPanel.update_image_slider(reference_image, generated_images)
```

## Data Source

`before_image`
- from service-prepared reference image
- source input still comes from `basic_params.reference_image`
- slider uses the prepared temp-file path, not the raw UI path

`after_image`
- from `result.images[0]`
- produced by `GenerateHandler.handle_generate()`

## Event Paths

### 1. Reference image change

Bound in `ui/app.py`:

```python
reference_image.change(fn=_handle_reference_image_change, ...)
```

Flow:

```text
reference_image.change
-> _handle_reference_image_change(reference_image_path, divisible_by)
-> OutputPanel.update_image_slider(reference_image_path, None)
-> slider output updates
```

### 2. Generate button click

Bound in `ui/app.py`:

```python
generate_button.click(fn=self.generate_handler.handle_generate, ...)
```

Flow:

```text
generate_button.click
-> GenerateHandler.handle_generate(...)
-> image_service.generate(task_config)
-> result.images
-> OutputPanel.update_image_slider(reference_image_path, result.images)
-> slider output updates
```

## Bug Found

The event chain was already wired correctly.

The real issue was output shape:

- old reference-only state returned `(reference, None)`
- old generated-only state returned `(None, generated)`

Gradio `ImageSlider` frontend renders empty when either side is missing.
So the callback fired, but the UI still looked blank.

Frontend empty-state condition confirmed from installed Gradio code:

```text
value === null || value[0] === null || value[1] === null
```

## Current Rule

`ui/components/output.py` now returns a renderable pair for single-image states:

```python
None + None -> None
reference only -> (reference, reference)
generated only -> (generated, generated)
reference + generated -> (reference, generated)
```

## Result

- updating reference image now updates the slider visually
- returning generated images now updates the slider visually
- slider left image is the prepared reference image actually used by generation
- the slider still uses only the first generated image
- Gallery selection still does not drive the slider

## Design Check

This matches the intended state/event pattern:

- events only trigger transitions
- a pure mapping function builds UI output state
- UI output must be complete and renderable

Note: `develop_docs/Gradio 状态与事件设计模式.md` is currently empty, so this check was done against the existing `ui/app.py`, `ui/handlers/generate_handler.py`, `ui/state_machine.py`, and installed Gradio behavior.
