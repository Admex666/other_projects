import logging
from app.db.crud import create_quest
from app.models.schemas import Encounter, EncounterNode, EncounterChoice, EncounterType, EncounterNodeType
from .story_service import STORY_DATA

logger = logging.getLogger(__name__)

dynamic_encounters = []

def sync_stories_to_quests_v2():
    """
    Simulates the 'Quest' structures from the loaded JSON stories.
    This replaces the hardcoded seed_quests for Story-based content.
    """
    dynamic_encounters.clear() # Clear in-place
    
    for story_id, story in STORY_DATA.items():
        if "rewards_xp" not in story and "estimated_distance_km" not in story:
            continue
            
        stages = []
        current_node_id = story.get("startNode")
        visited = set()
        
        while current_node_id and current_node_id not in visited:
            visited.add(current_node_id)
            node = story["nodes"].get(current_node_id)
            if not node: break
            
            if node.get("type") == "location_wait":
                next_node_id = node.get("next")
                if next_node_id:
                    stage_encounter_id = f"{story_id}_{next_node_id}"
                    
                    stages.append({
                        "id": f"{story_id}_stage_{len(stages)+1}",
                        "description": node.get("description", node.get("text")[:50]+"..."),
                        "location": (node["targetLocation"]["lat"], node["targetLocation"]["lng"]),
                        "encounter_id": stage_encounter_id 
                    })
                    
                    enc_nodes = {}
                    # Identify all reachable nodes from this encounter start
                    # For MVP, we collect all nodes from the story for each encounter (simple but works)
                    wait_node_ids = {nid for nid, n in story["nodes"].items() if n.get("type") == "location_wait"}
                    
                    for nid, nops in story["nodes"].items():
                        choices = []
                        if nops.get("choices"):
                            choices = []
                            for c in nops["choices"]:
                                next_id = c.get("next") or c.get("next_node_id")
                                if next_id in wait_node_ids:
                                    next_id = None
                                choices.append(EncounterChoice(text=c["text"], next_node_id=next_id))
                            
                        node_next_id = nops.get("next") or nops.get("successNext")
                        success_id = nops.get("successNext")
                        failure_id = nops.get("failureNext")
                        
                        # CRITICAL: If any pointer goes to a location_wait, cut it off so the encounter ends
                        if node_next_id in wait_node_ids: node_next_id = None
                        if success_id in wait_node_ids: success_id = None
                        if failure_id in wait_node_ids: failure_id = None
                            
                        # Handle answers (can be correctAnswer string or validAnswers list)
                        correct_val = nops.get("correctAnswer")
                        v_answers = nops.get("validAnswers", [])
                        if not v_answers and correct_val:
                            v_answers = [correct_val]
                        # For 'order' type, we still use correct_answer as the canonical string
                        # For 'input' type, valid_answers list is preferred
                        
                        enc_nodes[nid] = EncounterNode(
                            id=nid,
                            type=EncounterNodeType[nops.get("type", "narrative").upper()] if nops.get("type") != "location_wait" else EncounterNodeType.NARRATIVE,
                            text=nops.get("text", ""),
                            choices=choices if choices else None,
                            next_node_id=node_next_id,
                            image=nops.get("image"),
                            enemy_id=nops.get("enemyId"),
                            enemy_hp=nops.get("enemyHp"),
                            correct_answer=correct_val,
                            valid_answers=v_answers if v_answers else None,
                            success_node_id=success_id,
                            failure_node_id=failure_id,
                            button_text=nops.get("buttonText"),
                            options=nops.get("options")
                        )
                    
                    enc_obj = Encounter(
                        id=stage_encounter_id,
                        title=story.get("title") + " - " + node.get("description", "Stage"),
                        description=stages[-1]["description"],
                        type=EncounterType.STORY,
                        start_node_id=next_node_id, 
                        location=stages[-1]["location"],
                        nodes=enc_nodes,
                        zone_id="zone_nyolcker" # Default
                    )
                    dynamic_encounters.append(enc_obj)
                
            # Advancing to find next location_wait
            next_candidates = [
                node.get("next"),
                node.get("successNext"),
                node.get("failureNext")
            ]
            if node.get("choices"):
                for c in node["choices"]:
                    next_candidates.append(c.get("next"))
            
            # Pick first available non-visited candidate
            current_node_id = next((c for c in next_candidates if c and c not in visited), None)

        q_data = {
            "id": story_id,
            "title": story.get("title", "Untitled Story"),
            "description": story.get("description", "A mystery awaits..."),
            "flavor_text": story.get("flavor_text", ""),
            "image_url": story.get("image_url"),
            "start_location": tuple(stages[0]["location"]) if stages else (47.4979, 19.0402), 
            "stages": stages,
            "estimated_distance_km": story.get("estimated_distance_km", 1.0),
            "estimated_duration_min": story.get("estimated_duration_min", 30),
            "difficulty": story.get("difficulty", "Közepes"),
            "intro_steps": story.get("intro_steps", []),
            "min_level": story.get("min_level", 1),
            "objectives": [],
            "rewards_xp": story.get("rewards_xp", 100),
            "rewards_items": story.get("rewards_items", []),
            "starter_zone_id": "zone_nyolcker"
        }
        
        create_quest(q_data)
        logger.info(f" synced quest: {story_id} with {len(stages)} stages")

def seed_quests():
    q1 = {
        "id": "quest_opera_ghost",
        "title": "Az Operaház Fantomja",
        "description": "Keresd meg a ködben bujkáló szellemet.",
        "flavor_text": "Az Operaház árnyékában valami nem hagy nyugodni a lelkeket.",
        "image_url": "assets/mist_opera_phantom.png",
        "start_location": (47.502, 19.058),
        "min_level": 1,
        "objectives": [],
        "rewards_xp": 250,
        "starter_zone_id": "zone_belvaros",
        "stages": []
    }
    q2 = {
        "id": "quest_eight_shadows",
        "title": "A Nyolcadik Kerület Árnyai",
        "description": "Tudd meg, miért gyülekeznek a Vámszedők.",
        "flavor_text": "A Józsefvárosi piac környékén sötét alakok suttognak.",
        "image_url": "assets/mist_shadows_stairs.png",
        "start_location": (47.495, 19.075),
        "min_level": 2,
        "objectives": [],
        "rewards_xp": 500,
        "starter_zone_id": "zone_nyolcker",
        "stages": []
    }
    create_quest(q1)
    create_quest(q2)
