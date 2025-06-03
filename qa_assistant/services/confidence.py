import re
from typing import Dict, List, Tuple

# Define patterns that indicate different types of failures
ERROR_PATTERNS = {
    "assertion_error": [
        r"AssertionError",
        r"assert.*failed",
        r"expected.*but got",
        r"comparison.*failed",
        r"Failed: .*!=.*"
    ],
    "null_pointer": [
        r"NullPointerException",
        r"null reference",
        r"none.*reference",
        r"undefined.*reference"
    ],
    "timeout": [
        r"timeout",
        r"timed out",
        r"connection.*refused",
        r"request.*timed out",
        r"deadline exceeded"
    ],
    "environmental": [
        r"permission denied",
        r"access.*denied",
        r"unauthorized",
        r"configuration.*missing",
        r"insufficient.*permissions"
    ],
    "data_issues": [
        r"invalid.*format",
        r"data.*inconsistent",
        r"schema.*validation",
        r"missing.*field",
        r"type.*mismatch"
    ]
}

# Weight of each error category for confidence scoring
CATEGORY_WEIGHTS = {
    "assertion_error": 0.9,    # High confidence for assertion errors
    "null_pointer": 0.85,      # High confidence for null pointers
    "timeout": 0.7,           # Medium confidence for timeouts (could be intermittent)
    "environmental": 0.5,     # Lower confidence for environmental issues
    "data_issues": 0.8        # High confidence for data validation issues
}

def get_confidence_score(summary: str) -> float:
    """
    Determine a confidence score (0.0-1.0) for how actionable a failure is.
    
    A higher score means we have higher confidence that this is a real bug
    that needs attention. Lower scores might indicate transient failures or
    environmental issues.
    
    Args:
        summary: The failure summary text from log analysis
        
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    # Normalize text for pattern matching
    text = summary.lower()
    
    # Check for matches against our patterns
    matches: Dict[str, List[str]] = {}
    for category, patterns in ERROR_PATTERNS.items():
        category_matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                category_matches.append(pattern)
        if category_matches:
            matches[category] = category_matches
    
    # If no patterns matched, return a low confidence score
    if not matches:
        return 0.4
    
    # Calculate score based on matched categories and their weights
    total_weight = 0
    for category in matches:
        weight = CATEGORY_WEIGHTS.get(category, 0.5)
        # Increase confidence slightly for multiple matches in same category
        match_bonus = min(0.1, 0.02 * len(matches[category]))
        total_weight += weight + match_bonus
    
    # Average the weights and normalize to 0.4-1.0 range
    base_score = total_weight / len(matches)
    
    # Apply additional heuristics
    
    # Check for "consistently fails" or similar phrases that indicate reproducibility
    if re.search(r"(consistently|always|repeatedly) fail", text, re.IGNORECASE):
        base_score += 0.1
    
    # Check for specific error codes or explicit failure messages
    if re.search(r"(error code|status code|exit code|returned) [45]\d\d", text, re.IGNORECASE):
        base_score += 0.05
    
    # Cap the score at 1.0
    return min(1.0, base_score)

# Additional utility function to get detailed analysis of the failure
def analyze_failure(summary: str) -> Dict[str, any]:
    """
    Provide a detailed analysis of the failure summary.
    
    Args:
        summary: The failure summary text
        
    Returns:
        Dict with analysis results including confidence score and categories
    """
    text = summary.lower()
    matched_categories = []
    
    for category, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if category not in matched_categories:
                    matched_categories.append(category)
                break
    
    confidence = get_confidence_score(summary)
    
    return {
        "confidence_score": confidence,
        "matched_categories": matched_categories,
        "actionability": "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "low",
        "recommendation": "investigate immediately" if confidence > 0.8 else 
                        "schedule for review" if confidence > 0.6 else 
                        "monitor for recurrence"
    }
