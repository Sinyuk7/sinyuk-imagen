"""Private task artifact materialization and cleanup."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import logging
import os
from pathlib import Path
import shutil
import tempfile

from core.schemas import GeneratedImageArtifact, GenerationResult, TaskConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedTaskInputs:
    """Task-owned inputs created before a task enters the queue."""

    task_config: TaskConfig
    related_files: list[str]


@dataclass(frozen=True)
class MaterializedTaskResult:
    """Task-owned result payload produced after generation finishes."""

    result: GenerationResult
    related_files: list[str]


class TaskArtifactStore:
    """Manage task-owned files without leaking file system details upward."""

    def prepare_task_inputs(self, task_id: str, task_config: TaskConfig) -> PreparedTaskInputs:
        related_files: list[str] = []
        owned_reference_path = task_config.reference_image_path
        if task_config.reference_image_path:
            source_path = Path(task_config.reference_image_path)
            if source_path.exists():
                suffix = source_path.suffix or ".png"
                destination = self.task_directory(task_id) / f"reference{suffix}"
                if self._materialize_file(source_path, destination):
                    owned_reference_path = str(destination)
                    related_files.append(str(destination))

        return PreparedTaskInputs(
            task_config=replace(task_config, reference_image_path=owned_reference_path),
            related_files=related_files,
        )

    def materialize_result(
        self,
        task_id: str,
        result: GenerationResult,
    ) -> MaterializedTaskResult:
        related_files: list[str] = []
        try:
            task_dir = self.task_directory(task_id)
            task_dir.mkdir(parents=True, exist_ok=True)

            prepared_reference_path = self._materialize_prepared_reference(
                task_dir,
                result.prepared_reference_image_path,
                related_files,
            )
            owned_images = self._materialize_images(task_dir, result.images, related_files)
        except Exception:
            self.cleanup_paths(related_files)
            raise

        return MaterializedTaskResult(
            result=GenerationResult(
                images=owned_images,
                provider=result.provider,
                model=result.model,
                metadata=deepcopy(result.metadata),
                diagnostics=deepcopy(result.diagnostics),
                prepared_reference_image_path=prepared_reference_path,
                error=result.error,
                success=result.success,
            ),
            related_files=related_files,
        )

    def cleanup_paths(self, paths: list[str]) -> None:
        for path in paths:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to delete task file: %s", path)

    def delete_task(self, task_id: str, related_files: list[str]) -> None:
        self.cleanup_paths(related_files)
        shutil.rmtree(self.task_directory(task_id), ignore_errors=True)

    @staticmethod
    def task_directory(task_id: str) -> Path:
        return Path(tempfile.gettempdir()) / "sinyuk-imagen" / "tasks" / task_id

    def _materialize_prepared_reference(
        self,
        task_dir: Path,
        prepared_reference_image_path: str | None,
        related_files: list[str],
    ) -> str | None:
        if not prepared_reference_image_path:
            return None

        source = Path(prepared_reference_image_path)
        destination = task_dir / f"prepared-reference{source.suffix or '.png'}"
        if self._materialize_file(source, destination):
            related_files.append(str(destination))
            return str(destination)
        return prepared_reference_image_path

    def _materialize_images(
        self,
        task_dir: Path,
        images: list[GeneratedImageArtifact],
        related_files: list[str],
    ) -> list[GeneratedImageArtifact]:
        owned_images: list[GeneratedImageArtifact] = []
        for index, artifact in enumerate(images):
            owned_images.append(
                self._materialize_generated_artifact(task_dir, index, artifact, related_files)
            )
        return owned_images

    def _materialize_generated_artifact(
        self,
        task_dir: Path,
        index: int,
        artifact: GeneratedImageArtifact,
        related_files: list[str],
    ) -> GeneratedImageArtifact:
        canonical_source = Path(artifact.canonical_path)
        presentation_source = Path(artifact.presentation_path)
        canonical_destination = task_dir / (
            f"generated-{index}-canonical{canonical_source.suffix or '.png'}"
        )
        presentation_destination = task_dir / (
            artifact.download_name or f"generated-{index}.png"
        )
        canonical_path = artifact.canonical_path
        presentation_path = artifact.presentation_path
        if self._materialize_file(canonical_source, canonical_destination):
            related_files.append(str(canonical_destination))
            canonical_path = str(canonical_destination)
        if self._materialize_file(presentation_source, presentation_destination):
            related_files.append(str(presentation_destination))
            presentation_path = str(presentation_destination)
        return replace(
            artifact,
            canonical_path=canonical_path,
            presentation_path=presentation_path,
        )

    def _materialize_file(self, source: Path, destination: Path) -> bool:
        if not source.exists():
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        # ARTIFACT STORE TENSION: prefer hard links for cheap task ownership, but
        # cross-device task materialization must still succeed when linking fails.
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
        return True
