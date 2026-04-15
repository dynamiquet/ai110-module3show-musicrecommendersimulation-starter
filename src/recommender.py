import csv as csv_module
from dataclasses import dataclass
from typing import Dict, List, Tuple


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


@dataclass
class UserProfile:
    """Represents a user's musical taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.65  # default: moderate brightness


class Recommender:
    """Scores and ranks a song catalog against a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects ranked by score for the given user."""
        user_prefs = {
            "genre":          user.favorite_genre,
            "mood":           user.favorite_mood,
            "energy":         user.target_energy,
            "valence":        user.target_valence,
            "likes_acoustic": user.likes_acoustic,
        }

        def _song_to_dict(s: Song) -> Dict:
            return {
                "genre":        s.genre,
                "mood":         s.mood,
                "energy":       s.energy,
                "valence":      s.valence,
                "acousticness": s.acousticness,
            }

        scored = [(s, score_song(user_prefs, _song_to_dict(s))[0]) for s in self.songs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string explaining why this song was recommended."""
        user_prefs = {
            "genre":          user.favorite_genre,
            "mood":           user.favorite_mood,
            "energy":         user.target_energy,
            "valence":        user.target_valence,
            "likes_acoustic": user.likes_acoustic,
        }
        song_dict = {
            "genre":        song.genre,
            "mood":         song.mood,
            "energy":       song.energy,
            "valence":      song.valence,
            "acousticness": song.acousticness,
        }
        _, reasons = score_song(user_prefs, song_dict)
        if not reasons:
            return f"{song.title}: no strong match found"
        return f"{song.title}: " + "; ".join(reasons)


# ---------------------------------------------------------------------------
# Functional API  (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file, converting numeric fields to float/int."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            for field in ("energy", "valence", "danceability", "acousticness"):
                row[field] = float(row[field])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against user preferences; returns (total_score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # --- categorical matches ------------------------------------------------
    if song.get("genre") == user_prefs.get("genre"):
        score += 3.0
        reasons.append(f"genre match: {song['genre']} (+3.0)")

    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood match: {song['mood']} (+2.0)")

    # --- numerical proximity (rewards closeness, not raw magnitude) ----------
    if "energy" in user_prefs:
        diff = abs(float(user_prefs["energy"]) - float(song["energy"]))
        pts = round(1.5 * (1.0 - diff), 2)
        score += pts
        reasons.append(f"energy proximity (+{pts:.2f})")

    if "valence" in user_prefs:
        diff = abs(float(user_prefs["valence"]) - float(song.get("valence", 0.65)))
        pts = round(1.0 * (1.0 - diff), 2)
        score += pts
        reasons.append(f"valence proximity (+{pts:.2f})")

    # --- acoustic texture bonus ---------------------------------------------
    if user_prefs.get("likes_acoustic") and float(song.get("acousticness", 0)) > 0.6:
        score += 0.5
        reasons.append("acoustic match (+0.50)")

    return round(score, 2), reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort descending, and return the top-k as (song, score, explanation)."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = " | ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
