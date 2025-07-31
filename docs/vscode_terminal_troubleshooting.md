# VSCode Terminal Troubleshooting Guide

This guide helps resolve common terminal issues in the Casino Calendar VSCode workspace.

## Quick Fixes

### 1. Python Command Not Found
**Problem**: `'python' is not recognized as an internal or external command`

**Solutions**:
```cmd
# Option A: Run setup script
setup_terminal.bat

# Option B: Use full path
.venv\Scripts\python.exe --version

# Option C: Create new terminal with environment
# Ctrl+Shift+P → "Terminal: Create New Terminal" → Select "Casino Calendar Environment"
```

### 2. Virtual Environment Not Activated
**Problem**: Terminal shows regular prompt instead of `(.venv)`

**Solutions**:
```cmd
# Manual activation
call .venv\Scripts\activate.bat

# Or use auto-activation
auto_activate.bat

# Or create new terminal with auto-environment
```

### 3. Scripts Don't Run
**Problem**: Python scripts fail with import errors

**Solutions**:
```cmd
# Set Python path
set PYTHONPATH=%CD%

# Run with full path
.venv\Scripts\python.exe scripts\cleanup_logs.py --info

# Use VSCode tasks instead (Ctrl+Shift+P → "Tasks: Run Task")
```

### 4. Git Commands Don't Work
**Problem**: Git commands not found or behaving unexpectedly

**Solutions**:
```cmd
# Check git installation
"C:\Program Files\Git\cmd\git.exe" --version

# Add git to path temporarily
set PATH=C:\Program Files\Git\cmd;%PATH%

# Use full path for git commands
"C:\Program Files\Git\cmd\git.exe" status
```

## Terminal Profiles Available

### 1. Casino Calendar Environment (Default)
- **Purpose**: Auto-activates Python environment
- **Usage**: Default for all new terminals
- **Features**: Python, pip, project scripts available

### 2. Casino Calendar Setup
- **Purpose**: Full setup with detailed output
- **Usage**: When troubleshooting environment issues
- **Features**: Diagnostic information, error checking

### 3. Command Prompt
- **Purpose**: Standard Windows command prompt
- **Usage**: When you need a clean environment
- **Features**: No auto-activation

### 4. PowerShell
- **Purpose**: Windows PowerShell
- **Usage**: When PowerShell-specific features needed
- **Features**: Advanced scripting capabilities

## VSCode Tasks Available

Access via `Ctrl+Shift+P` → "Tasks: Run Task":

### 1. Setup Terminal Environment
- Configures terminal for Python development
- Verifies all dependencies

### 2. Run Casino Calendar
- Starts the main application
- Uses correct Python interpreter

### 3. Run Test Script
- Runs all tests with pytest
- Shows detailed output

### 4. Log Cleanup Tasks
- Info: Show log directory status
- Dry Run: Preview cleanup actions
- Execute: Perform cleanup

### 5. Install Dependencies
- Installs/updates Python packages
- Uses virtual environment pip

## Debug Configurations

Access via `F5` or Debug panel:

### 1. Casino Calendar - Debug
- Runs app with debug logging
- Breakpoint support enabled

### 2. Casino Calendar - Production
- Runs app with production settings
- Minimal logging output

### 3. Run Tests
- Debug test execution
- Step through test code

### 4. Log Cleanup Script
- Debug cleanup script issues
- Step through cleanup logic

## Environment Variables Set

When using Casino Calendar terminals:

```cmd
PYTHONPATH=C:\Users\Wesley Allegre\source\repos\GitHub\Casino_Calendar
PROJECT_ROOT=C:\Users\Wesley Allegre\source\repos\GitHub\Casino_Calendar
PATH=.venv\Scripts;[original PATH]
```

## Common Command Patterns

### Python Commands
```cmd
# Run main application
python app.py

# Run tests
python -m pytest tests/ -v

# Install packages
pip install package-name

# Run cleanup
python scripts\cleanup_logs.py --info
```

### Git Commands
```cmd
# Check status
git status

# Commit changes
git add .
git commit -m "Your message"

# Push changes
git push
```

### Project Commands
```cmd
# Setup environment
setup_terminal.bat

# Auto-activate
auto_activate.bat

# Clean logs
cleanup_logs.bat --info
```

## Advanced Troubleshooting

### Reset Terminal Environment
1. Close all terminals
2. Run `setup_terminal.bat`
3. Create new terminal

### Check Virtual Environment
```cmd
# Verify virtual environment
dir .venv\Scripts

# Check Python in venv
.venv\Scripts\python.exe --version

# Check installed packages
.venv\Scripts\pip.exe list
```

### Environment Conflicts
If you have multiple Python installations:

1. **Check system Python**:
   ```cmd
   where python
   ```

2. **Force virtual environment**:
   ```cmd
   .venv\Scripts\python.exe
   ```

3. **Update VSCode settings**:
   - Ctrl+Shift+P → "Python: Select Interpreter"
   - Choose `.venv\Scripts\python.exe`

### Performance Issues
If terminal is slow:

1. **Disable auto-activation**:
   - Change default profile to "Command Prompt"
   - Manually run `auto_activate.bat` when needed

2. **Use tasks instead**:
   - Use VSCode tasks for common operations
   - Avoid repeated environment setup

### Permission Issues
If scripts fail to run:

1. **Check file permissions**:
   ```cmd
   dir setup_terminal.bat
   ```

2. **Run as administrator** (if needed):
   - Right-click VSCode → "Run as administrator"

3. **Execution policy** (PowerShell):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Getting Help

1. **Check this guide** for common issues
2. **Run diagnostic commands**:
   ```cmd
   setup_terminal.bat
   python --version
   pip list
   ```
3. **Use VSCode tasks** instead of terminal commands
4. **Check VSCode settings** in `.vscode/settings.json`
5. **Reset environment** by closing terminals and reopening

## Support Commands

```cmd
# Show Python info
python -c "import sys; print(sys.executable); print(sys.path)"

# Show environment variables
echo %PYTHONPATH%
echo %PATH%

# Show virtual environment status
pip show pip

# Test import paths
python -c "import app_components; print('Success')"
```
