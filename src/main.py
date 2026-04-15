"""
Command-line runner for the Music Recommender Simulation.

Usage:
    python -m src.main
"""

from typing import Dict, List, Tuple
from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# Experimental scoring — used only for the weight-shift experiment in Phase 4.
# Genre weight halved (3.0 → 1.5); energy weight doubled (1.5 → 3.0).
# This lives in main.py so the core recommender logic stays untouched.
# ---------------------------------------------------------------------------
def _experimental_score(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score with inverted weights: genre=1.5, energy=3.0."""
    score = 0.0
    reasons: List[str] = []

    if song.get("genre") == user_prefs.get("genre"):
        score += 1.5
        reasons.append(f"genre match: {song['genre']} (+1.5)")

    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood match: {song['mood']} (+2.0)")

    if "energy" in user_prefs:
        diff = abs(float(user_prefs["energy"]) - float(song["energy"]))
        pts = round(3.0 * (1.0 - diff), 2)
        score += pts
        reasons.append(f"energy proximity (+{pts:.2f})")

    if "valence" in user_prefs:
        diff = abs(float(user_prefs["valence"]) - float(song.get("valence", 0.65)))
        pts = round(1.0 * (1.0 - diff), 2)
        score += pts
        reasons.append(f"valence proximity (+{pts:.2f})")

    if user_prefs.get("likes_acoustic") and float(song.get("acousticness", 0)) > 0.6:
        score += 0.5
        reasons.append("acoustic match (+0.50)")

    return round(score, 2), reasons


def _run_experiment(songs: List[Dict], user_prefs: Dict) -> List[Tuple[Dict, float, str]]:
    """Score every song with experimental weights and return top-5."""
    scored = []
    for song in songs:
        score, reasons = _experimental_score(user_prefs, song)
        explanation = " | ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:5]


def _print_results(results: List[Tuple[Dict, float, str]]) -> None:
    for rank, (song, score, explanation) in enumerate(results, start=1):
        print(f"  {rank}. {song['title']}  —  {song['artist']}")
        print(f"     Score : {score:.2f}")
        print(f"     Why   : {explanation}")
        print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs.\n")

    # -----------------------------------------------------------------------
    # Regular profiles
    # -----------------------------------------------------------------------
    profiles = [
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
        # --- adversarial profiles -------------------------------------------
        {
            "label":          "ADVERSARIAL: High-energy + melancholic (conflicting)",
            "genre":          "blues",
            "mood":           "melancholic",
            "energy":         0.95,   # blues catalog is low-energy — direct conflict
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

    for profile in profiles:
        label = profile.pop("label")
        print("=" * 64)
        print(f"Profile: {label}")
        print(f"  genre={profile['genre']}  mood={profile['mood']}"
              f"  energy={profile['energy']}  valence={profile['valence']}"
              f"  acoustic={profile['likes_acoustic']}")
        print("-" * 64)
        _print_results(recommend_songs(profile, songs, k=5))
        profile["label"] = label   # restore for the list

    # -----------------------------------------------------------------------
    # Weight-shift experiment (Phase 4, Step 3)
    # Genre weight: 3.0 → 1.5  |  Energy weight: 1.5 → 3.0
    # -----------------------------------------------------------------------
    pop_profile = {
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.80,
        "valence":        0.84,
        "likes_acoustic": False,
    }

    print("=" * 64)
    print("EXPERIMENT: Pop / Happy — original weights (genre=3.0, energy=1.5)")
    print("-" * 64)
    _print_results(recommend_songs(pop_profile, songs, k=5))

    print("=" * 64)
    print("EXPERIMENT: Pop / Happy — shifted weights (genre=1.5, energy=3.0)")
    print("-" * 64)
    _print_results(_run_experiment(songs, pop_profile))

    print("=" * 64)


if __name__ == "__main__":
    main()
