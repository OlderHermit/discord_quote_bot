import pathlib
import shutil
import subprocess

import pytest

FRONT_DIR = pathlib.Path(__file__).parent.parent / "front"
DIST_DIR = FRONT_DIR / "dist"

pytestmark = pytest.mark.skipif(
    shutil.which("npm") is None, reason="npm not available in this environment"
)


def _npm(*args, timeout=300):
    return subprocess.run(
        ["npm", *args],
        cwd=FRONT_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_front_builds():
    install_cmd = "ci" if (FRONT_DIR / "package-lock.json").exists() else "install"
    result = _npm(install_cmd)
    assert result.returncode == 0, f"npm {install_cmd} failed:\n{result.stderr}"

    # Wipe any stale dist/ so a leftover from a previous manual build
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    result = _npm("run", "build")
    assert result.returncode == 0, f"npm run build failed:\n{result.stdout}\n{result.stderr}"

    assert DIST_DIR.is_dir(), "build reported success but front/dist was not created"
    assert (DIST_DIR / "index.html").is_file(), "front/dist/index.html missing after build"
    assert any(DIST_DIR.rglob("*.js")), "no JS output found in front/dist"
