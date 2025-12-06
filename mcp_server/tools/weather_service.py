from datetime import datetime
from typing import Dict, Optional, List, Tuple
import re
import json
import os
from difflib import SequenceMatcher


# Load locations data
LOCATIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'locations.json')
_locations_cache = None


def load_locations() -> Dict:
    """Load and cache locations data."""
    global _locations_cache
    if _locations_cache is None:
        with open(LOCATIONS_FILE, 'r') as f:
            _locations_cache = json.load(f)
    return _locations_cache


def get_season(month: int, hemisphere: str = "northern") -> str:
    """Get season based on month and hemisphere."""
    if hemisphere == "southern":
        # Southern hemisphere has reversed seasons
        if month in [12, 1, 2]:
            return "summer"
        elif month in [3, 4, 5]:
            return "fall"
        elif month in [6, 7, 8]:
            return "winter"
        else:
            return "spring"
    else:
        # Northern hemisphere
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"


def fuzzy_match_location(query: str) -> Tuple[Optional[Dict], float]:
    """
    Find the best matching location using fuzzy matching.
    Returns (location_dict, confidence_score) or (None, 0) if no match.
    """
    locations = load_locations()
    query_lower = query.lower().strip()
    
    best_match = None
    best_score = 0.0
    
    for loc in locations["locations"]:
        # Check exact alias match first (high confidence)
        for alias in loc.get("aliases", []):
            if alias.lower() == query_lower:
                return (loc, 1.0)
        
        # Check if query contains or is contained in aliases
        for alias in loc.get("aliases", []):
            alias_lower = alias.lower()
            if alias_lower in query_lower or query_lower in alias_lower:
                score = SequenceMatcher(None, query_lower, alias_lower).ratio()
                if score > best_score:
                    best_score = max(score, 0.85)  # Boost partial matches
                    best_match = loc
        
        # Check location name
        name_lower = loc["name"].lower()
        if query_lower in name_lower or name_lower in query_lower:
            score = SequenceMatcher(None, query_lower, name_lower).ratio()
            if score > best_score:
                best_score = max(score, 0.8)
                best_match = loc
        
        # Fuzzy match against name
        score = SequenceMatcher(None, query_lower, name_lower).ratio()
        if score > best_score and score > 0.6:
            best_score = score
            best_match = loc
        
        # Fuzzy match against aliases
        for alias in loc.get("aliases", []):
            score = SequenceMatcher(None, query_lower, alias.lower()).ratio()
            if score > best_score and score > 0.6:
                best_score = score
                best_match = loc
    
    # Only return match if confidence is above threshold
    if best_score >= 0.6:
        return (best_match, best_score)
    
    return (None, 0.0)


def get_alternatives_for_region(region: str, exclude_id: str = None) -> List[Dict]:
    """Get alternative locations from the same or similar region."""
    locations = load_locations()
    alternatives = []
    
    for loc in locations["locations"]:
        if loc.get("id") != exclude_id and loc.get("region") == region:
            alternatives.append({
                "id": loc["id"],
                "name": loc["name"],
                "country": loc.get("country", ""),
                "activities": loc.get("activities", {})
            })
    
    return alternatives[:5]  # Return max 5 alternatives


def detect_likely_region(query: str) -> Optional[str]:
    """Try to detect the likely region from a location query."""
    query_lower = query.lower()
    
    region_keywords = {
        "North America": ["usa", "united states", "america", "canada", "canadian", "alaska", "california", "colorado", "utah", "arizona", "montana", "wyoming"],
        "South America": ["south america", "brazil", "argentina", "chile", "peru", "bolivia", "patagonia", "amazon", "andes"],
        "Central America": ["central america", "costa rica", "panama", "belize", "guatemala", "mexico"],
        "Europe": ["europe", "european", "switzerland", "swiss", "france", "french", "italy", "italian", "spain", "spanish", "germany", "german", "uk", "scotland", "england", "norway", "norwegian", "sweden", "iceland", "alps"],
        "Africa": ["africa", "african", "kenya", "tanzania", "south africa", "morocco", "egypt", "kilimanjaro", "sahara", "safari"],
        "Asia": ["asia", "asian", "japan", "japanese", "nepal", "himalaya", "china", "chinese", "india", "indian", "thailand", "vietnam", "indonesia", "bali", "singapore"],
        "Oceania": ["australia", "australian", "new zealand", "nz", "kiwi", "fiji", "pacific", "outback", "queensland"],
        "Middle East": ["middle east", "jordan", "israel", "dubai", "uae", "emirates", "saudi", "oman", "qatar"]
    }
    
    for region, keywords in region_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                return region
    
    return None


def parse_month_from_dates(dates: str) -> int:
    """
    Extract month number from dates string.
    Handles formats like:
    - "2024-01-15"
    - "January 15-20, 2024"
    - "Jan 15"
    - "this weekend" (defaults to current month)
    """
    # Try ISO format first
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', dates)
    if iso_match:
        return int(iso_match.group(2))
    
    # Try month name
    month_names = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12
    }
    
    dates_lower = dates.lower()
    for month_name, month_num in month_names.items():
        if month_name in dates_lower:
            return month_num
    
    # Default to current month if can't parse
    return datetime.now().month


def celsius_to_fahrenheit(c: float) -> int:
    """Convert Celsius to Fahrenheit."""
    return int((c * 9/5) + 32)


