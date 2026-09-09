"""Test that Word Search grids are always solvable — every target word
can be found in the grid in one of 8 directions.

This test exists because of a bug where Level 1 (isolate_words=True)
silently enlarged the grid from 8x8 to 9x9 inside create_word_search_grid,
but the rendering code still used the original grid_size=8, dropping the
last row and making 3 of 6 words physically missing from the student
puzzle while the answer key showed the full 9x9 grid.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import pytest
from Studioforge._TRUTH.WORD_SEARCH import create_word_search_grid, verify_grid_solvable


WORDS = ["school", "friend", "pencil", "happy", "teacher", "learn", "sit", "new"]


@pytest.mark.parametrize("level,grid_size,use_symbols,allow_diagonal,isolate", [
    (1, 8, True, False, True),    # Level 1 — the bug scenario
    (2, 8, False, False, False),  # Level 2
    (3, 9, False, True, False),   # Level 3
    (4, 10, False, True, False),  # Level 4
])
def test_grid_solvable_all_levels(level, grid_size, use_symbols, allow_diagonal, isolate):
    """Every generated grid must contain all target words."""
    random.seed(42 + level)
    grid, positions = create_word_search_grid(
        WORDS, grid_size=grid_size, use_symbols=use_symbols,
        allow_diagonal=allow_diagonal, isolate_words=isolate,
    )
    solvable, missing = verify_grid_solvable(grid, WORDS)
    assert solvable, f"Level {level}: words missing from grid: {missing}"


def test_level1_grid_is_9x9_when_isolated():
    """Level 1 must enlarge to 9x9 — and all rendering must use len(grid)."""
    random.seed(42)
    grid, _ = create_word_search_grid(
        WORDS, grid_size=8, use_symbols=True,
        allow_diagonal=False, isolate_words=True,
    )
    assert len(grid) == 9, f"Level 1 grid should be 9x9, got {len(grid)}x{len(grid[0])}"


def test_verify_grid_detects_missing_word():
    """The solvability checker must catch a deliberately broken grid."""
    # 3x3 grid with only "CAT" — "DOG" is not present
    grid = [
        ["C", "A", "T"],
        ["X", "Y", "Z"],
        ["P", "Q", "R"],
    ]
    solvable, missing = verify_grid_solvable(grid, ["cat", "dog"])
    assert not solvable
    assert "dog" in missing


def test_verify_grid_finds_diagonal_words():
    """The solvability checker must find words in all 8 directions."""
    grid = [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ]
    # AEI is diagonal down-right
    solvable, missing = verify_grid_solvable(grid, ["aei"])
    assert solvable, f"Diagonal word should be found, missing: {missing}"
