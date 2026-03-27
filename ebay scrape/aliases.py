# Alias dictionary for card sets and players

SET_ALIASES = {
    "ucl": "uefa champions league",
    "uefa": "uefa champions league",
    "optic": "donruss optic",
    "chrome": "topps chrome",
    "prizm": "panini prizm",
    "select": "panini select",
    # Hungarian-to-English translations for card items
    "krom": "chrome",
    "kromos": "chrome",
    "ujonc": "rookie",
    "rc": "rookie",
    "eladva": "sold",
    "refraktor": "refractor",
    "folt": "patch",
    "automata": "auto"
}

PLAYER_ALIASES = {
    "cr7": "cristiano ronaldo",
    "messi": "lionel messi",
    "vinicius": "vinicius jr",
    "vini": "vinicius jr",
    "lula": "luis suarez", # Careful with this one
    "haaland": "erling haaland",
    "mbappe": "kylian mbappe"
}

def apply_aliases(tokens: list) -> list:
    """Replaces tokens with their canonical versions if an alias exists."""
    new_tokens = []
    for t in tokens:
        # Check set aliases
        if t in SET_ALIASES:
            # Note: Aliases can be multiple words, but token set logic handles it
            new_tokens.extend(SET_ALIASES[t].split())
        elif t in PLAYER_ALIASES:
            new_tokens.extend(PLAYER_ALIASES[t].split())
        else:
            new_tokens.append(t)
    return list(set(new_tokens)) # Unique tokens
