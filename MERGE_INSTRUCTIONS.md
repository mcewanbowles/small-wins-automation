# Merge Instructions: Creating Branch of Truth

## Purpose
Merge `copilot/add-terms-of-use` into `copilot/enhance-automation-system` to create a single authoritative "branch of truth" containing all latest work.

---

## Why This Merge is Needed

**Current Situation:**
- `copilot/enhance-automation-system` has: Product files, documentation, TpT packages
- `copilot/add-terms-of-use` has: New TOU and Quick Start files

**After Merge:**
- Single branch with everything
- New TOU and Quick Start available
- Easier to manage and develop
- Ready for final package generation

---

## Pre-Merge Checklist

**Before starting, ensure:**
- [ ] You have both branches locally
- [ ] Current branch is `copilot/enhance-automation-system`
- [ ] Working directory is clean (no uncommitted changes)
- [ ] You've pulled latest from both branches

---

## Step-by-Step Merge Instructions

### Step 1: Prepare Your Environment

```bash
# Navigate to repository
cd /path/to/small-wins-automation

# Check current branch
git branch
# Should show: * copilot/enhance-automation-system

# Ensure working directory is clean
git status
# Should show: nothing to commit, working tree clean
```

### Step 2: Update Both Branches

```bash
# Update current branch
git pull origin copilot/enhance-automation-system

# Fetch the other branch
git fetch origin copilot/add-terms-of-use

# Or if it's only local:
# Make sure you're on the right branch
git checkout copilot/enhance-automation-system
```

### Step 3: Perform the Merge

```bash
# Merge copilot/add-terms-of-use into current branch
git merge copilot/add-terms-of-use

# Or if branch is only local:
git merge copilot/add-terms-of-use --no-ff -m "Merge copilot/add-terms-of-use to create branch of truth"
```

### Step 4: Resolve Conflicts (if any)

**If you see merge conflicts:**

```bash
# Check which files have conflicts
git status

# For each conflicted file:
# 1. Open the file
# 2. Look for conflict markers: <<<<<<<, =======, >>>>>>>
# 3. Decide which version to keep or combine both
# 4. Remove conflict markers
# 5. Save the file

# Mark as resolved
git add <filename>

# Complete the merge
git commit -m "Merge copilot/add-terms-of-use - resolved conflicts"
```

**Common files that might conflict:**
- Generator scripts
- Documentation files
- Package structure files

**Resolution strategy:**
- Keep latest versions
- Combine if both have valuable content
- Test after resolving

### Step 5: Verify the Merge

```bash
# Check that new files are present
ls -la assets/global/tpt_support_docs/

# Should see:
# - Terms_of_Use.pdf (NEW version)
# - Quick_Start.pdf (NEW version)

# Check git log
git log --oneline -5

# Should show merge commit
```

### Step 6: Push Merged Branch

```bash
# Push to remote
git push origin copilot/enhance-automation-system

# Verify push was successful
git status
# Should show: Your branch is up to date with 'origin/copilot/enhance-automation-system'
```

---

## What to Check After Merge

**Verify these files exist:**

1. **New TOU:**
   - Location: `assets/global/tpt_support_docs/Terms_of_Use.pdf`
   - Or similar location from the other branch

2. **New Quick Start:**
   - Location: `assets/global/tpt_support_docs/Quick_Start.pdf`
   - Or similar location from the other branch

3. **Existing Files Still Present:**
   - `final_products/brown_bear/matching/` (all FINAL PDFs)
   - `PRODUCT_STANDARD.md`
   - `tpt_packages/` (all ZIP files)
   - Generator scripts

**Run a quick test:**
```bash
# List final products
ls -lh final_products/brown_bear/matching/

# Check TpT packages
ls -lh tpt_packages/

# Verify new files
file assets/global/tpt_support_docs/*.pdf
```

---

## After Merge is Complete

**Notify Copilot:**
1. Confirm merge is complete
2. Confirm new TOU and Quick Start are in place
3. Confirm no conflicts remain

**Copilot will then:**
1. Pull the merged branch
2. Regenerate all TpT packages with new files
3. Create marketing materials (previews, thumbnails, descriptions)
4. Archive obsolete versions
5. Complete the automation system

**Expected timeline:** 30-60 minutes

---

## Troubleshooting

### Problem: Merge Conflicts

**Solution:**
- Carefully review each conflict
- Keep the most recent version
- When in doubt, keep both and combine
- Test after resolving

### Problem: File Not Found After Merge

**Solution:**
```bash
# Check if file exists in other branch
git show copilot/add-terms-of-use:path/to/file.pdf

# If it exists, the path might be different
# Find it:
git ls-tree -r copilot/add-terms-of-use --name-only | grep -i "terms"
```

### Problem: Merge Commit Not Pushing

**Solution:**
```bash
# Pull latest first
git pull origin copilot/enhance-automation-system --rebase

# Then push
git push origin copilot/enhance-automation-system
```

---

## Alternative: Manual File Copy

**If merge is too complex:**

1. **Get files from other branch:**
   ```bash
   git checkout copilot/add-terms-of-use
   cp assets/global/tpt_support_docs/Terms_of_Use.pdf /tmp/
   cp assets/global/tpt_support_docs/Quick_Start.pdf /tmp/
   git checkout copilot/enhance-automation-system
   ```

2. **Copy to current branch:**
   ```bash
   cp /tmp/Terms_of_Use.pdf assets/global/tpt_support_docs/
   cp /tmp/Quick_Start.pdf assets/global/tpt_support_docs/
   ```

3. **Commit:**
   ```bash
   git add assets/global/tpt_support_docs/*.pdf
   git commit -m "Add new TOU and Quick Start from copilot/add-terms-of-use"
   git push origin copilot/enhance-automation-system
   ```

---

## Summary

**Goal:** Single "branch of truth" with all work
**Method:** Merge copilot/add-terms-of-use → copilot/enhance-automation-system
**Result:** Consolidated branch ready for final automation

**Key Files Needed:**
- New Terms of Use PDF
- New Quick Start PDF

**Next Steps:**
- Complete merge
- Push to remote
- Notify Copilot
- Continue with package generation

---

**Status:** Ready to merge
**Time required:** 10-15 minutes (plus conflict resolution if needed)
**Benefit:** Single authoritative branch for all future work
