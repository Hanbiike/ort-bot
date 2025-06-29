from ..config import MAX_SCORE

def validate_score(score_text: str) -> int:
    if not score_text.isdigit():
        raise ValueError("Score must be a number")
        
    score = int(score_text)
    if not 0 <= score <= MAX_SCORE:
        raise ValueError(f"Score must be between 0 and {MAX_SCORE}")
        
    return score
