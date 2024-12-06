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


def main():
    commands = {
        "init": init,
        "add": lambda: add(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No file specified for 'add' command."),
         "commit": lambda: commit(sys.argv[2]) if len(sys.argv) > 2 else print("Error: No commit message provided."),
          "log": log,
        # Other commands will be added here.
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: dscs <command>")
        return
    
    command = sys.argv[1]
    commands[command]()

if __name__ == "__main__":
    main()
