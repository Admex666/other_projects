from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
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

# ============================================================================
# UNIFIED TRIP ARCHITECTURE MODELS
# ============================================================================

class TripInput(BaseModel):
    origin: str = "Budapest"
    origin_airport: Optional[str] = "BUD"
    adults: int = 2
    children: int = 0
    date_mode: str = "month" # 'exact' | 'interval' | 'month'
    month: str = "9"
    out_date_from: Optional[str] = None
    out_date_to: Optional[str] = None
    in_date_from: Optional[str] = None
    in_date_to: Optional[str] = None
    duration_days: int = 7
    min_stay: Optional[int] = 5
    max_stay: Optional[int] = 9
    daily_budget_eur: float = 150.0
    budget_strictness: str = "soft"
    exclusions: List[str] = Field(default_factory=list)
    destination_weights: Dict[str, float] = Field(default_factory=dict)

class TripDestination(BaseModel):
    name: str
    city: str
    country: str = ""
    region: str = ""
    rank: Optional[int] = 1
    score: Optional[float] = 0.0
    flight_price_huf: Optional[float] = 0.0
    flight_price_per_person: Optional[float] = 0.0
    temp_avg: Optional[float] = 22.0
    safety_index: Optional[float] = 60.0
    daily_cost_eur: Optional[float] = 45.0
    numbeo_breakdown: Dict[str, Any] = Field(default_factory=dict)
    highlights: List[str] = Field(default_factory=list)
    tradeoff: Optional[str] = None
    explanation: Optional[str] = None
    image: Optional[str] = None

class TripFlightItem(BaseModel):
    id: Optional[str] = None
    airline: str = "Járat"
    price_total_huf: float = 0.0
    price_per_person_huf: float = 0.0
    out_date: str = ""
    in_date: str = ""
    out_time: str = ""
    in_time: str = ""
    out_airport: str = "BUD"
    in_airport: str = ""
    duration_h: float = 0.0
    stops: int = 0
    phi_net: Optional[float] = None
    rank: Optional[int] = None
    adults: int = 2
    exact_stay_nights: int = 7
    booking_token: Optional[str] = None
    booking_url: Optional[str] = None

class TripFlightSearch(BaseModel):
    search_params: Dict[str, Any] = Field(default_factory=dict)
    ahp_weights: Dict[str, float] = Field(default_factory=dict)
    shortlist: List[TripFlightItem] = Field(default_factory=list)
    selected_flight: Optional[TripFlightItem] = None

class TripAccommodationItem(BaseModel):
    id: Optional[str] = None
    name: str = "Szállás"
    stars: int = 3
    rating: float = 8.0
    review_count: int = 0
    price_total_huf: float = 0.0
    price_per_night_huf: float = 0.0
    nights: int = 7
    address: str = ""
    city: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    image: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    booking_url: Optional[str] = None

class TripAccommodationSearch(BaseModel):
    search_params: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    shortlist: List[TripAccommodationItem] = Field(default_factory=list)
    selected_accommodation: Optional[TripAccommodationItem] = None

class TripBudgetItem(BaseModel):
    key: str
    icon: str
    name: str
    desc: str
    formula: str
    amount_huf: float
    badge: str = "Kalkulált"
    is_estimated: bool = False

class TripBudgetBreakdown(BaseModel):
    flight_total_huf: float = 0.0
    accommodation_total_huf: float = 0.0
    food_total_huf: float = 0.0
    transport_total_huf: float = 0.0
    total_huf: float = 0.0
    per_person_huf: float = 0.0
    items: List[TripBudgetItem] = Field(default_factory=list)

class UnifiedTrip(BaseModel):
    trip_id: str
    user_id: Optional[str] = "default_user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: str = "initialized" # initialized | destination_selected | flight_selected | accommodation_selected | proposal_ready
    input: TripInput = Field(default_factory=TripInput)
    destination: Optional[TripDestination] = None
    flight: TripFlightSearch = Field(default_factory=TripFlightSearch)
    accommodation: TripAccommodationSearch = Field(default_factory=TripAccommodationSearch)
    budget: TripBudgetBreakdown = Field(default_factory=TripBudgetBreakdown)

