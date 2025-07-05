# Git Cheat-Sheet

## Table of Contents

1. [Basic Status & Inspection](#basic-status--inspection)  
2. [Creating & Switching Branches](#creating--switching-branches)  
3. [Checkout a Remote Branch Locally](#checkout-a-remote-branch-locally)  
4. [Switch Back to `main` Without Merging](#switch-back-to-main-without-merging)  
5. [Pull (Update Your Local Branch)](#pull-update-your-local-branch)  
6. [Commit Your Changes on the Current Branch](#commit-your-changes-on-the-current-branch)  
7. [Merge a Feature Branch into `main`](#merge-a-feature-branch-into-main)  
8. [Fix the Previous Commit (Minor Changes)](#fix-the-previous-commit-minor-changes)  
9. [Stash Changes](#stash-changes)  
10. [Run the Dash App on a Checked-Out Branch](#run-the-dash-app-on-a-checked-out-branch)  
11. [View a Past Commit (Detached HEAD)](#view-a-past-commit-detached-head)  
12. [Reset Your Branch to a Specific Commit](#reset-your-branch-to-a-specific-commit)  
13. [Point Your Branch at a Specific Commit](#point-your-branch-at-a-specific-commit)  
14. [Revert a Merged PR & Clean Up Its Branch](#revert-a-merged-pr--clean-up-its-branch)  
15. [Delete a Merged Branch](#delete-a-merged-branch)  
16. [Update Your Local Directory After a Branch Has Been Merged & Deleted](#update-your-local-directory-after-a-branch-has-been-merged--deleted)  
17. [Handling Merge Conflicts](#handling-merge-conflicts)  
18. [Interactive Rebase & History Cleanup](#interactive-rebase--history-cleanup)  
19. [Cherry-Pick a Commit](#cherry-pick-a-commit)  
20. [Tagging Releases](#tagging-releases)  
21. [Remote Management](#remote-management)  
22. [Config & Help](#config--help)  

---

## Basic Status & Inspection

```bash
# 1. See what’s changed & staged
git status

# 2. View diffs
git diff           # unstaged
git diff --staged  # staged

# 3. Browse commit history as a graph
git log --oneline --graph --decorate --all
````

✔️ **Use when:** you want a quick health-check or to explore your history.

---

## Creating & Switching Branches

```bash
# 1. Create & switch in one go
git checkout -b my-new-branch

# 2. Switch to an existing branch
git checkout other-branch
# —or—
git switch other-branch

# 3. List all local branches
git branch
```

✔️ **Use when:** you need to start a new line of work or jump between contexts.

---

## Checkout a Remote Branch Locally

```bash
# 1. Fetch all remote updates
git fetch origin

# 2. (Optional) List remote branches
git branch -r

# 3. Create & switch to a tracking branch
git checkout --track origin/feature-branch
```

✔️ **Use when:** you want to preview or work on a branch that exists on GitHub but not yet locally.

---

## Switch Back to `main` Without Merging

```bash
# 1. (Optional) Stash or discard WIP
git stash push -m "WIP before switching"
# or to discard:
git reset --hard HEAD
git clean -fd

# 2. Switch to main
git checkout main
# —or—
git switch main

# 3. Verify
git status  # On branch main

# 4. (Optional) Delete the feature branch
git branch -d feature-branch    # if merged
git branch -D feature-branch    # force if unmerged
```

✔️ **Use when:** you want to abandon a feature branch and return to `main` without merging its changes.

---

## Pull (Update Your Local Branch)

```bash
# 1. Fetch remote updates
git fetch origin

# 2. Merge remote changes
git pull

# —or—

# 3. Rebase your local commits on top of remote
git pull --rebase
```

✔️ **Use when:** you want to ensure your tracking branch reflects the latest on GitHub.

---

## Commit Your Changes on the Current Branch

```bash
# 1. Ensure you’re on your feature branch
git checkout feature-branch

# 2. Stage modified files
git add [files]

# 3. Commit with a descriptive message
git commit -m "Describe what you changed"

# 4. Push to remote
git push
```

✔️ **Use when:** you’ve made edits on your feature branch and want to save them.

---

## Merge a Feature Branch into `main`

```bash
# 1. Switch to main & update
git checkout main
git pull origin main

# 2. Merge your feature branch
git merge feature-branch

# 3. If there are conflicts:
#    a. Open each conflicted file and resolve the <<<< / >>>> markers.
#    b. Stage the resolved files:
git add [fixed-files]
#    c. Complete the merge:
git commit

# 4. Push the updated main
git push origin main

# 5. (Optional) Delete the merged branch locally
git branch -d feature-branch

# 6. (Optional) Delete it on the remote
git push origin --delete feature-branch
```

✔️ **Use when:** your feature is ready and you want to integrate it into `main`; follow conflict-resolution steps if needed.

---

## Fix the Previous Commit (Minor Changes)

```bash
# 1. Stage the fix
git add [file]

# 2. Amend the previous commit without editing the message
git commit --amend --no-edit

# 3. Force-push the amended commit
git push --force
```

✔️ **Use when:** you just pushed a commit, notice a small mistake, and want to avoid a messy new commit.

---

## Stash Changes

```bash
# 1. Stash tracked changes
git stash

# 2. Stash with a message
git stash push -m "WIP: describe work"

# 3. Include untracked files
git stash push -u

# 4. Stash everything (including ignored)
git stash push -a

# 5. List all stashes
git stash list

# 6. Show a stash’s diff
git stash show stash@{0}

# 7. Apply without dropping
git stash apply stash@{0}

# 8. Apply & drop
git stash pop stash@{0}

# 9. Drop a specific stash
git stash drop stash@{0}

# 10. Clear all stashes
git stash clear

# 11. Create & switch to a branch from a stash
git stash branch my-temp-branch stash@{0}
```

✔️ **Use when:** you need to shelve work to switch branches, pull updates, experiment, or start a fresh branch with stashed changes.

---

## Run the Dash App on a Checked-Out Branch

```bash
# 1. Confirm you’re on the right branch
git branch   # current branch marked with *

# 2. (Optional) Pull updates
git pull     # ensure branch is up to date

# 3. Activate your virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows cmd.exe:
.\.venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt

# 5. Launch the Dash server
python app.py  # default: http://127.0.0.1:8050
```

✔️ **Use when:** you’ve checked out a branch and want to run your Dash app against its code.

---

## View a Past Commit (Detached HEAD)

```bash
# 1. Fetch remote updates
git fetch origin

# 2. Check out the commit by its SHA
git checkout <commit-hash>
```

✔️ **Use when:** you want to inspect or run code at an arbitrary commit without altering branch pointers.

---

## Reset Your Branch to a Specific Commit

```bash
# 1. Switch to your feature branch
git checkout feature-branch

# 2. Reset to the specified commit
git reset --hard <commit-hash>
```

✔️ **Use when:** you need to move your branch pointer to a given commit, discarding uncommitted work.

---

## Point Your Branch at a Specific Commit

```bash
# 1. Switch to your feature branch
git checkout feature-branch

# 2. (Optional) Fetch remote updates
git fetch origin

# 3. Reset the branch pointer
git reset --hard <commit-hash>

# 4. Force-push to update remote
git push --force
```

> ⚠️ **Warning:**
>
> * `--hard` discards uncommitted changes.
> * `--force` rewrites remote history—use only when you’re sure.

✔️ **Use when:** you need to roll your branch to a known commit and discard intervening commits.

---

## Revert a Merged PR & Clean Up Its Branch

```bash
# 1. Switch to main & update
git checkout main
git pull origin main

# 2. Find the merge commit SHA
git log --oneline   # look for "Merge pull request #…" → e.g. abcd123

# 3. Revert the merge commit
git revert -m 1 abcd123

# 4. Push the revert
git push origin main

# 5. Delete the old feature branch locally
git branch -d feature-branch

# 6. Delete the old feature branch remotely
git push origin --delete feature-branch
```

✔️ **Use when:** you’ve merged a PR into `main` and need to undo its changes, then remove its branch.

---

## Delete a Merged Branch

```bash
# 1. Delete the branch locally (only if merged)
git branch -d feature-branch

# 2. Delete the branch on GitHub
git push origin --delete feature-branch
```

✔️ **Use when:** the branch has been merged into `main` and you want to clean it up locally and remotely.

---

## Update Your Local Directory After a Branch Has Been Merged & Deleted

```bash
# 1. Prune stale remote-tracking branches
git fetch --prune
# or:
git remote prune origin

# 2. Switch to main
git checkout main
# or:
git switch main

# 3. Pull the latest merged changes
git pull origin main

# 4. Verify your branches
git branch -a  # feature-branch should be gone
```

✔️ **Use when:** you’ve merged a PR into `main`, deleted the remote branch, and want your local clone to match.

---

## Handling Merge Conflicts

```bash
# 1. After a failed merge or rebase, resolve the <<<< / >>>> markers in your editor
# 2. Stage the resolved files
git add [fixed-files]

# 3a. If merging:
git commit           # completes the merge

# 3b. If rebasing:
git rebase --continue
```

✔️ **Use when:** Git can’t automatically reconcile two sets of changes.

---

## Interactive Rebase & History Cleanup

```bash
# 1. Start an interactive rebase to squash, reorder, or fixup
git rebase -i HEAD~5   # last 5 commits

# 2. In the editor: choose pick/squash/fixup/reword
# 3. Save & exit to rewrite history
```

✔️ **Use when:** you want a cleaner commit history before pushing.

---

## Cherry-Pick a Commit

```bash
# 1. Grab a single commit from elsewhere
git cherry-pick <commit-hash>

# 2. Resolve conflicts (if any), then:
git cherry-pick --continue
```

✔️ **Use when:** you need one change without merging an entire branch.

---

## Tagging Releases

```bash
# 1. Create an annotated tag
git tag -a v1.2.0 -m "Release v1.2.0"

# 2. Push tags to remote
git push origin v1.2.0
# —or— all tags
git push origin --tags
```

✔️ **Use when:** you want to mark a stable point in your history.

---

## Remote Management

```bash
# 1. List all remotes
git remote -v

# 2. Add a new remote
git remote add upstream git@github.com:orig/repo.git

# 3. Remove or rename a remote
git remote remove origin
git remote rename upstream origin
```

✔️ **Use when:** you’re collaborating against forks or juggling multiple servers.

---

## Config & Help

```bash
# 1. Set your identity globally
git config --global user.name "Your Name"
git config --global user.email you@example.com

# 2. Read Git’s built-in manual
git help <command>   # e.g. git help rebase
```

✔️ **Use when:** you need to tweak settings or dive deeper.