def generate_conditions_from_patterns(location: Dict, season: str) -> Dict:
    """Generate weather conditions from location's weather patterns."""
    patterns = location.get("weather_patterns", {}).get(season, {})
    
    if not patterns:
        # Default patterns
        patterns = {
            "temp_range": [10, 25],
            "conditions": ["variable"],
            "precipitation_chance": 0.3
        }
    
    temp_range = patterns.get("temp_range", [10, 25])
    conditions = patterns.get("conditions", ["variable"])
    precip_chance = patterns.get("precipitation_chance", 0.3)
    
    # Convert temps to Fahrenheit
    min_temp_f = celsius_to_fahrenheit(temp_range[0])
    max_temp_f = celsius_to_fahrenheit(temp_range[1])
    
    # Generate weather description
    weather_desc = conditions[0] if conditions else "variable"
    
    # Generate road alerts based on conditions
    road_alert = "none"
    if "snow" in conditions:
        road_alert = "snow_possible"
    elif "extreme heat" in conditions:
        road_alert = "heat_advisory"
    elif "monsoon" in conditions or "rain" in conditions:
        road_alert = "wet_conditions"
    elif "wind" in conditions or "windy" in conditions:
        road_alert = "high_winds"
    
    # Generate recommendations based on conditions and activities
    recommendations = []
    season_activities = location.get("activities", {}).get(season, [])
    
    if "snow" in conditions or "cold" in conditions:
        recommendations.append("Pack cold-weather gear and layers")
    if "rain" in conditions or precip_chance > 0.4:
        recommendations.append("Waterproof gear essential")
    if "hot" in conditions or "extreme heat" in conditions:
        recommendations.append("Carry extra water and sun protection")
        recommendations.append("Plan activities for early morning or evening")
    if "wind" in conditions or "windy" in conditions:
        recommendations.append("Secure tent and gear for high winds")
    
    if season_activities:
        recommendations.append(f"Popular activities: {', '.join(season_activities[:3])}")
    
    if not recommendations:
        recommendations.append("Check local conditions before departure")
    
    return {
        "weather": weather_desc,
        "min_temp_f": min_temp_f,
        "max_temp_f": max_temp_f,
        "road_alert": road_alert,
        "precipitation_chance": precip_chance,
        "recommendations": recommendations
    }


def get_trip_conditions(location: str, dates: str) -> Dict:
    """
    Get trip conditions for a location.
    Returns weather, coverage status, and alternatives if not covered.
    """
    month = parse_month_from_dates(dates)
    
    # Try to find matching location
    matched_location, confidence = fuzzy_match_location(location)
    
    if matched_location and confidence >= 0.6:
        # Location is covered!
        # Determine hemisphere for season calculation
        lat = matched_location.get("coordinates", {}).get("lat", 40)
        hemisphere = "southern" if lat < 0 else "northern"
        season = get_season(month, hemisphere)
        
        conditions = generate_conditions_from_patterns(matched_location, season)
        
        return {
            "covered": True,
            "location": {
                "id": matched_location["id"],
                "name": matched_location["name"],
                "region": matched_location["region"],
                "country": matched_location.get("country", ""),
                "terrain": matched_location.get("terrain", "")
            },
            "confidence": confidence,
            "season": season,
            "activities": matched_location.get("activities", {}).get(season, []),
            "year_round_activities": matched_location.get("activities", {}).get("year_round", []),
            **conditions
        }
    else:
        # Location not covered - provide helpful alternatives
        likely_region = detect_likely_region(location)
        
        alternatives = []
        if likely_region:
            alternatives = get_alternatives_for_region(likely_region)
        
        # If no region-specific alternatives, provide global popular options
        if not alternatives:
            locations = load_locations()
            popular = ["yosemite", "banff", "swiss-alps", "nz-south-island", "costa-rica"]
            for loc in locations["locations"]:
                if loc["id"] in popular:
                    alternatives.append({
                        "id": loc["id"],
                        "name": loc["name"],
                        "country": loc.get("country", ""),
                        "activities": loc.get("activities", {})
                    })
        
        return {
            "covered": False,
            "queried_location": location,
            "likely_region": likely_region,
            "message": f"Wayfinder doesn't have detailed coverage for '{location}' yet, but we're constantly expanding!",
            "alternatives": alternatives,
            "suggestion": "Would you like me to help plan for one of these covered destinations instead? Or I can provide general guidance based on typical conditions."
        }


def get_all_covered_locations() -> List[Dict]:
    """Return a summary of all covered locations."""
    locations = load_locations()
    return [
        {
            "id": loc["id"],
            "name": loc["name"],
            "region": loc["region"],
            "country": loc.get("country", ""),
            "activities": list(set(
                loc.get("activities", {}).get("winter", []) +
                loc.get("activities", {}).get("summer", []) +
                loc.get("activities", {}).get("year_round", [])
            ))
        }
        for loc in locations["locations"]
    ]


def get_locations_by_activity(activity: str) -> List[Dict]:
    """Find locations that support a specific activity."""
    locations = load_locations()
    activity_lower = activity.lower()
    matching = []
    
    for loc in locations["locations"]:
        all_activities = (
            loc.get("activities", {}).get("winter", []) +
            loc.get("activities", {}).get("summer", []) +
            loc.get("activities", {}).get("year_round", [])
        )
        
        for act in all_activities:
            if activity_lower in act.lower():
                matching.append({
                    "id": loc["id"],
                    "name": loc["name"],
                    "region": loc["region"],
                    "country": loc.get("country", "")
                })
                break
    
    return matching
