"""Exception hierarchy for Pincer simulation engine."""


class PincerError(Exception):
    """Base exception for all Pincer engine errors."""
    pass


class InvalidActionError(PincerError):
    """Raised when an action is fundamentally invalid or illegal under the current game state."""
    pass


class RuleViolationError(InvalidActionError):
    """Raised when an action violates specific board game rules."""
    pass


class IllegalMovementError(RuleViolationError):
    """Raised when a unit attempts an illegal move (range, terrain, enemy blocked)."""
    pass


class IllegalPlacementError(RuleViolationError):
    """Raised when an infrastructure or unit placement violates placement rules."""
    pass


class PhaseOrderError(InvalidActionError):
    """Raised when an action is executed during the wrong turn phase."""
    pass


class ResourceDeficitError(RuleViolationError):
    """Raised when a player attempts to buy or trade without sufficient resources."""
    pass
