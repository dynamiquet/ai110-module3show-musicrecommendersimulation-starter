"""
Music Recommender — core logic.

Public API:
  Data:        Song, UserProfile
  Strategy:    ScoringWeights, DEFAULT, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED
  OOP:         Recommender (recommend, recommend_diverse, explain_recommendation)
  Functional:  load_songs, score_song, recommend_songs, apply_diversity_filter
"""

import csv as csv_module
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """Represents a song and its audio attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Challenge 1 — advanced features (default to neutral so old Song() calls still work)
    popularity: int = 50
    release_decade: int = 2020
    speechiness: float = 0.05
    instrumentalness: float = 0.50
    liveness: float = 0.10


@dataclass
class UserProfile:
    """Represents a user's musical taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.65
    # Challenge 1 — advanced preferences (all opt-in; None = ignored by scorer)
    target_popularity: Optional[int] = None
    preferred_decade: Optional[int] = None
    target_speechiness: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    likes_live: bool = False


# ---------------------------------------------------------------------------
# Challenge 2 — Scoring Strategy (Strategy Pattern)
# ---------------------------------------------------------------------------

@dataclass
class ScoringWeights:
    """
    Controls how much each feature contributes to the final score.
    Swap preset instances to change ranking strategy without touching any
    other code — that is the Strategy pattern.
    """
    # Categorical gates
    genre: float = 3.0
    mood: float = 2.0
    # Numerical proximity  (score = weight × (1 − |diff|))
    energy: float = 1.5
    valence: float = 1.0
    # Bonuses
    acousticness_bonus: float = 0.50
    liveness_bonus: float = 0.30
    # Challenge 1 new feature weights
    popularity: float = 0.50
    decade: float = 1.00
    speechiness_weight: float = 0.50
    instrumentalness: float = 0.75


# Preset modes — import and pass to score_song / recommend_songs / Recommender
DEFAULT = ScoringWeights()  # original Phase 3 weights

GENRE_FIRST = ScoringWeights(          # Category loyalty dominates
    genre=4.0,   mood=2.0,   energy=0.75,  valence=0.50,
    acousticness_bonus=0.50, liveness_bonus=0.20,
    popularity=0.25, decade=0.50, speechiness_weight=0.25, instrumentalness=0.40,
)

MOOD_FIRST = ScoringWeights(           # Emotional context dominates
    genre=1.5,   mood=4.0,   energy=1.50,  valence=1.50,
    acousticness_bonus=0.50, liveness_bonus=0.20,
    popularity=0.25, decade=0.50, speechiness_weight=0.25, instrumentalness=0.50,
)

ENERGY_FOCUSED = ScoringWeights(       # Sonic energy and feel dominate
    genre=1.0,   mood=1.0,   energy=4.00,  valence=2.00,
    acousticness_bonus=0.75, liveness_bonus=0.30,
    popularity=0.25, decade=0.50, speechiness_weight=0.25, instrumentalness=0.75,
)


# ---------------------------------------------------------------------------
# OOP interface  (required by tests)
# ---------------------------------------------------------------------------

