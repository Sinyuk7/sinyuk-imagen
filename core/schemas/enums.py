"""Stable enums that define the public protocol across core and UI."""

from enum import Enum


class TaskStatus(str, Enum):
    """Stable task lifecycle states exposed to the UI."""

    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"

    @property
    def is_terminal(self) -> bool:
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.TIMED_OUT,
        }


class TaskErrorCode(str, Enum):
    """Stable task and facade error codes."""

    INVALID_REQUEST = "invalid_request"
    QUEUE_FULL = "queue_full"
    SHUTDOWN = "shutdown"
    INPUT_MATERIALIZATION_FAILED = "input_materialization_failed"
    RESULT_MATERIALIZATION_FAILED = "result_materialization_failed"
    PROVIDER_ERROR = "provider_error"
    TIMED_OUT = "timed_out"


class DiagnosticCode(str, Enum):
    """Stable provider diagnostics rendered by the UI."""

    CLIENT_INITIALIZED = "client_initialized"
    GENERATED_IMAGE_MATERIALIZED = "generated_image_materialized"
    GENERATED_IMAGE_REMOTE_ONLY_UNSUPPORTED = "generated_image_remote_only_unsupported"
    GENERATED_IMAGE_RESOLUTION_MISMATCH = "generated_image_resolution_mismatch"
    GENERATED_IMAGE_SOURCE_RECORDED = "generated_image_source_recorded"
    PROVIDER_ERROR = "provider_error"
    REFERENCE_IMAGE_LOADED = "reference_image_loaded"
    REQUEST_CONFIGURED = "request_configured"
    REQUEST_DISPATCHED = "request_dispatched"
    REQUEST_NOT_SENT = "request_not_sent"
    REQUEST_SNAPSHOT = "request_snapshot"
    REQUESTED_RESOLUTION_UNSUPPORTED = "requested_resolution_unsupported"
    RESOLVED_MODEL = "resolved_model"
    RESPONSE_RECEIVED = "response_received"
