import os
import sys
import json
from datetime import datetime
from pathlib import Path

DSCS_DIR = '.dscs'

def init():
    """Initialize a new DSCS repository."""
    if os.path.exists(DSCS_DIR):
        print("DSCS repository already initialized.")
        return
    
    os.makedirs(DSCS_DIR)
    os.makedirs(f"{DSCS_DIR}/objects")
    os.makedirs(f"{DSCS_DIR}/refs/heads")
    
    with open(f"{DSCS_DIR}/HEAD", 'w') as head_file:
        head_file.write("ref: refs/heads/main\n")
    
    with open(f"{DSCS_DIR}/refs/heads/main", 'w') as main_branch:
        main_branch.write("")
    
    with open(f"{DSCS_DIR}/index", 'w') as index_file:
        index_file.write("{}")
    
    print("Initialized empty DSCS repository.")

def add(file_path):
    """Stage a file for commit."""
    if not os.path.exists(DSCS_DIR):
        print("Not a DSCS repository. Run 'dscs init' first.")
        return
    
    index_path = f"{DSCS_DIR}/index"
    with open(index_path, 'r') as index_file:
        index = json.load(index_file)
    
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    
    with open(file_path, 'rb') as f:
        content = f.read()
    file_hash = hash_object(content)
    
    object_path = f"{DSCS_DIR}/objects/{file_hash}"
    if not os.path.exists(object_path):
        with open(object_path, 'wb') as obj_file:
            obj_file.write(content)
    
    index[file_path] = file_hash
    
    with open(index_path, 'w') as index_file:
        json.dump(index, index_file)
    
    print(f"Staged {file_path} for commit.")

def hash_object(data):
    """Generate a hash for the given data."""
    import hashlib
    return hashlib.sha1(data).hexdigest()

def commit(message):
    """Create a new commit."""
    index_file = f"{DSCS_DIR}/index"
    head_file = f"{DSCS_DIR}/HEAD"
    objects_dir = f"{DSCS_DIR}/objects"
    
    # Load the index (staged changes)
    with open(index_file, 'r') as f:
        index = json.load(f)
    
    if not index:
        print("Nothing to commit (staging area is empty).")
        return
    
    # Get current HEAD reference
    with open(head_file, 'r') as f:
        head_ref = f.read().strip().split(": ")[1]
    
    # Read current branch's last commit (if exists)
    branch_file = f"{DSCS_DIR}/{head_ref}"
    parent_commit = None
    if os.path.exists(branch_file):
        with open(branch_file, 'r') as f:
            parent_commit = f.read().strip()
    
    # Create a new commit object
    commit_hash = str(hash(f"{index}{parent_commit}{message}{datetime.now()}"))
    commit_data = {
        "hash": commit_hash,
        "parent": parent_commit,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "changes": index
    }
    
    # Write commit to objects directory
    commit_path = f"{objects_dir}/{commit_hash}.json"
    with open(commit_path, 'w') as f:
        json.dump(commit_data, f, indent=4)
    
    # Update branch pointer
    with open(branch_file, 'w') as f:
        f.write(commit_hash)
    
    # Clear staging area
    with open(index_file, 'w') as f:
        json.dump({}, f)
    
    print(f"Commit successful. Commit hash: {commit_hash}")

def log():
    """Display commit history."""
    head_file = f"{DSCS_DIR}/HEAD"
    objects_dir = f"{DSCS_DIR}/objects"
    
    # Get current HEAD reference
    with open(head_file, 'r') as f:
        head_ref = f.read().strip().split(": ")[1]
    
    # Read current branch's last commit
    branch_file = f"{DSCS_DIR}/{head_ref}"
    if not os.path.exists(branch_file):
        print("No commits yet.")
        return
    
    with open(branch_file, 'r') as f:
        commit_hash = f.read().strip()
    
    # Traverse commit history
    while commit_hash:
        commit_path = f"{objects_dir}/{commit_hash}.json"
        if not os.path.exists(commit_path):
            break
        
        # Load commit data
        with open(commit_path, 'r') as f:
            commit_data = json.load(f)
        
        # Print commit details
        print("Commit:", commit_data["hash"])
        print("Message:", commit_data["message"])
        print("Timestamp:", commit_data["timestamp"])
        print()
        
        # Move to the parent commit
        commit_hash = commit_data["parent"]

def branch(branch_name=None):
    """Handle branch creation and listing branches."""
    refs_heads_dir = f"{DSCS_DIR}/refs/heads"
    
    if branch_name:
        # Create a new branch
        branch_path = f"{refs_heads_dir}/{branch_name}"
        if os.path.exists(branch_path):
            print(f"Branch '{branch_name}' already exists.")
            return
        
        with open(f"{DSCS_DIR}/HEAD", 'r') as head_file:
            current_commit = head_file.read().strip().split(": ")[1]
        
        with open(branch_path, 'w') as branch_file:
            branch_file.write(current_commit)
        
        print(f"Branch '{branch_name}' created.")
    else:
        # List all branches
        branches = os.listdir(refs_heads_dir)
        print("Branches:")
        for branch in branches:
            print(f"  - {branch}")