class Recommender:
    """Scores and ranks a song catalog against a UserProfile."""

    def __init__(self, songs: List[Song], weights: ScoringWeights = None):
        self.songs = songs
        self.weights = weights or DEFAULT

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects ranked by score for the given user."""
        user_prefs = _profile_to_dict(user)
        scored = [
            (s, score_song(user_prefs, _song_to_dict(s), self.weights)[0])
            for s in self.songs
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored[:k]]

    def recommend_diverse(
        self,
        user: UserProfile,
        k: int = 5,
        max_per_genre: int = 2,
        max_per_artist: int = 1,
    ) -> List[Song]:
        """Return top-k songs with artist and genre diversity enforced."""
        user_prefs = _profile_to_dict(user)
        scored = sorted(
            self.songs,
            key=lambda s: score_song(user_prefs, _song_to_dict(s), self.weights)[0],
            reverse=True,
        )

        accepted: List[Song] = []
        genre_count: Dict[str, int] = {}
        artist_count: Dict[str, int] = {}

        for s in scored:
            if genre_count.get(s.genre, 0) >= max_per_genre:
                continue
            if artist_count.get(s.artist, 0) >= max_per_artist:
                continue
            accepted.append(s)
            genre_count[s.genre] = genre_count.get(s.genre, 0) + 1
            artist_count[s.artist] = artist_count.get(s.artist, 0) + 1
            if len(accepted) == k:
                break

        # Fallback: if catalog too small to meet diversity constraints, return top-k
        return accepted if len(accepted) >= k else scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string explaining why this song was recommended."""
        user_prefs = _profile_to_dict(user)
        _, reasons = score_song(user_prefs, _song_to_dict(song), self.weights)
        if not reasons:
            return f"{song.title}: no strong match found"
        return f"{song.title}: " + "; ".join(reasons)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _profile_to_dict(user: UserProfile) -> Dict:
    """Convert a UserProfile to a flat dict for use by score_song."""
    d: Dict = {
        "genre":          user.favorite_genre,
        "mood":           user.favorite_mood,
        "energy":         user.target_energy,
        "valence":        user.target_valence,
        "likes_acoustic": user.likes_acoustic,
    }
    if user.target_popularity is not None:
        d["target_popularity"] = user.target_popularity
    if user.preferred_decade is not None:
        d["preferred_decade"] = user.preferred_decade
    if user.target_speechiness is not None:
        d["target_speechiness"] = user.target_speechiness
    if user.target_instrumentalness is not None:
        d["target_instrumentalness"] = user.target_instrumentalness
    if user.likes_live:
        d["likes_live"] = True
    return d


def _song_to_dict(s: Song) -> Dict:
    """Convert a Song to a flat dict for use by score_song."""
    return {
        "genre":            s.genre,
        "mood":             s.mood,
        "energy":           s.energy,
        "valence":          s.valence,
        "acousticness":     s.acousticness,
        "popularity":       s.popularity,
        "release_decade":   s.release_decade,
        "speechiness":      s.speechiness,
        "instrumentalness": s.instrumentalness,
        "liveness":         s.liveness,
    }


# ---------------------------------------------------------------------------
# Functional API  (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file, converting numeric fields to the right types."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["popularity"] = int(row["popularity"])
            row["release_decade"] = int(row["release_decade"])
            for field in (
                "energy", "valence", "danceability", "acousticness",
                "speechiness", "instrumentalness", "liveness",
            ):
                row[field] = float(row[field])
            songs.append(row)
    return songs


