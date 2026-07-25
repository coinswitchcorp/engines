import subprocess
import tempfile
import os

REMOTE = "origin"

def run(cmd, check=True):
    print(">", " ".join(cmd))
    return subprocess.run(cmd, check=check)

def output(cmd):
    return subprocess.check_output(cmd, text=True).strip()

# Make sure there are local changes
status = output(["git", "status", "--porcelain"])
if not status:
    print("No local changes found.")
    exit(0)

# Save current branch
current_branch = output(["git", "branch", "--show-current"])

# Save local changes to a patch
patch_file = tempfile.NamedTemporaryFile(delete=False, suffix=".patch")
patch_file.close()

with open(patch_file.name, "w", encoding="utf-8") as f:
    subprocess.run(["git", "diff"], stdout=f, check=True)

# Get all local branches
branches = output([
    "git",
    "for-each-ref",
    "--format=%(refname:short)",
    "refs/heads"
]).splitlines()

# Get all remote branches
remote_branches = subprocess.check_output(
    ["git", "branch", "-r"],
    text=True
).splitlines()

remote_branches = [b.strip() for b in remote_branches]

print(remote_branches)
print("=================================")
for branch in branches:
    print(f"\n===== {branch} =====")

    run(["git", "checkout", branch])

    # Clean working tree
    run(["git", "reset", "--hard"])

    # Apply patch
    result = subprocess.run(["git", "apply", patch_file.name])

    if result.returncode != 0:
        print(f"Skipping {branch}: patch could not be applied.")
        run(["git", "reset", "--hard"])
        continue

    # Stage all files
    run(["git", "add", "-A"])

    # Skip if no changes
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("No changes for this branch.")
        continue

    # Update last commit, keep same commit message
    run(["git", "commit", "--amend", "--no-edit"])

    # Push updated branch
    run([
        "git",
        "push",
        "--force-with-lease",
        REMOTE,
        branch
    ])

# Restore original branch
run(["git", "checkout", current_branch])

os.unlink(patch_file.name)

print("\nDone.")