"""Dice rolling subsystem with deterministic seeding."""
import random
from typing import Optional


class DiceRoller:
    """Deterministic dice roller for harvest and random mechanics."""

    def __init__(self, seed: Optional[int] = None, num_sides: int = 6) -> None:
        self.num_sides = num_sides
        self.rng = random.Random(seed)

    def roll(self) -> int:
        """Rolls a single die returning an integer from 1 to num_sides."""
        return self.rng.randint(1, self.num_sides)