def score_song(
    user_prefs: Dict,
    song: Dict,
    weights: ScoringWeights = None,
) -> Tuple[float, List[str]]:
    """
    Score one song against user preferences using the given weight strategy.
    Returns (total_score, reasons) where reasons explains each contribution.
    If weights is None, DEFAULT weights are used.
    """
    w = weights or DEFAULT
    score = 0.0
    reasons: List[str] = []

    # --- categorical matches ------------------------------------------------
    if song.get("genre") == user_prefs.get("genre"):
        score += w.genre
        reasons.append(f"genre match: {song['genre']} (+{w.genre:.1f})")

    if song.get("mood") == user_prefs.get("mood"):
        score += w.mood
        reasons.append(f"mood match: {song['mood']} (+{w.mood:.1f})")

    # --- core numerical proximity -------------------------------------------
    if "energy" in user_prefs:
        diff = abs(float(user_prefs["energy"]) - float(song["energy"]))
        pts = round(w.energy * (1.0 - diff), 2)
        score += pts
        reasons.append(f"energy proximity (+{pts:.2f})")

    if "valence" in user_prefs:
        diff = abs(float(user_prefs["valence"]) - float(song.get("valence", 0.65)))
        pts = round(w.valence * (1.0 - diff), 2)
        score += pts
        reasons.append(f"valence proximity (+{pts:.2f})")

    # --- acoustic texture bonus ---------------------------------------------
    if user_prefs.get("likes_acoustic") and float(song.get("acousticness", 0)) > 0.6:
        score += w.acousticness_bonus
        reasons.append(f"acoustic match (+{w.acousticness_bonus:.2f})")

    # --- Challenge 1: advanced feature scoring ------------------------------

    # Popularity proximity — rewarded by closeness to target, not raw value
    if "target_popularity" in user_prefs and "popularity" in song:
        diff = abs(float(user_prefs["target_popularity"]) - float(song["popularity"])) / 100.0
        pts = round(w.popularity * (1.0 - diff), 2)
        score += pts
        reasons.append(f"popularity proximity (+{pts:.2f})")

    # Release decade proximity — each decade = 1/6 of the scoring range
    if "preferred_decade" in user_prefs and "release_decade" in song:
        decade_diff = abs(int(user_prefs["preferred_decade"]) - int(song["release_decade"])) / 60.0
        pts = round(w.decade * (1.0 - decade_diff), 2)
        score += pts
        reasons.append(f"decade proximity (+{pts:.2f})")

    # Speechiness proximity — how much vocals/rap the user wants
    if "target_speechiness" in user_prefs and "speechiness" in song:
        diff = abs(float(user_prefs["target_speechiness"]) - float(song["speechiness"]))
        pts = round(w.speechiness_weight * (1.0 - diff), 2)
        score += pts
        reasons.append(f"speechiness proximity (+{pts:.2f})")

    # Instrumentalness proximity — pure music vs lyrics preference
    if "target_instrumentalness" in user_prefs and "instrumentalness" in song:
        diff = abs(float(user_prefs["target_instrumentalness"]) - float(song["instrumentalness"]))
        pts = round(w.instrumentalness * (1.0 - diff), 2)
        score += pts
        reasons.append(f"instrumentalness proximity (+{pts:.2f})")

    # Liveness bonus — rewards live-feeling recordings for users who want them
    if user_prefs.get("likes_live") and float(song.get("liveness", 0)) > 0.2:
        score += w.liveness_bonus
        reasons.append(f"live feel match (+{w.liveness_bonus:.2f})")

    return round(score, 2), reasons


# ---------------------------------------------------------------------------
# Challenge 3 — Diversity filter
# ---------------------------------------------------------------------------

def apply_diversity_filter(
    scored: List[Tuple[Dict, float, str]],
    k: int,
    max_per_genre: int = 2,
    max_per_artist: int = 1,
) -> List[Tuple[Dict, float, str]]:
    """
    Walk a score-sorted list and accept songs only while artist and genre
    quotas have not been filled.  Falls back to plain top-k if the catalog
    is too small to satisfy the constraints.
    """
    accepted: List[Tuple[Dict, float, str]] = []
    genre_count: Dict[str, int] = {}
    artist_count: Dict[str, int] = {}

    for item in scored:
        song = item[0]
        genre = song.get("genre", "")
        artist = song.get("artist", "")

        if genre_count.get(genre, 0) >= max_per_genre:
            continue
        if artist_count.get(artist, 0) >= max_per_artist:
            continue

        accepted.append(item)
        genre_count[genre] = genre_count.get(genre, 0) + 1
        artist_count[artist] = artist_count.get(artist, 0) + 1

        if len(accepted) == k:
            break

    return accepted if len(accepted) >= k else scored[:k]


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: ScoringWeights = None,
    diverse: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song, sort descending, and return top-k as (song, score, explanation).
    Pass weights= to change strategy; pass diverse=True to enforce variety.
    """
    scored = []
    for song in songs:
        sc, reasons = score_song(user_prefs, song, weights)
        explanation = " | ".join(reasons) if reasons else "no matching features"
        scored.append((song, sc, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)

    if diverse:
        return apply_diversity_filter(scored, k)
    return scored[:k]
