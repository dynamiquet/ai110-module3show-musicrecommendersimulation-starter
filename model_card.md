# 🎧 Model Card — VibeFinder 1.0

---

## 1. Model Name

**VibeFinder 1.0**

A content-based music recommender simulation built for classroom exploration. It suggests songs from an 18-song catalog based on a user's stated taste preferences.

---

## 2. Goal / Task

VibeFinder tries to answer: *"Given what you told me about your taste, which songs in this catalog will feel the most right for you right now?"*

It is designed for a single user at a time. It does not learn from listening behavior. You tell it what you want; it finds the closest match using a fixed scoring formula.

**This is for classroom use only.** It is not intended for real users or production deployment.

---

## 3. Data Used

- **Catalog size**: 18 songs in `data/songs.csv`
- **Genres represented**: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, r&b, classical, metal, folk, edm, blues, reggae
- **Moods represented**: happy, chill, intense, relaxed, focused, moody, energetic, romantic, peaceful, angry, nostalgic, euphoric, melancholic
- **Numerical features per song**: energy (0–1), valence (0–1), danceability (0–1), acousticness (0–1), tempo_bpm
- **What is missing**: country, K-pop, Latin, gospel, spoken word, and many other genres. Lyric themes, key/mode, language, and cultural context are completely absent. Each genre has at most 2–3 songs, so the catalog heavily underrepresents most genres.

---

## 4. Algorithm Summary (plain language)

Every song in the catalog is judged against the user's stated preferences using a points system:

1. **Genre match** — If the song's genre is the same as what the user asked for, it earns 3 points. This is the heaviest weight because genre is the single most defining dimension of musical taste.

2. **Mood match** — If the song's emotional context matches (e.g., both are "focused" or "intense"), it earns 2 points.

3. **Energy closeness** — Songs get up to 1.5 points based on how close their energy level is to the user's target. A song with exactly the right energy gets the full 1.5 points; a song far away gets close to 0. The formula rewards closeness, not just high values.

4. **Valence (brightness) closeness** — Same idea as energy but worth up to 1.0 point. This measures emotional positivity: the difference between a dark moody track and a bright cheerful one even within the same genre.

5. **Acoustic bonus** — If the user prefers acoustic music and the song is mostly acoustic (acousticness > 0.6), it earns an extra 0.5 points.

After every song is scored, they are sorted from highest to lowest and the top results are shown. The maximum possible score is 8.0 (all five components fire perfectly).

---

## 5. Observed Behavior / Biases

### Genre dominance creates a filter bubble

The 3-point genre bonus is so large that it can override significant numerical mismatches. In the **adversarial test** (a user who wants high-energy blues at 0.95 energy + melancholic mood), "Bayou Blues" ranked first with a score of 6.65 — even though its actual energy is only 0.44, a difference of 0.51. The genre + mood bonus (5.0 points) compensated for almost all of the energy penalty. In other words, a song can be very different from what the user wants numerically, but still win because its genre and mood label happen to match.

### No partial genre credit — related genres are strangers

"Lofi" and "ambient" are sonically very close — both are low-energy, low-BPM, chill listening experiences. But in this system they score identically to "lofi" vs "metal" for a genre match: both get 0.0 points. A lofi user will never see Spacewalk Thoughts (ambient) near the top, even though it might genuinely fit their vibe. The system treats every genre mismatch as equally wrong.

### The ghost genre problem

A user who asks for a genre not in the catalog (tested with "country") receives zero genre bonuses across the entire catalog. The recommendations fall back entirely on mood, energy, and valence. Coffee Shop Stories (jazz) ranked first — reasonable, but the user asked for country music and got jazz. The system cannot tell the user "I don't have your genre; here's the closest thing." It just silently substitutes.

### "Gym Hero" appears everywhere

"Gym Hero" (pop, intense, energy 0.93) appeared in the top 5 for four out of six profiles tested: Pop/Happy, Rock/Intense, EDM/Euphoric, and the adversarial high-energy profile. It does not match the genre or mood of most of those users, but its high energy earns proximity points broadly. This is a minor filter-bubble effect — one song gravitates toward the top of many lists just because energy 0.93 is rare and rewarded.

### Catalog skew limits diversity

Lofi has 3 songs in the catalog; the lofi user's entire top 3 is completely predictable and dominated by one artist (LoRoom). Users whose preferred genre has few songs will always see a thin, repetitive list. This would be more severe if the genre had only 1 song.

---

## 6. Evaluation

### Profiles tested

