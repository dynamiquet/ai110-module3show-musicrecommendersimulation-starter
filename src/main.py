"""
Command-line runner for the Music Recommender Simulation.

Usage:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs.\n")

    # -----------------------------------------------------------------------
    # Define user taste profiles to demo
    # -----------------------------------------------------------------------
    profiles = [
        {
            "label":         "Pop / Happy (high energy)",
            "genre":         "pop",
            "mood":          "happy",
            "energy":        0.80,
            "valence":       0.84,
            "likes_acoustic": False,
        },
        {
            "label":         "Late-night study session (lofi / focused)",
            "genre":         "lofi",
            "mood":          "focused",
            "energy":        0.40,
            "valence":       0.58,
            "likes_acoustic": True,
        },
    ]

    for profile in profiles:
        label = profile.pop("label")
        print("=" * 60)
        print(f"Profile: {label}")
        print(f"  genre={profile['genre']}  mood={profile['mood']}"
              f"  energy={profile['energy']}  valence={profile['valence']}"
              f"  acoustic={profile['likes_acoustic']}")
        print("-" * 60)

        recommendations = recommend_songs(profile, songs, k=5)

        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"  {rank}. {song['title']}  —  {song['artist']}")
            print(f"     Score : {score:.2f}")
            print(f"     Why   : {explanation}")
            print()

        # restore label so the list stays intact for re-runs
        profile["label"] = label

    print("=" * 60)


if __name__ == "__main__":
    main()