def switch(branch_name):
    """Switch to another branch."""
    branch_path = f"{DSCS_DIR}/refs/heads/{branch_name}"
    if not os.path.exists(branch_path):
        print(f"Branch '{branch_name}' does not exist.")
        return
    
    # Update HEAD to point to the new branch
    with open(f"{DSCS_DIR}/HEAD", 'w') as head_file:
        head_file.write(f"ref: refs/heads/{branch_name}\n")
    
    print(f"Switched to branch '{branch_name}'.")
def merge(branch_name):
    """Merge another branch into the current branch."""
    refs_heads_dir = f"{DSCS_DIR}/refs/heads"
    branch_path = f"{refs_heads_dir}/{branch_name}"
    
    if not os.path.exists(branch_path):
        print(f"Branch '{branch_name}' does not exist.")
        return
    
    # Get current branch and its HEAD
    with open(f"{DSCS_DIR}/HEAD", 'r') as head_file:
        current_branch_ref = head_file.read().strip().split(": ")[1]
    current_branch_path = f"{DSCS_DIR}/{current_branch_ref}"
    
    with open(current_branch_path, 'r') as current_file:
        current_commit = current_file.read().strip()
    
    with open(branch_path, 'r') as merge_file:
        merge_commit = merge_file.read().strip()
    
    # Detect conflicts (simple case: files changed in both branches)
    with open(f"{DSCS_DIR}/objects/{current_commit}.json", 'r') as current_commit_file:
        current_data = json.load(current_commit_file)
    
    with open(f"{DSCS_DIR}/objects/{merge_commit}.json", 'r') as merge_commit_file:
        merge_data = json.load(merge_commit_file)
    
    current_changes = current_data["changes"]
    merge_changes = merge_data["changes"]
    
    conflicts = []
    for file, content in merge_changes.items():
        if file in current_changes and current_changes[file] != content:
            conflicts.append(file)
    
    if conflicts:
        print("Merge conflicts detected in the following files:")
        for conflict in conflicts:
            print(f"  - {conflict}")
        print("Please resolve conflicts manually.")
        return
    
    # Create a new merge commit
    new_commit_data = {
        "hash": str(hash(f"{current_commit}{merge_commit}{datetime.now()}")),
        "parent": [current_commit, merge_commit],
        "message": f"Merge branch '{branch_name}'",
        "timestamp": datetime.now().isoformat(),
        "changes": {**current_changes, **merge_changes}
    }
    
    new_commit_path = f"{DSCS_DIR}/objects/{new_commit_data['hash']}.json"
    with open(new_commit_path, 'w') as new_commit_file:
        json.dump(new_commit_data, new_commit_file, indent=4)
    
    # Update current branch to point to the new commit
    with open(current_branch_path, 'w') as current_branch_file:
        current_branch_file.write(new_commit_data["hash"])
    
    print(f"Branch '{branch_name}' merged successfully into the current branch.")
def diff(commit_hash=None):
    """Show differences between states."""
    index_file = f"{DSCS_DIR}/index"
    objects_dir = f"{DSCS_DIR}/objects"
    
    # Compare working directory with staging area
    if not commit_hash:
        with open(index_file, 'r') as f:
            staged_changes = json.load(f)
        
        for file in staged_changes:
            with open(file, 'r') as current_file:
                current_content = current_file.read()
            
            staged_content = staged_changes[file]
            if current_content != staged_content:
                print(f"Diff for {file}:")
                print("- Current:", current_content)
                print("- Staged:", staged_content)
                print()
        return
    
    # Compare two commits
    commit_path = f"{objects_dir}/{commit_hash}.json"
    if not os.path.exists(commit_path):
        print(f"Commit '{commit_hash}' not found.")
        return
    
    with open(commit_path, 'r') as commit_file:
        commit_data = json.load(commit_file)
    
    print("Changes in commit:")
    for file, content in commit_data["changes"].items():
        print(f"{file} -> {content}")

def main():
    commands = {
        "init": init,
        "add": lambda: add(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No file specified for 'add' command."),
        "commit": lambda: commit(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No commit message provided."),
        "log": log,
        "branch": lambda: branch(sys.argv[2]) if len(sys.argv) > 2 else branch(),
        "switch": lambda: switch(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No branch specified."),
        "merge": lambda: merge(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No branch specified."),
        "diff": lambda: diff(sys.argv[2]) if len(sys.argv) > 2 else diff(),


        # Other commands will be added here.
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: dscs <command>")
        return
    
    command = sys.argv[1]
    commands[command]()

if __name__ == "__main__":
    main()
