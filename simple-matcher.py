from collections import defaultdict
import math

# --------------------  tweakable knobs  --------------------
W_INTERESTS = 0.60   # weight for shared interests
W_AGE_GAP   = 0.25   # penalty for getting further from ideal age
W_DISTANCE  = 0.15   # penalty for physical distance
MAX_KM      = 50     # hard radius for suggestions
TOP_N       = 5      # how many matches to return per user
# -----------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    "Great-circle distance between two points on Earth (km)."
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = φ2 - φ1
    Δλ = math.radians(lon2 - lon1)
    a = (math.sin(Δφ / 2) ** 2 +
         math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

class User:
    def __init__(
        self,
        uid: int,
        name: str,
        age: int,
        gender: str,
        seeking: set[str],
        min_age: int,
        max_age: int,
        lat: float,
        lon: float,
        interests: set[str],
    ):
        self.uid = uid
        self.name = name
        self.age = age
        self.gender = gender
        self.seeking = seeking
        self.min_age = min_age
        self.max_age = max_age
        self.lat = lat
        self.lon = lon
        self.interests = interests

    def __repr__(self) -> str:  # debug helper
        return f"User({self.uid}, {self.name})"

def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)

def age_penalty(a: int, b: int) -> float:
    "0 when ages identical, 1 when 25+ years apart."
    return min(abs(a - b) / 25.0, 1.0)

def distance_penalty(km: float) -> float:
    "0 when distance is zero, 1 when at hard radius."
    return min(km / MAX_KM, 1.0)

def compatibility(u: User, v: User) -> float:
    """Return a score in [0, 1]."""
    # Hard filters
    if u.gender not in v.seeking or v.gender not in u.seeking:
        return 0.0
    if not (u.min_age <= v.age <= u.max_age and v.min_age <= u.age <= v.max_age):
        return 0.0
    km = haversine_km(u.lat, u.lon, v.lat, v.lon)
    if km > MAX_KM:
        return 0.0

    # Soft score
    s_interests = jaccard(u.interests, v.interests)
    s_age = 1.0 - age_penalty(u.age, v.age)
    s_dist = 1.0 - distance_penalty(km)

    return (
        W_INTERESTS * s_interests +
        W_AGE_GAP   * s_age +
        W_DISTANCE  * s_dist
    )

def make_matches(users: list[User], top_n: int = TOP_N) -> dict[int, list[tuple[int, float]]]:
    """Return {uid: [(candidate_uid, score), ...]} sorted by score."""
    scores = defaultdict(list)
    for i, u in enumerate(users):
        for j, v in enumerate(users):
            if i == j:
                continue
            s = compatibility(u, v)
            if s > 0:
                scores[u.uid].append((v.uid, round(s, 4)))

        scores[u.uid].sort(key=lambda t: t[1], reverse=True)
        scores[u.uid] = scores[u.uid][:top_n]

    return scores

# ---------------------- quick demo -------------------------
if __name__ == "__main__":
    demo_users = [
        User(1, "Alice", 29, "F", {"M"}, 25, 35, 42.36, -71.06, {"hiking", "coffee", "board games"}),
        User(2, "Bob",   31, "M", {"F"}, 24, 34, 42.36, -71.07, {"hiking", "baking", "tennis"}),
        User(3, "Cara",  28, "F", {"M"}, 26, 38, 40.71, -74.00, {"coffee", "running", "music"}),
        User(4, "Dan",   35, "M", {"F"}, 27, 35, 42.36, -71.05, {"music", "board games", "travel"}),
        User(5, "Eve",   30, "F", {"M"}, 26, 36, 42.36, -71.10, {"tennis", "baking", "travel"}),
    ]

    print("Top matches:")
    for uid, matches in make_matches(demo_users).items():
        names = {u.uid: u.name for u in demo_users}
        readable = [(names[mid], score) for mid, score in matches]
        print(f"{names[uid]} → {readable}")
