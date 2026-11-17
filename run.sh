#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_python="$project_root/.venv/bin/python"
if [[ ! -x "$project_python" ]]; then
    printf '%s\n' 'Run: python3 setup_environment.py from the project directory first.' >&2
    exit 1
fi
exec "$project_python" "$project_root/transcribe_translate.py" "$@"
