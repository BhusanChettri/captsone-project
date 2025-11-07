# Git Workflow Guide

## Branch Strategy

We use a **two-branch workflow** for safe development:

- **`master`**: Production-ready, stable code (protected)
- **`dev`**: Development branch for new features and changes

## Current Setup

✅ **`dev` branch created** from `master`  
✅ **`dev` branch pushed** to GitHub  
✅ **Currently on `dev` branch**

## Daily Workflow

### 1. Working on Features

Always work on the `dev` branch:

```bash
# Make sure you're on dev branch
git checkout dev

# Pull latest changes
git pull origin dev

# Make your changes, then commit
git add .
git commit -m "Description of changes"

# Push to dev branch
git push origin dev
```

### 2. Testing on Dev Branch

- Test all changes thoroughly on `dev` branch
- Run tests: `pytest tests/`
- Test end-to-end: `python test_end_to_end.py`
- Test UI: `python app.py`

### 3. Merging to Master (When Ready)

Once everything is tested and working on `dev`:

```bash
# Switch to master branch
git checkout master

# Pull latest master (in case of updates)
git pull origin master

# Merge dev into master
git merge dev

# Push to master
git push origin master
```

## Branch Commands Reference

### Check Current Branch
```bash
git branch --show-current
```

### Switch Branches
```bash
# Switch to dev
git checkout dev

# Switch to master
git pull origin master
git checkout master
```

### View All Branches
```bash
git branch -a
```

### Create New Feature Branch (Optional)
```bash
# Create feature branch from dev
git checkout dev
git checkout -b feature/new-feature-name

# Work on feature, then merge back to dev
git checkout dev
git merge feature/new-feature-name
```

## Best Practices

1. ✅ **Always work on `dev` branch** for new changes
2. ✅ **Test thoroughly** before merging to `master`
3. ✅ **Commit frequently** with clear messages
4. ✅ **Pull before pushing** to avoid conflicts
5. ✅ **Never push directly to `master`** (use merge from `dev`)

## GitHub Protection (Recommended)

Consider protecting the `master` branch on GitHub:

1. Go to: `Settings` → `Branches`
2. Add branch protection rule for `master`
3. Require pull request reviews
4. Require status checks to pass
5. Prevent force pushes

This ensures `master` can only be updated via pull requests from `dev`.

## Merge Workflow Diagram

```
dev branch (development)
    │
    │ (work, test, commit)
    │
    ▼
[Testing Complete]
    │
    │ (merge)
    ▼
master branch (production)
    │
    │ (deploy)
    ▼
Production
```

## Troubleshooting

### If you accidentally commit to master:
```bash
# Move commits to dev
git checkout master
git log --oneline -1  # Note the commit hash
git checkout dev
git cherry-pick <commit-hash>
git checkout master
git reset --hard HEAD~1  # Remove from master
```

### If branches are out of sync:
```bash
# Update dev with latest master
git checkout dev
git merge master

# Or rebase (cleaner history)
git checkout dev
git rebase master
```

## Current Status

- **Active Branch**: `dev`
- **Master Branch**: Protected (stable)
- **Remote**: `origin` → `https://github.com/BhusanChettri/captsone-project.git`

---

**Remember**: Always work on `dev`, test thoroughly, then merge to `master` when ready! 🚀

