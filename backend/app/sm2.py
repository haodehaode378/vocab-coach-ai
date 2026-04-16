from dataclasses import dataclass


@dataclass
class SrsState:
    ease_factor: float
    interval_days: int
    repetitions: int


def apply_sm2(state: SrsState, grade: str) -> SrsState:
    score_map = {"again": 0, "hard": 3, "good": 4, "easy": 5}
    q = score_map[grade]

    ease = state.ease_factor
    interval = state.interval_days
    reps = state.repetitions

    if q < 3:
        reps = 0
        interval = 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = max(1, round(interval * ease))

    ease = max(1.3, ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))

    return SrsState(ease_factor=ease, interval_days=interval, repetitions=reps)
