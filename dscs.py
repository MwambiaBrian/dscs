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

def main():
    commands = {
        "init": init,
        # Other commands will be added here.
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: dscs <command>")
        return
    
    command = sys.argv[1]
    commands[command]()

if __name__ == "__main__":
    main()