| Profile | Top result | Intuition check |
|---|---|---|
| Pop / Happy (energy 0.80) | Sunrise City (7.47) | Correct — triple match |
| Lofi / Focused study | Focus Flow (7.99) | Correct — all 5 bonuses fired |
| Deep Intense Rock | Storm Runner (7.45) | Correct — genre + mood + energy match |
| EDM / Euphoric | Drop Zone (7.50) | Correct — near-perfect match |
| ADVERSARIAL: Blues + melancholic + high energy | Bayou Blues (6.65) | Partially wrong — genre/mood match won despite 0.51 energy gap |
| ADVERSARIAL: Country (not in catalog) | Coffee Shop Stories (4.79) | Reasonable fallback, but not what the user actually wanted |

### Weight-shift experiment

I tested what happens when the genre weight is halved (3.0 → 1.5) and the energy weight is doubled (1.5 → 3.0), using the Pop/Happy profile.

**Original ranking**: Sunrise City → Gym Hero → Rooftop Lights  
**Shifted ranking**: Sunrise City → **Rooftop Lights** → **Gym Hero**

Gym Hero dropped from #2 to #3 because its energy (0.93) is further from the target (0.80) than Rooftop Lights (0.76). When energy matters more, the better numerical match wins. This shows the system is sensitive to weights — a small change in how much you care about energy vs genre meaningfully reorders the results. The original weights produce more genre-loyal recommendations; the shifted weights produce more energy-precise recommendations.

### What surprised me

- The adversarial high-energy + melancholic profile exposed how strong the genre+mood gate is. I expected the energy mismatch to drop Bayou Blues lower, but 5.0 categorical points overwhelmed it.
- The ghost-genre profile gracefully degraded without crashing. Coffee Shop Stories is actually a reasonable relaxed/acoustic pick even without the country genre in the catalog.
- Rooftop Lights climbing past Gym Hero in the weight-shift experiment was the most interesting result. Both are pop-adjacent songs for a pop user, but Rooftop Lights has a tighter energy match and the mood bonus, which the original genre-heavy weighting was hiding.

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
- Classroom simulation for understanding how content-based recommenders work
- Learning tool for seeing how weights and features affect ranking
- A starting point for experiments with scoring logic

**Not intended for:**
- Real music discovery for real users
- Large catalogs (the catalog is 18 songs; behavior at 50,000 songs would be very different)
- Users who expect to be understood from behavior — this system requires explicit preference input every time
- Any commercial application

---

## 8. Ideas for Improvement

1. **Genre proximity / genre families**: Instead of a binary genre match, group related genres (lofi + ambient + jazz → "low-key" family; metal + rock → "heavy" family). A partial match should earn partial credit (e.g., +1.5 instead of +3.0 or 0).

2. **Catalog diversity enforcement**: After scoring, add a re-ranking step that prevents the same artist or genre from occupying more than 2 of the top-5 slots. This would fix the lofi user seeing only LoRoom in the top 3.

3. **Listening history as implicit feedback**: After the user "plays" songs, record skips and replays. Adjust the preference profile automatically — if the user keeps skipping intense songs, lower the energy target without them having to say anything.

4. **Hybrid model**: Add a lightweight collaborative filtering layer. Even with a tiny dataset of 5–10 simulated users, you could recommend based on "users with similar profiles also liked..."

---

## 9. Personal Reflection

**Biggest learning moment**: I expected the scoring to just work — assign points, sort, done. What actually surprised me was how much the *weight ratios* matter. The weight-shift experiment made it clear that a number you pick somewhat arbitrarily (3.0 for genre) encodes a strong assumption about what music taste actually is. Changing one number reshuffled the rankings in a meaningful way.

**Using AI tools in this project**: AI was useful for generating the initial song catalog entries (diversity across genres and moods), suggesting the proximity formula `1 − |diff|` for numerical features, and helping think through what biases might emerge. The key moment where I had to override it was on the genre weight — a naive suggestion was to treat genre and mood as equal (both +2.0). Keeping genre higher (3.0) was a deliberate design choice because genre is a more stable signal of musical identity than mood. I had to reason through the tradeoff rather than accept the first suggestion.

**What surprised me about simple algorithms**: Running just 6 profiles made it obvious that the recommendations "feel" right for most users (rock fan gets rock songs, EDM fan gets EDM). But the adversarial tests showed the cracks: the system has no concept of "I cannot satisfy this user's genre request, so I should say so." It silently does its best and the user may not realize they're getting substitutes. Real Spotify-scale systems handle this by having enough catalog depth that any genre has hundreds of options — the small-catalog fragility is essentially invisible.

**What I would try next**: The most interesting next step would be to simulate a listening history — have a few "users" play songs over 5 sessions, track skips vs replays, and use that history to update the energy/valence targets automatically. That would turn this from a static content filter into something that actually learns. Even a simple "if the user skips 3 songs in a row that have high energy, lower target_energy by 0.1" would make the system feel meaningfully smarter without adding much complexity.
