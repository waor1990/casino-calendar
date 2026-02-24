#!/usr/bin/env python3
"""
Auto-commit message generator for Casino Calendar project.

This script analyzes staged git changes and generates a commit message
following the project's Commitizen conventions.
"""

import argparse
import os
import subprocess
from collections import Counter
from pathlib import Path

try:
    import openai

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


# Allowed types and scopes from commitlint.config.js
ALLOWED_TYPES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "merge", "revert"]

ALLOWED_SCOPES = [
    "app",
    "dash",
    "components",
    "layout",
    "styles",
    "theme",
    "data",
    "services",
    "logging",
    "config",
    "assets",
    "scripts",
    "deps",
    "branch",
    "tests",
    "docs",
    "ci",
    "infra",
]

# Keywords mapping to types
KEYWORDS_TO_TYPE = {
    "feat": ["add", "new", "feature", "implement", "create"],
    "fix": ["fix", "bug", "error", "issue", "resolve", "correct"],
    "refactor": ["refactor", "rename", "move", "restructure"],
    "docs": ["doc", "readme", "comment", "documentation"],
    "style": ["style", "format", "lint", "whitespace", "indent"],
    "test": ["test", "spec", "assert", "mock"],
    "build": ["build", "package", "dependency", "setup"],
    "ci": ["ci", "pipeline", "workflow", "github", "actions"],
    "chore": ["chore", "cleanup", "remove", "delete", "update"],
    "perf": ["perf", "optimize", "speed", "performance", "fast"],
}

# Path patterns to scopes
PATH_TO_SCOPE = {
    "src/casino_calendar/dash_app/": "dash",
    "src/casino_calendar/dash_app/components/": "components",
    "src/casino_calendar/dash_app/layout/": "layout",
    "assets/styles/": "styles",
    "assets/scripts/": "theme",  # theme-toggle.js etc.
    "assets/": "assets",
    "scripts/": "scripts",
    "tests/": "tests",
    "config/": "config",
    "data/": "data",
    "docs/": "docs",
    "deploy/": "infra",
    "logs/": "logging",
    "src/casino_calendar/services/": "services",
    "src/casino_calendar/logging/": "logging",
    "src/casino_calendar/": "app",  # fallback
    "app.py": "app",
    "wsgi.py": "app",
    "requirements.txt": "deps",
    "package.json": "deps",
    "pyproject.toml": "deps",
    "setup.py": "deps",
}


def run_git_command(args):
    """Run a git command and return the output."""
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_staged_files():
    """Get list of staged files."""
    output = run_git_command(["diff", "--cached", "--name-only"])
    return output.splitlines() if output else []


def get_staged_diff():
    """Get the staged diff."""
    return run_git_command(["diff", "--cached"])


def infer_type(diff):
    """Infer the commit type from the diff."""
    diff_lower = diff.lower()
    type_counts = Counter()

    for commit_type, keywords in KEYWORDS_TO_TYPE.items():
        for keyword in keywords:
            if keyword in diff_lower:
                type_counts[commit_type] += diff_lower.count(keyword)  # Count occurrences

    if type_counts:
        most_common = type_counts.most_common(1)[0][0]
        # Special priority for feat if adding new files
        if "new file" in diff_lower and "feat" in type_counts:
            return "feat"
        return most_common

    # Default to 'chore' if no keywords match
    return "chore"


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
                parent_str = str(parent) + "/"
                if parent_str in PATH_TO_SCOPE:
                    scope_counts[PATH_TO_SCOPE[parent_str]] += 1
                    break

    if scope_counts:
        return scope_counts.most_common(1)[0][0]

    # Default scope
    return "app"


def generate_subject_with_ai(diff, staged_files):
    """Generate subject using AI."""
    if not AI_AVAILABLE:
        print("OpenAI not installed. Install with: pip install openai")
        return generate_subject_basic(diff, staged_files)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set. Using basic generation.")
        return generate_subject_basic(diff, staged_files)

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
Analyze the following git diff and staged files, and generate a short, imperative commit subject line (max 50 chars) that summarizes the changes.

Staged files: {', '.join(staged_files)}

Diff:
{diff[:2000]}  # Truncate if too long

Subject should be lowercase, no punctuation at end.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=50
        )
        subject = response.choices[0].message.content.strip()
        return subject.lower()
    except Exception as e:
        print(f"AI generation failed: {e}. Using basic generation.")
        return generate_subject_basic(diff, staged_files)


def generate_subject_basic(diff, staged_files):
    """Generate a short subject line (basic logic)."""
    if len(staged_files) == 1:
        file_path = staged_files[0]
        file_name = Path(file_path).name
        action = "add" if "new file" in diff else "update"
        # Try to make it more descriptive
        if "auto_commit" in file_name:
            return f"{action} automatic commit generation script"
        elif "package.json" in file_name:
            return f"{action} package scripts"
        else:
            return f"{action} {file_name}"
    elif len(staged_files) == 2:
        # Special case for current changes
        files = [Path(f).name for f in staged_files]
        if "auto_commit.py" in files and "package.json" in files:
            return "add automatic commit generation feature"
        else:
            return f"update {len(staged_files)} files"
    else:
        # Instead of using diff content, use file names
        file_names = [Path(f).name for f in staged_files]
        if len(file_names) <= 3:
            names_str = ", ".join(file_names)
            return f"update {names_str}"
        else:
            return f"update {len(staged_files)} files"


def generate_subject(diff, staged_files, use_ai=False):
    """Generate a short subject line."""
    if use_ai:
        return generate_subject_with_ai(diff, staged_files)
    else:
        return generate_subject_basic(diff, staged_files)


def generate_commit_message(use_ai=False):
    """Generate the full commit message."""
    staged_files = get_staged_files()
    if not staged_files:
        raise ValueError("No staged changes to commit")

    diff = get_staged_diff()
    commit_type = infer_type(diff)
    scope = infer_scope(staged_files)
    subject = generate_subject(diff, staged_files, use_ai)

    # Ensure lowercase subject
    subject = subject.lower()

    message = f"{commit_type}({scope}): {subject}"
    return message


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Auto-generate commit messages from staged changes.")
    parser.add_argument(
        "--ai", action="store_true", help="Use AI to generate the subject line (requires openai and OPENAI_API_KEY)"
    )
    args = parser.parse_args()

    try:
        while True:
            message = generate_commit_message(use_ai=args.ai)
            print(f"Generated commit message: {message}")
            print("Options: (a)ccept, (e)dit, (r)egenerate, (c)ancel")
            response = input("Choose an option: ").strip().lower()
            if response in ["a", "accept"]:
                run_git_command(["commit", "-m", message])
                print("Committed successfully!")
                break
            elif response in ["e", "edit"]:
                new_message = input("Enter new commit message: ").strip()
                if new_message:
                    run_git_command(["commit", "-m", new_message])
                    print("Committed with edited message!")
                    break
                else:
                    print("Message cannot be empty.")
            elif response in ["r", "regenerate"]:
                # Toggle AI for regeneration
                args.ai = not args.ai
                print(f"Regenerating with {'AI' if args.ai else 'basic'} logic...")
                continue
            elif response in ["c", "cancel"]:
                print("Commit cancelled.")
                break
            else:
                print("Invalid option. Please choose a, e, r, or c.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
