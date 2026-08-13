from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import date, datetime

class City(BaseModel):
    id: str
    name: str
    country: str
    cost_index: float = 0.0
    safety_index: float = 0.0
    weather_score: float = 0.0
    attraction_density: float = 0.0
    nightlife_score: float = 0.0
    walkability_score: float = 0.0
    flight_score: float = 0.0
    computed_score: float = 0.0
    image: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    region: Optional[str] = None

class POILocation(BaseModel):
    lat: float
    lng: float

class POI(BaseModel):
    id: str
    city_id: str
    name: str
    type: str  # "restaurant" | "attraction" | "cafe" | "viewpoint"
    rating: float = 0.0
    user_ratings_total: int = 0
    price_level: Optional[int] = None
    opening_hours: Optional[Dict] = None
    location: POILocation
    image_url: Optional[str] = None
    address: Optional[str] = None

class TravelPreferences(BaseModel):
    weather_temp: float = 22.0
    cost_pref: str = "medium"  # "low" | "medium" | "high"
    vibe_urban_nature: int = 50  # 0-100 (0: nature, 100: urban)
    vibe_calm_party: int = 50    # 0-100 (0: calm, 100: party)
    vibe_history: int = 5         # 1-10 (historical importance)
    safety_level: str = "medium" # "low" | "medium" | "high"
    crowds_pref: str = "medium"  # "low" | "medium" | "high"
    travel_time_max: int = 12    # hours
    interests: List[str] = Field(default_factory=list) # e.g. ["culture", "food", "nature", "nightlife"]

class Trip(BaseModel):
    id: str
    user_id: str
    city_id: str
    start_date: Union[date, str]
    end_date: Union[date, str]
    budget: float
    preferences: TravelPreferences

class ItineraryItem(BaseModel):
    poi_id: Optional[str] = None  # None for travel
    poi_name: Optional[str] = None
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    type: str  # "activity" | "meal" | "travel"
    locked: bool = False
    details: Optional[Dict] = None # details like travel duration, distance, price, booking url, address, type, etc.

class ItineraryDay(BaseModel):
    date: str  # "YYYY-MM-DD"
    items: List[ItineraryItem] = Field(default_factory=list)
