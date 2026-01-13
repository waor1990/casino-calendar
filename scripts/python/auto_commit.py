#!/usr/bin/env python3
"""
Auto-commit message generator for Casino Calendar project.

This script analyzes staged git changes and generates a commit message
following the project's Commitizen conventions.
"""

import subprocess
import re
from collections import Counter
from pathlib import Path


# Allowed types and scopes from commitlint.config.js
ALLOWED_TYPES = [
    'feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test',
    'build', 'ci', 'chore', 'merge', 'revert'
]

ALLOWED_SCOPES = [
    'app', 'dash', 'components', 'layout', 'styles', 'theme', 'data',
    'services', 'logging', 'config', 'assets', 'scripts', 'deps',
    'branch', 'tests', 'docs', 'ci', 'infra'
]

# Keywords mapping to types
KEYWORDS_TO_TYPE = {
    'feat': ['add', 'new', 'feature', 'implement', 'create'],
    'fix': ['fix', 'bug', 'error', 'issue', 'resolve', 'correct'],
    'refactor': ['refactor', 'rename', 'move', 'restructure'],
    'docs': ['doc', 'readme', 'comment', 'documentation'],
    'style': ['style', 'format', 'lint', 'whitespace', 'indent'],
    'test': ['test', 'spec', 'assert', 'mock'],
    'build': ['build', 'package', 'dependency', 'setup'],
    'ci': ['ci', 'pipeline', 'workflow', 'github', 'actions'],
    'chore': ['chore', 'cleanup', 'remove', 'delete', 'update'],
    'perf': ['perf', 'optimize', 'speed', 'performance', 'fast'],
}

# Path patterns to scopes
PATH_TO_SCOPE = {
    'src/casino_calendar/dash_app/': 'dash',
    'src/casino_calendar/dash_app/components/': 'components',
    'src/casino_calendar/dash_app/layout/': 'layout',
    'assets/styles/': 'styles',
    'assets/scripts/': 'theme',  # theme-toggle.js etc.
    'assets/': 'assets',
    'scripts/': 'scripts',
    'tests/': 'tests',
    'config/': 'config',
    'data/': 'data',
    'docs/': 'docs',
    'deploy/': 'infra',
    'logs/': 'logging',
    'src/casino_calendar/services/': 'services',
    'src/casino_calendar/logging/': 'logging',
    'src/casino_calendar/': 'app',  # fallback
    'app.py': 'app',
    'wsgi.py': 'app',
    'requirements.txt': 'deps',
    'package.json': 'deps',
    'pyproject.toml': 'deps',
    'setup.py': 'deps',
}


def run_git_command(args):
    """Run a git command and return the output."""
    result = subprocess.run(['git'] + args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_staged_files():
    """Get list of staged files."""
    output = run_git_command(['diff', '--cached', '--name-only'])
    return output.splitlines() if output else []


def get_staged_diff():
    """Get the staged diff."""
    return run_git_command(['diff', '--cached'])


def infer_type(diff):
    """Infer the commit type from the diff."""
    diff_lower = diff.lower()
    type_counts = Counter()

    for commit_type, keywords in KEYWORDS_TO_TYPE.items():
        for keyword in keywords:
            if keyword in diff_lower:
                type_counts[commit_type] += 1

    if type_counts:
        return type_counts.most_common(1)[0][0]

    # Default to 'chore' if no keywords match
    return 'chore'


def infer_scope(staged_files):
    """Infer the commit scope from staged files."""
    scope_counts = Counter()

    for file_path in staged_files:
        path = Path(file_path)
        for pattern, scope in PATH_TO_SCOPE.items():
            if pattern in str(path) or str(path) == pattern:
                scope_counts[scope] += 1
                break
        else:
            # If no pattern matches, try parent directories
            for parent in path.parents:
                parent_str = str(parent) + '/'
                if parent_str in PATH_TO_SCOPE:
                    scope_counts[PATH_TO_SCOPE[parent_str]] += 1
                    break

    if scope_counts:
        return scope_counts.most_common(1)[0][0]

    # Default scope
    return 'app'


def generate_subject(diff, staged_files):
    """Generate a short subject line."""
    # Simple implementation: use the first file or a summary
    if len(staged_files) == 1:
        file_name = Path(staged_files[0]).name
        return f"update {file_name}"
    elif len(staged_files) > 1:
        return f"update {len(staged_files)} files"
    else:
        # Extract first meaningful line from diff
        lines = diff.split('\n')
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                # Remove leading + and strip
                content = line[1:].strip()
                if content and not content.startswith('//') and not content.startswith('#'):
                    # Truncate to 50 chars
                    return content[:50] + ('...' if len(content) > 50 else '')
        return "update code"


def generate_commit_message():
    """Generate the full commit message."""
    staged_files = get_staged_files()
    if not staged_files:
        raise ValueError("No staged changes to commit")

    diff = get_staged_diff()
    commit_type = infer_type(diff)
    scope = infer_scope(staged_files)
    subject = generate_subject(diff, staged_files)

    # Ensure lowercase subject
    subject = subject.lower()

    message = f"{commit_type}({scope}): {subject}"
    return message


def main():
    """Main function."""
    try:
        message = generate_commit_message()
        print(f"Generated commit message: {message}")
        # Confirm and commit
        response = input("Proceed with this commit message? (y/n): ").strip().lower()
        if response == 'y':
            run_git_command(['commit', '-m', message])
            print("Committed successfully!")
        else:
            print("Commit cancelled.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == '__main__':
    main()