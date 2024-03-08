#!/bin/bash

# Fetching remote branches
git fetch --prune

# Get the list of local branches
local_branches=$(git branch -vv | grep ": gone]" | awk '{print $1}')

# Iterate through local branches and delete those without remotes
for branch in $local_branches; do
    remote=$(git config --get branch.$branch.remote)
    
    if [ -z "$remote" ]; then
        # If remote is empty, branch doesn't have a remote counterpart
        echo "Deleting local branch: $branch"
        git branch -d $branch
    fi
done

echo "Cleanup complete."
