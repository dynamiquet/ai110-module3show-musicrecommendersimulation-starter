"""
Command-line runner for the Music Recommender Simulation.

Usage:
    python -m src.main
"""

from typing import Dict, List, Tuple
from src.recommender import (
    load_songs,
    recommend_songs,
    DEFAULT,
    GENRE_FIRST,
    MOOD_FIRST,
    ENERGY_FOCUSED,
    ScoringWeights,
)


# ---------------------------------------------------------------------------
# Challenge 4 — ASCII table renderer
# ---------------------------------------------------------------------------

_W_SONG  = 34   # max width for "Title — Artist" column
_W_SCORE =  5   # score column (e.g. " 7.47")
_W_WHY   = 42   # reason string column (truncated with ".." if needed)
_SEP = f"+----+{'-'*(_W_SONG+2)}+{'-'*(_W_SCORE+2)}+{'-'*(_W_WHY+2)}+"


def _trunc(s: str, width: int) -> str:
    """Truncate string to width, appending '..' if cut."""
    return s if len(s) <= width else s[:width - 2] + ".."


def _print_table(
    results: List[Tuple[Dict, float, str]],
    label: str,
    mode_name: str = "DEFAULT",
    diverse: bool = False,
) -> None:
    """Render a scored recommendation list as a formatted ASCII table."""
    tag = "  ★ DIVERSE" if diverse else ""
    title = f"  {label}  [{mode_name}]{tag}"
    inner_w = len(_SEP) - 4      # total inner width for the title row
    print(_SEP)
    print(f"| {title:<{inner_w}} |")
    print(_SEP)
    print(f"| {'#':>2} | {' Song — Artist':<{_W_SONG}} | {'Score':>{_W_SCORE}} | {'Why':<{_W_WHY}} |")
    print(_SEP)
    for rank, (song, score, explanation) in enumerate(results, start=1):
        song_str = _trunc(f"{song['title']} — {song['artist']}", _W_SONG)
        why_str  = _trunc(explanation, _W_WHY)
        print(f"| {rank:>2} | {song_str:<{_W_SONG}} | {score:>{_W_SCORE}.2f} | {why_str:<{_W_WHY}} |")
    print(_SEP)
    print()


# ---------------------------------------------------------------------------
# Profile definitions
# ---------------------------------------------------------------------------

# --- standard profiles (Phases 3 & 4) --------------------------------------
STANDARD_PROFILES = [
    {
        "label":          "Pop / Happy (high energy)",
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.80,
        "valence":        0.84,
        "likes_acoustic": False,
    },
    {
        "label":          "Late-night study session (lofi / focused)",
        "genre":          "lofi",
        "mood":           "focused",
        "energy":         0.40,
        "valence":        0.58,
        "likes_acoustic": True,
    },
    {
        "label":          "Deep Intense Rock",
        "genre":          "rock",
        "mood":           "intense",
        "energy":         0.90,
        "valence":        0.45,
        "likes_acoustic": False,
    },
    {
        "label":          "EDM / Euphoric workout",
        "genre":          "edm",
        "mood":           "euphoric",
        "energy":         0.95,
        "valence":        0.85,
        "likes_acoustic": False,
    },
    {
        "label":          "ADVERSARIAL: High-energy + melancholic (conflicting)",
        "genre":          "blues",
        "mood":           "melancholic",
        "energy":         0.95,
        "valence":        0.25,
        "likes_acoustic": False,
    },
    {
        "label":          "ADVERSARIAL: Ghost genre (country not in catalog)",
        "genre":          "country",
        "mood":           "relaxed",
        "energy":         0.50,
        "valence":        0.70,
        "likes_acoustic": True,
    },
]

