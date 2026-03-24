"""Service-layer request and response contracts."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeAlias

from core.schemas.enums import DiagnosticCode
from core.schemas.ids import ModelDisplayName, ProviderId


@dataclass(frozen=True)
class GeneratedImageArtifact:
    """Business-owned generated image record shared across provider and UI layers."""

    canonical_path: str
    presentation_path: str
    download_name: str
    mime_type: Optional[str]
    width: int
    height: int
    content_hash: str
    source_uri: Optional[str] = None
    source_kind: str = "inline_data"


GeneratedImageValue: TypeAlias = GeneratedImageArtifact


@dataclass
class TaskConfig:
    """Standard generation request passed from UI to service to provider."""

    prompt: str
    provider: ProviderId
    model: ModelDisplayName
    params: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    ui_token_override: Optional[str] = None
    debug_mode: bool = False
    reference_image_path: Optional[str] = None
    prepared_reference_image_path: Optional[str] = None
    divisible_by: int = 16


@dataclass(frozen=True)
class ProviderExecutionRequest:
    """Prepared execution contract passed from service to provider."""

    task: TaskConfig
    model_name: str
    api_key: str
    auth_source: str


@dataclass
class PreparedReferenceImage:
    """Business-owned prepared reference image produced by preprocessing."""

    raw_path: str
    prepared_path: str
    width: int
    height: int
    divisible_by: int
    aspect_ratio: Optional[str] = None


@dataclass
class ProviderDiagnosticFact:
    """Structured provider-authored fact used for downstream diagnostics rendering."""

    code: DiagnosticCode | str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.code = DiagnosticCode(self.code)


@dataclass
class ProviderDiagnostics:
    """Expandable provider diagnostics attached to a generation result."""

    facts: List[ProviderDiagnosticFact] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Standard generation response returned from provider to service to UI."""

    images: List[GeneratedImageValue]
    provider: ProviderId
    model: ModelDisplayName
    metadata: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Optional[ProviderDiagnostics] = None
    prepared_reference_image_path: Optional[str] = None
    error: Optional[str] = None
    success: bool = True
