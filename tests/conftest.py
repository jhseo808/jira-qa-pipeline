"""pytest: 프로젝트 루트를 import path에 둔다."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def tmp_path() -> Path:
    """
    Custom tmp_path fixture.

    Rationale:
      - The default pytest tmpdir plugin relies on Windows temp + directory scanning,
        which can be blocked in this sandbox.
      - We provide a simple, mkdir-only temporary directory under the repo.

    Notes:
      - No cleanup on purpose (avoids scandir/rmtree permission issues).
    """
    import uuid

    base = _ROOT / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    d = base / f"t_{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=True)
    return d