# --- Challenge 1: profiles that use advanced features ----------------------
ADVANCED_PROFILES = [
    {
        "label":                   "Discover obscure 2000s instrumentals",
        "genre":                   "classical",
        "mood":                    "peaceful",
        "energy":                  0.25,
        "valence":                 0.70,
        "likes_acoustic":          True,
        "target_popularity":       30,    # prefer niche / low-profile songs
        "preferred_decade":        2000,
        "target_speechiness":      0.03,  # minimal vocals
        "target_instrumentalness": 0.95,  # as instrumental as possible
        "likes_live":              False,
    },
    {
        "label":                   "Live-feel blues aficionado (00s, obscure)",
        "genre":                   "blues",
        "mood":                    "melancholic",
        "energy":                  0.45,
        "valence":                 0.35,
        "likes_acoustic":          True,
        "target_popularity":       28,
        "preferred_decade":        2000,
        "target_speechiness":      0.06,
        "target_instrumentalness": 0.35,
        "likes_live":              True,   # liveness bonus active
    },
]


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded {len(songs)} songs from data/songs.csv.\n")

    # =======================================================================
    # Section 1 — Standard profiles (DEFAULT weights, table format)
    # =======================================================================
    print("=" * (len(_SEP)))
    print("  SECTION 1 — Standard profiles  [DEFAULT weights]")
    print("=" * (len(_SEP)))
    print()

    for profile in STANDARD_PROFILES:
        label = profile.pop("label")
        results = recommend_songs(profile, songs, k=5)
        _print_table(results, label)
        profile["label"] = label  # restore

    # =======================================================================
    # Section 2 — Scoring mode comparison (Challenge 2)
    # Run Pop/Happy through all four strategy presets
    # =======================================================================
    print("=" * (len(_SEP)))
    print("  SECTION 2 — Scoring mode comparison  (Pop / Happy profile)")
    print("=" * (len(_SEP)))
    print()

    pop_profile = {
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.80,
        "valence":        0.84,
        "likes_acoustic": False,
    }

    modes: List[Tuple[str, ScoringWeights]] = [
        ("DEFAULT",       DEFAULT),
        ("GENRE_FIRST",   GENRE_FIRST),
        ("MOOD_FIRST",    MOOD_FIRST),
        ("ENERGY_FOCUSED", ENERGY_FOCUSED),
    ]

    for mode_name, weights in modes:
        results = recommend_songs(pop_profile, songs, k=5, weights=weights)
        _print_table(results, "Pop / Happy", mode_name)

    print("  Key insight: MOOD_FIRST and ENERGY_FOCUSED both promote Rooftop Lights")
    print("  to #2 because it has the mood match AND a tight energy fit (0.76 vs 0.80).")
    print("  GENRE_FIRST keeps Gym Hero at #2 since genre weight overwhelms the energy gap.\n")

    # =======================================================================
    # Section 3 — Diversity filter (Challenge 3)
    # Shows the lofi profile before and after diversity enforcement
    # =======================================================================
    print("=" * (len(_SEP)))
    print("  SECTION 3 — Diversity filter demo  (Lofi / Focused profile)")
    print("=" * (len(_SEP)))
    print()

    lofi_profile = {
        "genre":          "lofi",
        "mood":           "focused",
        "energy":         0.40,
        "valence":        0.58,
        "likes_acoustic": True,
    }

    # Without diversity — LoRoom appears twice, lofi dominates top-3
    plain = recommend_songs(lofi_profile, songs, k=5)
    _print_table(plain, "Lofi / Focused", "DEFAULT  (no diversity)")

    # With diversity — max 2 songs per genre, max 1 per artist
    diverse = recommend_songs(lofi_profile, songs, k=5, diverse=True)
    _print_table(diverse, "Lofi / Focused", "DEFAULT", diverse=True)

    print("  Without diversity: LoRoom occupies slots #1 and #2; user gets zero variety.")
    print("  With diversity (max 1 artist, max 2 genre): LoRoom capped at 1 slot, Coffee")
    print("  Shop Stories and Porch Song enter the list from different genres.\n")

    # =======================================================================
    # Section 4 — Advanced feature scoring (Challenge 1)
    # Profiles that use popularity, decade, instrumentalness, speechiness, liveness
    # =======================================================================
    print("=" * (len(_SEP)))
    print("  SECTION 4 — Advanced feature scoring  (Challenge 1 new attributes)")
    print("=" * (len(_SEP)))
    print()
    print("  New scoring fields active: popularity · decade · speechiness")
    print(f"  · instrumentalness · liveness bonus\n")

    for profile in ADVANCED_PROFILES:
        label = profile.pop("label")
        results = recommend_songs(profile, songs, k=5)
        _print_table(results, label, "DEFAULT+advanced")
        profile["label"] = label

    print("  Morning Strings dominates the 'obscure 2000s instrumental' search because")
    print("  every single new feature aligns: popularity~33 (target 30), decade=2000,")
    print("  speechiness=0.03, instrumentalness=0.99 — plus genre+mood+energy match.\n")

    print("=" * (len(_SEP)))


if __name__ == "__main__":
    main()
