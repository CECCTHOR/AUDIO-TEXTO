"""Create a local virtual environment and install project dependencies."""

from pathlib import Path
import subprocess
import sys
import venv


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10 or newer is required.", file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parent
    environment = root / ".venv"
    if not environment.exists():
        print("Creating .venv...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        print("The existing .venv is incomplete. Rename it and run setup again.", file=sys.stderr)
        return 1
    try:
        subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(root / "requirements.txt")], check=True)
        subprocess.run([str(python), "-m", "pip", "check"], check=True)
    except subprocess.CalledProcessError as exc:
        print("Installation failed. Check your network, Python version, and platform wheels.", file=sys.stderr)
        return exc.returncode
    print("Setup complete. See README.md for the command for your operating system.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
