#!/bin/bash

# Fetching remote branches and pruning stale tracking branches
git fetch --prune

# Get the list of all local branches
all_local_branches=$(git branch | sed 's/^* //')

# Iterate through all local branches
for branch in $all_local_branches; do
    delete_branch=false

    # Check if the branch name starts with "pr/"
    if [[ "$branch" == pr/* ]]; then
        echo "Considering deletion (prefix 'pr/'): $branch"
        delete_branch=true
    else
        # Check if the branch has a remote counterpart
        remote=$(git config --get "branch.$branch.remote")
        tracking_branch=$(git config --get "branch.$branch.merge")

        if [ -z "$remote" ] && [ -z "$tracking_branch" ]; then
            # If no remote and no tracking branch, it likely has no remote counterpart
            echo "Considering deletion (no remote): $branch"
            delete_branch=true
        elif [ -n "$remote" ] && [ -n "$tracking_branch" ]; then
            # Check if the remote tracking branch is gone
            remote_branch_exists=$(git rev-parse --verify --quiet "$remote/$branch")
            if [ -z "$remote_branch_exists" ]; then
                echo "Considering deletion (remote gone): $branch"
                delete_branch=true
            fi
        fi
    fi

    if "$delete_branch"; then
        echo "Deleting local branch: $branch"
        git branch -D "$branch" # Use -D to force delete if necessary
    fi
done

echo "Cleanup complete."
