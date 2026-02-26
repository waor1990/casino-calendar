# VSCode Terminal Troubleshooting Guide

This guide covers common local terminal issues for the current Casino Calendar setup.

## Quick checks

```cmd
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe scripts\python\check_environment.py
```

If `.venv` does not exist, run:

```cmd
setup.bat
```

## Common issues

### 1) `python` is not recognized

Use the venv Python directly:

```cmd
.venv\Scripts\python.exe app.py
```

Or run through the Windows launcher:

```cmd
run.bat
```

### 2) Virtual environment not active

Activate manually:

```cmd
call .venv\Scripts\activate.bat
```

Then verify:

```cmd
python --version
```

### 3) CSS build/lint commands fail

Install Node dependencies first:

```cmd
npm install
npm run build:css
npm run lint:css
```

### 4) Tests or linters fail from VSCode terminal

Run the project test entrypoint:

```cmd
scripts\windows\test.bat
```

Or run shell checks from Git Bash/WSL:

```bash
bash scripts/shell/test.sh
```

## Recommended VSCode workflow

- Use the workspace Python interpreter from `.venv`.
- Run `setup.bat` once after cloning.
- Use `run.bat` for local app startup.
- Use `scripts\windows\test.bat` (Windows) or `bash scripts/shell/test.sh` (Unix-like shells) before committing.
