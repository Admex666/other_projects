"""DuckDB adatbázis sémák és DDL utasítások."""

SCHEMA_SQL = """
-- 1. Knowledge Layer: Entitások
CREATE TABLE IF NOT EXISTS entities (
    entity_id VARCHAR PRIMARY KEY,
    label_hu VARCHAR NOT NULL,
    label_en VARCHAR,
    domain VARCHAR NOT NULL,
    subdomain VARCHAR,
    wikidata_qid VARCHAR,
    description VARCHAR,
    metadata JSON,
    relevance_score DOUBLE DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Knowledge Layer: Relációk (irányított élek)
CREATE TABLE IF NOT EXISTS relations (
    relation_id VARCHAR PRIMARY KEY,
    source_entity_id VARCHAR NOT NULL,
    target_entity_id VARCHAR NOT NULL,
    relation_type VARCHAR NOT NULL,
    weight DOUBLE DEFAULT 1.0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Quiz Layer: Kvízkérdések és mechanizmusok
CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id VARCHAR PRIMARY KEY,
    text VARCHAR NOT NULL,
    mechanism VARCHAR NOT NULL,
    correct_answer VARCHAR NOT NULL,
    options JSON,
    domain VARCHAR NOT NULL,
    subdomain VARCHAR,
    source_type VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Kapcsoló tábla a kérdések és az érintett entitások között
CREATE TABLE IF NOT EXISTS question_entities (
    question_id VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'topic',
    PRIMARY KEY (question_id, entity_id)
);

-- 5. Locality Layer: Magyar kvízrelevancia és gyakoriság
CREATE TABLE IF NOT EXISTS entity_relevance (
    entity_id VARCHAR PRIMARY KEY,
    corpus_frequency INTEGER DEFAULT 0,
    degree_centrality INTEGER DEFAULT 0,
    hungarian_quiz_score DOUBLE DEFAULT 1.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Player Layer: Játékos válaszok és önértékelés (confidence)
CREATE TABLE IF NOT EXISTS player_answers (
    answer_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    question_id VARCHAR NOT NULL,
    given_answer VARCHAR NOT NULL,
    is_correct BOOLEAN NOT NULL,
    confidence_level DOUBLE NOT NULL,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Player Layer: Képességmátrix (Domain x Mechanism szinten)
CREATE TABLE IF NOT EXISTS player_skills (
    user_id VARCHAR NOT NULL,
    domain VARCHAR NOT NULL,
    mechanism VARCHAR NOT NULL,
    skill_rating DOUBLE DEFAULT 0.5,
    confidence_bias DOUBLE DEFAULT 0.0,
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, domain, mechanism)
);
"""
