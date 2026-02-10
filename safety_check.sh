#!/bin/bash
# Safety Check Script - Run before making big changes
# Usage: ./safety_check.sh

set -e  # Exit on error

echo ""
echo "🛡️  SAFETY CHECK - Pre-Flight Checklist"
echo "========================================"
echo ""

EXIT_CODE=0

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# 1. Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

if [[ "$CURRENT_BRANCH" != "copilot/enhance-automation-system" ]]; then
    echo "   ⚠️  Not on main working branch!"
    echo "   Switch with: git checkout copilot/enhance-automation-system"
    EXIT_CODE=1
else
    echo "   ✅ On correct branch"
fi
echo ""

# 2. Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Uncommitted changes detected:"
    git status -s
    echo "   ⚠️  Please commit these first!"
    echo "   Use: ./quick_save.sh"
    EXIT_CODE=1
else
    echo "📝 Working directory: ✅ Clean"
fi
echo ""

# 3. Check if tests exist and run them
if [[ -f "test_system.py" ]]; then
    echo "🧪 Running tests..."
    
    if python3 test_system.py > /tmp/test_output.txt 2>&1; then
        echo "   ✅ All tests passed!"
    else
        echo "   ❌ Tests failed!"
        echo ""
        echo "   Last few lines of output:"
        tail -10 /tmp/test_output.txt
        echo ""
        echo "   Fix tests before making changes"
        EXIT_CODE=1
    fi
else
    echo "🧪 No test file found (test_system.py)"
    echo "   ⚠️  Consider adding tests"
fi
echo ""

# Summary
echo "======================================"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ ALL CHECKS PASSED!"
    echo "   Safe to make changes 🎉"
else
    echo "⚠️  SOME CHECKS FAILED"
    echo "   Fix issues above before proceeding"
fi
echo "======================================"
echo ""

exit $EXIT_CODE
