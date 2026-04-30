import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

ARTIFACT_SUFFIXES = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".wav",
    ".tsv",
    ".json",
}


def _remove_tree(path: Path) -> int:
    if not path.exists():
        return 0

    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=False)
        else:
            path.unlink()
        return 1
    except FileNotFoundError:
        return 0
    except Exception as exc:
        logger.warning(f"Failed to remove runtime path {path}: {exc}")
        return 0


def ensure_runtime_directories(upload_dir: str, temp_dir: str) -> None:
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    Path(temp_dir).mkdir(parents=True, exist_ok=True)


def configure_temp_environment(temp_dir: str) -> str:
    resolved = str(Path(temp_dir).resolve())
    os.environ["TEMP"] = resolved
    os.environ["TMP"] = resolved
    os.environ["TMPDIR"] = resolved
    return resolved


def cleanup_upload_artifacts(upload_dir: str) -> int:
    root = Path(upload_dir)
    if not root.exists():
        return 0

    removed = 0
    for child in root.iterdir():
        try:
            if child.is_file() and child.suffix.lower() in ARTIFACT_SUFFIXES:
                child.unlink()
                removed += 1
            elif child.is_dir() and child.name == ".tmp":
                for nested in child.iterdir():
                    if nested.is_dir():
                        shutil.rmtree(nested, ignore_errors=True)
                    else:
                        nested.unlink(missing_ok=True)
                    removed += 1
        except Exception as exc:
            logger.warning(f"Failed to remove runtime artifact {child}: {exc}")
    return removed


def cleanup_external_caches(
    huggingface_cache_dir: str,
    uv_cache_dir: str,
) -> int:
    removed = 0
    removed += _remove_tree(Path(huggingface_cache_dir).expanduser())
    removed += _remove_tree(Path(uv_cache_dir).expanduser())
    return removed
