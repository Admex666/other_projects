"""Wikidata SPARQL lekérdező és triplet-kinyerő modul."""

from typing import Any, Dict, List, Tuple
from quizforge.core.constants import Domain, SourceType
from quizforge.core.models import Entity, Relation
from quizforge.ingestion.base import BaseIngestor


class WikidataIngestor(BaseIngestor):
    """Wikidata SPARQL lekérdező magyar relevanciájú tudáselemekhez."""

    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    def __init__(self):
        super().__init__(
            source_name="Wikidata SPARQL",
            source_type=SourceType.WIKIDATA,
            endpoint=self.SPARQL_ENDPOINT
        )

    def fetch_sample(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Mintalekérdezés futtatása: Magyar Nobel-díjasok kinyerése."""
        query = f"""
        SELECT ?person ?personLabel ?award ?awardLabel ?year WHERE {{
          ?person wdt:P166 ?award .
          ?award wdt:P31/wdt:P279* wd:Q7191 . # Nobel-díj
          ?person wdt:P27 wd:Q28 .           # Magyar állampolgárság / Magyarország
          OPTIONAL {{
            ?person p:P166 ?statement .
            ?statement ps:P166 ?award .
            ?statement pq:P585 ?date .
            BIND(YEAR(?date) AS ?year)
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "hu,en". }}
        }}
        LIMIT {limit}
        """
        response = self.client.get(
            self.SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"Accept": "application/sparql-results+json"}
        )
        response.raise_for_status()
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        
        results = []
        for b in bindings:
            results.append({
                "person_uri": b.get("person", {}).get("value", ""),
                "person_label": b.get("personLabel", {}).get("value", ""),
                "award_uri": b.get("award", {}).get("value", ""),
                "award_label": b.get("awardLabel", {}).get("value", ""),
                "year": b.get("year", {}).get("value", "")
            })
        return results

    def fetch_hungarian_counties(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Magyar vármegyék, székhelyeik és népességük."""
        query = f"""
        SELECT ?county ?countyLabel ?seat ?seatLabel ?population WHERE {{
          ?county wdt:P31 wd:Q17502758 . # Magyarország vármegyéi
          OPTIONAL {{ ?county wdt:P36 ?seat . }}
          OPTIONAL {{ ?county wdt:P1082 ?population . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "hu,en". }}
        }}
        LIMIT {limit}
        """
        response = self.client.get(
            self.SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"Accept": "application/sparql-results+json"}
        )
        response.raise_for_status()
        bindings = response.json().get("results", {}).get("bindings", [])
        results = []
        for b in bindings:
            results.append({
                "county_uri": b.get("county", {}).get("value", ""),
                "county_label": b.get("countyLabel", {}).get("value", ""),
                "seat_uri": b.get("seat", {}).get("value", ""),
                "seat_label": b.get("seatLabel", {}).get("value", ""),
                "population": b.get("population", {}).get("value", "")
            })
        return results

    def extract_triplets(self, sample_data: List[Dict[str, Any]]) -> Tuple[List[Entity], List[Relation]]:
        """Wikidata eredmények átalakítása entitásokká és relációkká."""
        entities: Dict[str, Entity] = {}
        relations: List[Relation] = []

        for idx, row in enumerate(sample_data):
            if "person_uri" in row and "award_uri" in row:
                # Nobel-díjas séma
                p_id = row["person_uri"].split("/")[-1]
                p_name = row["person_label"]
                a_id = row["award_uri"].split("/")[-1]
                a_name = row["award_label"]
                year = row.get("year")

                if p_id not in entities:
                    entities[p_id] = Entity(
                        entity_id=f"wd:{p_id}",
                        label_hu=p_name,
                        domain=Domain.SCIENCE_TECH,
                        subdomain="nobel_laureate",
                        wikidata_qid=p_id,
                        relevance_score=1.5
                    )
                if a_id not in entities:
                    entities[a_id] = Entity(
                        entity_id=f"wd:{a_id}",
                        label_hu=a_name,
                        domain=Domain.GENERAL_KNOWLEDGE,
                        subdomain="award",
                        wikidata_qid=a_id,
                        relevance_score=1.2
                    )

                rel_id = f"rel:nobel:{p_id}:{a_id}:{idx}"
                relations.append(Relation(
                    relation_id=rel_id,
                    source_entity_id=f"wd:{p_id}",
                    target_entity_id=f"wd:{a_id}",
                    relation_type="KAPOTT_DÍJAT",
                    metadata={"year": year} if year else {}
                ))
            elif "county_uri" in row and "seat_uri" in row:
                # Vármegye séma
                c_id = row["county_uri"].split("/")[-1]
                c_name = row["county_label"]
                s_id = row["seat_uri"].split("/")[-1]
                s_name = row["seat_label"]
                pop = row.get("population")

                if c_id not in entities:
                    entities[c_id] = Entity(
                        entity_id=f"wd:{c_id}",
                        label_hu=c_name,
                        domain=Domain.GEOGRAPHY,
                        subdomain="county",
                        wikidata_qid=c_id,
                        metadata={"population": pop} if pop else {},
                        relevance_score=1.4
                    )
                if s_id and s_id not in entities:
                    entities[s_id] = Entity(
                        entity_id=f"wd:{s_id}",
                        label_hu=s_name,
                        domain=Domain.GEOGRAPHY,
                        subdomain="city",
                        wikidata_qid=s_id,
                        relevance_score=1.3
                    )

                if s_id:
                    relations.append(Relation(
                        relation_id=f"rel:seat:{c_id}:{s_id}",
                        source_entity_id=f"wd:{c_id}",
                        target_entity_id=f"wd:{s_id}",
                        relation_type="SZÉKHELYE"
                    ))

        return list(entities.values()), relations

    def get_seed_curated_knowledge(self) -> Tuple[List[Entity], List[Relation]]:
        """Alapvető, minőségi kvíz tudáselemek (Nobel-díjak, feltalálók, írók)."""
        entities = [
            # Nobel-díj kategóriák (award)
            Entity(entity_id="wd:Q38104", label_hu="fizikai Nobel-díj", domain=Domain.SCIENCE_TECH, subdomain="award", relevance_score=2.0),
            Entity(entity_id="wd:Q44585", label_hu="kémiai Nobel-díj", domain=Domain.SCIENCE_TECH, subdomain="award", relevance_score=2.0),
            Entity(entity_id="wd:Q80061", label_hu="fiziológiai és orvostudományi Nobel-díj", domain=Domain.SCIENCE_TECH, subdomain="award", relevance_score=2.0),
            Entity(entity_id="wd:Q37922", label_hu="irodalmi Nobel-díj", domain=Domain.LITERATURE, subdomain="award", relevance_score=2.0),
            Entity(entity_id="wd:Q35637", label_hu="Nobel-békedíj", domain=Domain.GENERAL_KNOWLEDGE, subdomain="award", relevance_score=2.0),
            Entity(entity_id="wd:Q47170", label_hu="közgazdasági Nobel-emlékdíj", domain=Domain.GENERAL_KNOWLEDGE, subdomain="award", relevance_score=2.0),

            # Híres magyar feltalálók (inventor)
            Entity(entity_id="inv:biro", label_hu="Bíró László", domain=Domain.SCIENCE_TECH, subdomain="inventor", relevance_score=1.8),
            Entity(entity_id="inv:rubik", label_hu="Rubik Ernő", domain=Domain.SCIENCE_TECH, subdomain="inventor", relevance_score=1.8),
            Entity(entity_id="inv:jedlik", label_hu="Jedlik Ányos", domain=Domain.SCIENCE_TECH, subdomain="inventor", relevance_score=1.8),
            Entity(entity_id="inv:puskas", label_hu="Puskás Tivadar", domain=Domain.SCIENCE_TECH, subdomain="inventor", relevance_score=1.8),
            Entity(entity_id="inv:gabor", label_hu="Gábor Dénes", domain=Domain.SCIENCE_TECH, subdomain="inventor", relevance_score=1.8),

            # Híres magyar találmányok (invention)
            Entity(entity_id="item:golyostoll", label_hu="golyóstoll", domain=Domain.SCIENCE_TECH, subdomain="invention", relevance_score=1.8),
            Entity(entity_id="item:rubik_kocka", label_hu="Rubik-kocka (bűvös kocka)", domain=Domain.SCIENCE_TECH, subdomain="invention", relevance_score=1.8),
            Entity(entity_id="item:dinamo", label_hu="dinamó elv", domain=Domain.SCIENCE_TECH, subdomain="invention", relevance_score=1.8),
            Entity(entity_id="item:telefonkozpont", label_hu="telefonközpont", domain=Domain.SCIENCE_TECH, subdomain="invention", relevance_score=1.8),
            Entity(entity_id="item:holografia", label_hu="holográfia", domain=Domain.SCIENCE_TECH, subdomain="invention", relevance_score=1.8),

            # Híres magyar írók (author)
            Entity(entity_id="aut:arany", label_hu="Arany János", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:petofi", label_hu="Petőfi Sándor", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:madach", label_hu="Madách Imre", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:gardonyi", label_hu="Gárdonyi Géza", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:jokai", label_hu="Jókai Mór", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:moricz", label_hu="Móricz Zsigmond", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:mikszath", label_hu="Mikszáth Kálmán", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:karinthy", label_hu="Karinthy Frigyes", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:kosztolanyi", label_hu="Kosztolányi Dezső", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:jozsef_a", label_hu="József Attila", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:radnoti", label_hu="Radnóti Miklós", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),
            Entity(entity_id="aut:ady", label_hu="Ady Endre", domain=Domain.LITERATURE, subdomain="author", relevance_score=2.0),

            # Híres magyar klasszikus művek (book)
            Entity(entity_id="book:toldi", label_hu="Toldi", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:janos_vitez", label_hu="János vitéz", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:tragedia", label_hu="Az ember tragédiája", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:egri_csillagok", label_hu="Egri csillagok", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:koszivu", label_hu="A kőszívű ember fiai", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:legy_jo", label_hu="Légy jó mindhalálig", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:fekete_varos", label_hu="A fekete város", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:utazas_koponyam", label_hu="Utazás a koponyám körül", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:edes_anna", label_hu="Édes Anna", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:tiszta_szivvel", label_hu="Tiszta szívvel", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:nem_tudhatom", label_hu="Nem tudhatom", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),
            Entity(entity_id="book:uj_versek", label_hu="Új versek", domain=Domain.LITERATURE, subdomain="book", relevance_score=2.0),

            # Magyar vármegyék (county)
            Entity(entity_id="geo:bekes", label_hu="Békés vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:csongrad", label_hu="Csongrád-Csanád vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:hajdu", label_hu="Hajdú-Bihar vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:baranya", label_hu="Baranya vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:borsod", label_hu="Borsod-Abaúj-Zemplén vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:gyor", label_hu="Győr-Moson-Sopron vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:fejer", label_hu="Fejér vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:somogy", label_hu="Somogy vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:zala", label_hu="Zala vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:veszprem", label_hu="Veszprém vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:tolna", label_hu="Tolna vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),
            Entity(entity_id="geo:vas", label_hu="Vas vármegye", domain=Domain.GEOGRAPHY, subdomain="county", relevance_score=1.8),

            # Magyar megyeszékhelyek (city)
            Entity(entity_id="city:bekescsaba", label_hu="Békéscsaba", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:szeged", label_hu="Szeged", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:debrecen", label_hu="Debrecen", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:pecs", label_hu="Pécs", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:miskolc", label_hu="Miskolc", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:gyor", label_hu="Győr", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:szekesfehervar", label_hu="Székesfehérvár", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:kaposvar", label_hu="Kaposvár", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:zalaegerszeg", label_hu="Zalaegerszeg", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:veszprem", label_hu="Veszprém", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:szekszard", label_hu="Szekszárd", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
            Entity(entity_id="city:szombathely", label_hu="Szombathely", domain=Domain.GEOGRAPHY, subdomain="city", relevance_score=1.8),
        ]

        relations = [
            # Feltaláló - Találmány relációk
            Relation(relation_id="rel:inv:1", source_entity_id="inv:biro", target_entity_id="item:golyostoll", relation_type="TALÁLMÁNYA"),
            Relation(relation_id="rel:inv:2", source_entity_id="inv:rubik", target_entity_id="item:rubik_kocka", relation_type="TALÁLMÁNYA"),
            Relation(relation_id="rel:inv:3", source_entity_id="inv:jedlik", target_entity_id="item:dinamo", relation_type="TALÁLMÁNYA"),
            Relation(relation_id="rel:inv:4", source_entity_id="inv:puskas", target_entity_id="item:telefonkozpont", relation_type="TALÁLMÁNYA"),
            Relation(relation_id="rel:inv:5", source_entity_id="inv:gabor", target_entity_id="item:holografia", relation_type="TALÁLMÁNYA"),

            # Író - Mű relációk
            Relation(relation_id="rel:lit:1", source_entity_id="aut:arany", target_entity_id="book:toldi", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:2", source_entity_id="aut:petofi", target_entity_id="book:janos_vitez", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:3", source_entity_id="aut:madach", target_entity_id="book:tragedia", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:4", source_entity_id="aut:gardonyi", target_entity_id="book:egri_csillagok", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:5", source_entity_id="aut:jokai", target_entity_id="book:koszivu", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:6", source_entity_id="aut:moricz", target_entity_id="book:legy_jo", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:7", source_entity_id="aut:mikszath", target_entity_id="book:fekete_varos", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:8", source_entity_id="aut:karinthy", target_entity_id="book:utazas_koponyam", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:9", source_entity_id="aut:kosztolanyi", target_entity_id="book:edes_anna", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:10", source_entity_id="aut:jozsef_a", target_entity_id="book:tiszta_szivvel", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:11", source_entity_id="aut:radnoti", target_entity_id="book:nem_tudhatom", relation_type="SZERZŐJE"),
            Relation(relation_id="rel:lit:12", source_entity_id="aut:ady", target_entity_id="book:uj_versek", relation_type="SZERZŐJE"),

            # Vármegye - Székhely relációk
            Relation(relation_id="rel:seat:1", source_entity_id="geo:bekes", target_entity_id="city:bekescsaba", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:2", source_entity_id="geo:csongrad", target_entity_id="city:szeged", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:3", source_entity_id="geo:hajdu", target_entity_id="city:debrecen", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:4", source_entity_id="geo:baranya", target_entity_id="city:pecs", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:5", source_entity_id="geo:borsod", target_entity_id="city:miskolc", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:6", source_entity_id="geo:gyor", target_entity_id="city:gyor", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:7", source_entity_id="geo:fejer", target_entity_id="city:szekesfehervar", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:8", source_entity_id="geo:somogy", target_entity_id="city:kaposvar", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:9", source_entity_id="geo:zala", target_entity_id="city:zalaegerszeg", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:10", source_entity_id="geo:veszprem", target_entity_id="city:veszprem", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:11", source_entity_id="geo:tolna", target_entity_id="city:szekszard", relation_type="SZÉKHELYE"),
            Relation(relation_id="rel:seat:12", source_entity_id="geo:vas", target_entity_id="city:szombathely", relation_type="SZÉKHELYE"),
        ]

        return entities, relations
