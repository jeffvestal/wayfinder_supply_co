from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()


@router.get("/users/personas")
async def get_user_personas():
    """
    Get all user personas with their browsing history and session stories.
    Falls back to default personas if file doesn't exist.
    """
    # Try multiple possible paths
    possible_paths = [
        Path("generated_products/user_personas.json"),
        Path("../generated_products/user_personas.json"),
        Path("/tmp/user_personas.json"),
    ]
    
    personas_file = None
    for path in possible_paths:
        if path.exists():
            personas_file = path
            break
    
    if personas_file:
        try:
            with open(personas_file, 'r') as f:
                personas_data = json.load(f)
            return {"personas": personas_data}
        except Exception as e:
            # Fall back to defaults on error
            pass
    
    # Default personas if file doesn't exist
    default_personas = [
        {
            "id": "ultralight_backpacker_sarah",
            "name": "Sarah Martinez",
            "avatar_color": "from-teal-500 to-cyan-500",
            "story": "Planning a 3-week Pacific Crest Trail thru-hike",
            "sessions": [
                {
                    "goal": "Research ultralight shelter options",
                    "timeframe": "3 days ago",
                    "item_count": 12,
                    "categories": ["Tents", "Tarps"]
                },
                {
                    "goal": "Find lightweight sleep system",
                    "timeframe": "2 days ago",
                    "item_count": 8,
                    "categories": ["Sleeping Bags", "Pads"]
                },
                {
                    "goal": "Browse backpacks",
                    "timeframe": "Yesterday",
                    "item_count": 15,
                    "categories": ["Backpacks"]
                }
            ],
            "total_views": 35,
            "total_cart_adds": 3
        },
        {
            "id": "family_camper_mike",
            "name": "Mike Chen",
            "avatar_color": "from-amber-500 to-orange-500",
            "story": "Getting gear for weekend family camping trips",
            "sessions": [
                {
                    "goal": "Find a spacious family tent",
                    "timeframe": "5 days ago",
                    "item_count": 9,
                    "categories": ["Tents"]
                },
                {
                    "goal": "Camp kitchen and cooking gear",
                    "timeframe": "3 days ago",
                    "item_count": 11,
                    "categories": ["Stoves", "Cookware"]
                }
            ],
            "total_views": 20,
            "total_cart_adds": 5
        },
        {
            "id": "winter_mountaineer_alex",
            "name": "Alex Thompson",
            "avatar_color": "from-blue-500 to-indigo-500",
            "story": "Preparing for winter alpine climbing season",
            "sessions": [
                {
                    "goal": "Upgrade 4-season tent for alpine",
                    "timeframe": "1 week ago",
                    "item_count": 6,
                    "categories": ["Tents"]
                },
                {
                    "goal": "Cold weather sleep system",
                    "timeframe": "5 days ago",
                    "item_count": 7,
                    "categories": ["Sleeping Bags", "Pads"]
                }
            ],
            "total_views": 18,
            "total_cart_adds": 4
        },
        {
            "id": "weekend_hiker_emma",
            "name": "Emma Wilson",
            "avatar_color": "from-green-500 to-emerald-500",
            "story": "New to hiking, building out day hike essentials",
            "sessions": [
                {
                    "goal": "Day hiking essentials research",
                    "timeframe": "4 days ago",
                    "item_count": 16,
                    "categories": ["Backpacks", "Hydration"]
                },
                {
                    "goal": "Revisit favorites",
                    "timeframe": "Yesterday",
                    "item_count": 4,
                    "categories": ["Backpacks", "Water Filters"]
                }
            ],
            "total_views": 20,
            "total_cart_adds": 1
        },
        {
            "id": "car_camper_david",
            "name": "David Park",
            "avatar_color": "from-purple-500 to-pink-500",
            "story": "Car camping enthusiast, prioritizes comfort and luxury",
            "sessions": [
                {
                    "goal": "Luxury camping gear upgrade",
                    "timeframe": "6 days ago",
                    "item_count": 7,
                    "categories": ["Tents", "Sleeping Bags"]
                },
                {
                    "goal": "Comfort accessories",
                    "timeframe": "3 days ago",
                    "item_count": 10,
                    "categories": ["Accessories", "Cookware"]
                }
            ],
            "total_views": 17,
            "total_cart_adds": 6
        },
        {
            "id": "user_new",
            "name": "Guest User",
            "avatar_color": "from-gray-500 to-slate-500",
            "story": "First-time visitor, browsing casually",
            "sessions": [],
            "total_views": 0,
            "total_cart_adds": 0
        },
        {
            "id": "user_member",
            "name": "Alex Hiker",
            "avatar_color": "from-emerald-500 to-teal-500",
            "story": "Experienced hiker with ultralight preferences",
            "sessions": [
                {
                    "goal": "Ultralight gear browsing",
                    "timeframe": "2 days ago",
                    "item_count": 13,
                    "categories": ["Backpacks", "Tents"]
                }
            ],
            "total_views": 13,
            "total_cart_adds": 2
        },
        {
            "id": "user_business",
            "name": "Casey Campground",
            "avatar_color": "from-orange-500 to-red-500",
            "story": "Campground owner purchasing bulk equipment",
            "sessions": [
                {
                    "goal": "Bulk tent purchases",
                    "timeframe": "4 days ago",
                    "item_count": 11,
                    "categories": ["Tents"]
                },
                {
                    "goal": "Campground amenities",
                    "timeframe": "Yesterday",
                    "item_count": 8,
                    "categories": ["Cookware", "Accessories"]
                }
            ],
            "total_views": 19,
            "total_cart_adds": 9
        }
    ]
    
    return {"personas": default_personas}

