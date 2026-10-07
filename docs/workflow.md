# Git and integration workflow

Use the existing checkout. Cloud tasks are already isolated; do not create a
worktree unless explicitly requested. Never overwrite teammates' local changes.

Work on feature branches: `feature/frontend`, `feature/api`, `feature/auth`,
`feature/activities`, `feature/admin`. Person 1 reviews and integrates changes.
The cloud checkout currently uses `work`; no branch rename or remote push is
required just to develop. Confirm shared branch policy before publishing work.

1. Update from the shared branch before beginning, preserving local work.
2. Keep commits focused; inspect the diff and exclude secrets/generated files.
3. Open a PR with behavior, interface changes, and actual test evidence.
4. Person 1 reviews compatibility and merges one dependent change at a time.
5. Rerun affected user flows after each merge; record results.

Assign a single integrator to shared `app.py`, dependency declarations, and
base navigation changes. Feature owners provide blueprint imports/registration
instructions rather than independently rewriting the factory.

Prioritize integrated required features. The plan targets Wednesday feature
completion and Thursday 6 PM freeze; confirm timezone and instructor deadline.
After freeze, limit work to defects, tests, documentation, and presentation.
