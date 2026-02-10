#!/bin/bash
# Quick Save Script - Save your work quickly and safely
# Usage: ./quick_save.sh

set -e  # Exit on error

echo ""
echo "🛡️  QUICK SAVE - Protecting Your Work"
echo "======================================"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Warn if not on main working branch
if [[ "$CURRENT_BRANCH" != "copilot/enhance-automation-system" ]]; then
    echo "⚠️  WARNING: You're not on the main working branch!"
    echo "   Consider switching: git checkout copilot/enhance-automation-system"
    echo ""
fi

# Check if there are changes
if [[ -z $(git status -s) ]]; then
    echo "✅ No changes to save - you're all caught up!"
    echo ""
    exit 0
fi

# Show what will be saved
echo "📝 Changes to save:"
echo ""
git status -s
echo ""

# Ask for confirmation
read -p "💾 Save these changes? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "💾 Saving..."
    
    # Add all changes
    git add .
    
    # Ask for commit message (or use default)
    echo ""
    read -p "📝 Commit message (or press Enter for timestamp): " COMMIT_MSG
    
    if [[ -z "$COMMIT_MSG" ]]; then
        COMMIT_MSG="Quick save: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    # Create commit
    git commit -m "$COMMIT_MSG"
    
    echo ""
    echo "📤 Pushing to GitHub..."
    
    # Push to GitHub
    if git push; then
        echo ""
        echo "✅ SAVED SUCCESSFULLY!"
        echo "   Your work is safe on GitHub 🎉"
        echo ""
    else
        echo ""
        echo "⚠️  Changes committed locally but push failed"
        echo "   Your work is saved on your computer"
        echo "   Try: git push"
        echo ""
    fi
else
    echo ""
    echo "❌ Save cancelled - no changes made"
    echo ""
fi
