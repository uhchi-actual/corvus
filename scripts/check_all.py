from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "scripts/check_phase0.py"],
    [sys.executable, "scripts/check_phase1.py"],
    [sys.executable, "scripts/check_phase2.py"],
    [sys.executable, "scripts/check_phase3.py"],
    [sys.executable, "scripts/check_phase4.py"],
    [sys.executable, "-m", "ruff", "check", "backend/src", "backend/tests", "scripts"],
    [sys.executable, "-m", "pytest", "-q"],
    ["npm", "run", "lint"],
    ["npm", "audit", "--audit-level=moderate"],
    ["npm", "run", "build"],
    ["docker", "compose", "config"],
]


def resolve_command(command: list[str]) -> list[str]:
    executable = which(command[0])
    if executable is None:
        raise SystemExit(f"Missing executable: {command[0]}")
    return [executable, *command[1:]]


def main() -> None:
    for command in COMMANDS:
        cwd = ROOT
        if command[:3] == [sys.executable, "-m", "pytest"]:
            cwd = ROOT / "backend"
        if command[:2] == ["npm", "run"] or command[:2] == ["npm", "audit"]:
            cwd = ROOT / "frontend"
        print(" ".join(command))
        subprocess.run(resolve_command(command), cwd=cwd, check=True)


if __name__ == "__main__":
    main()
