#!/usr/bin/env fish
set SCRIPT_DIR (dirname (status filename))
set VENV_PYTHON "$SCRIPT_DIR/venv/bin/python"

if not test -f "$VENV_PYTHON"
    echo "Virtual environment not found. Creating..."
    python -m venv "$SCRIPT_DIR/venv"
    "$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"
end

exec "$VENV_PYTHON" -m ivygen $argv
