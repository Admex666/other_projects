from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/world", tags=["world"])

class Zone(BaseModel):
    id: str
    name: str
    description: str
    boundary_points: List[List[float]]
    difficulty_level: int

class Encounter(BaseModel):
    id: str
    title: str
    description: str
    type: str # quest, random, story
    nodes: dict
    start_node_id: str
    location: List[float]
    zone_id: str

@router.get("/nearby")
def get_nearby_world(lat: float, lon: float):
    # For now, return ALL zones and encounters. 
    # Real implementation would filter by distance/bounds.
    
    zones = [
        {
            "id": "zone_belvaros",
            "name": "Belváros - A Ködös Utcák",
            "description": "A régi Pest szíve. Itt a legerősebb a Rend őreinek jelenléte.",
            "boundary_points": [
                [47.498, 19.040], [47.502, 19.050],
                [47.495, 19.060], [47.490, 19.045]
            ],
            "difficulty_level": 1
        },
        {
            "id": "zone_nyolcker",
            "name": "VIII. Kerület - A Sötét Parkok",
            "description": "A senki földje. Kereskedők, csempészek és bukott költők tanyája.",
            "boundary_points": [
                [47.495, 19.065], [47.498, 19.080],
                [47.485, 19.085], [47.485, 19.070]
            ],
            "difficulty_level": 3
        },
        {
            "id": "zone_gellert",
            "name": "Gellért-hegy - A Boszorkányok Sziklája",
            "description": "A város fölé magasodó szikla, ahol az ősi energiák összegyűlnek.",
            "boundary_points": [
                [47.490, 19.030], [47.485, 19.035], 
                [47.482, 19.045], [47.488, 19.055],
                [47.492, 19.048]
            ],
            "difficulty_level": 5
        }
    ]

    encounters = [
        # Intro Encounter (Virtual/Loc independent potentially, but placed in Belvaros)
        {
            "id": "enc_poet_ghost",
            "title": "Az Elfeledett Költő Szelleme",
            "description": "Egy halvány alak szaval a lámpaoszlop alatt.",
            "type": "story",
            "location": [47.498, 19.040],
            "zone_id": "zone_belvaros",
            "start_node_id": "start",
            "nodes": {
                "start": {
                    "id": "start", "type": "narrative",
                    "text": "A szellem feléd fordul. 'Emlékszel még a régi szavakra?'",
                    "next_node_id": "choice1"
                },
                "choice1": {
                    "id": "choice1", "type": "choice",
                    "text": "Mit válaszolsz?",
                    "choices": [
                         {"text": "Igen, emlékszem.", "next_node_id": "end_good"},
                         {"text": "Nem tudom miről beszélsz.", "next_node_id": "end_bad"}
                    ]
                },
                "end_good": {"id": "end_good", "type": "narrative", "text": "A szellem elmosolyodik és köddé válik. (Kaptál egy ősi érmét!)"}, # Logic handled by quest sync ideally
                "end_bad": {"id": "end_bad", "type": "narrative", "text": "A szellem szomorúan rázza a fejét."}
            }
        },
        # Gellért Hill Encounter
        {
            "id": "enc_citadella_shadows",
            "title": "A Citadella Árnyai",
            "description": "Sötét alakok gyülekeznek a régi erőd falainál.",
            "type": "fight", # Or quest
            "location": [47.487, 19.044], # Near Citadella
            "zone_id": "zone_gellert",
             "start_node_id": "start",
             "nodes": {
                 "start": {
                    "id": "start", "type": "fight",
                    "text": "Egy Árny-Őr állja utadat!",
                    "enemy_id": "enemy_shadow_guard",
                    "enemy_hp": 30,
                    "success_node_id": "win",
                    "failure_node_id": "lose"
                 },
                 "win": {"id": "win", "type": "narrative", "text": "Legyőzted az árnyat! Az út szabad."},
                 "lose": {"id": "lose", "type": "narrative", "text": "Az árny túl erős volt... Visszavonulsz."}
             }
        }
    ]
    
    return {"zones": zones, "encounters": encounters}
