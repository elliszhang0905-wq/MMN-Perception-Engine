BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS geo_schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO geo_schema_meta VALUES (1, strftime('%Y-%m-%dT%H:%M:%SZ','now'));
CREATE TABLE IF NOT EXISTS geo_project (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, edition TEXT NOT NULL,
 payload_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_question (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 active INTEGER NOT NULL CHECK(active IN (0,1)), latest_version INTEGER NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_question_version (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 question_id TEXT NOT NULL, version INTEGER NOT NULL, payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(org_id,id), UNIQUE(org_id,question_id,version),
 FOREIGN KEY(org_id,question_id) REFERENCES geo_question(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_condition (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 condition_hash TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(org_id,id), UNIQUE(org_id,project_id,condition_hash),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_fact_baseline (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 logical_id TEXT NOT NULL, version INTEGER NOT NULL, payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(org_id,id), UNIQUE(org_id,logical_id,version),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_batch (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','queued','running','completed','completed_with_errors','cancelled','blocked')),
 paused INTEGER NOT NULL DEFAULT 0 CHECK(paused IN (0,1)), manifest_json TEXT NOT NULL,
 budget_day TEXT NOT NULL, reserved_micro INTEGER NOT NULL DEFAULT 0,
 held_micro INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(org_id,id), UNIQUE(org_id,project_id,idempotency_key),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_daily_budget (
 org_id TEXT NOT NULL, project_id TEXT NOT NULL, day TEXT NOT NULL, currency TEXT NOT NULL,
 reserved_micro INTEGER NOT NULL DEFAULT 0 CHECK(reserved_micro>=0),
 spent_micro INTEGER NOT NULL DEFAULT 0 CHECK(spent_micro>=0),
 PRIMARY KEY(org_id,project_id,day,currency),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_observation (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, batch_id TEXT NOT NULL,
 question_version_id TEXT NOT NULL, condition_id TEXT NOT NULL, repeat_index INTEGER NOT NULL,
 status TEXT NOT NULL, answer TEXT NOT NULL DEFAULT '', payload_json TEXT NOT NULL DEFAULT '{}',
 raw_json TEXT, raw_hash TEXT, analysis_json TEXT, sample_metadata_json TEXT NOT NULL DEFAULT '{}',
 channel TEXT NOT NULL, evidence_origin TEXT NOT NULL DEFAULT 'provider_api',
 lease_owner TEXT, lease_expires REAL, next_attempt_at REAL NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL, sampled_at TEXT,
 UNIQUE(org_id,id), UNIQUE(org_id,batch_id,question_version_id,condition_id,repeat_index),
 FOREIGN KEY(org_id,batch_id) REFERENCES geo_batch(org_id,id),
 FOREIGN KEY(org_id,question_version_id) REFERENCES geo_question_version(org_id,id),
 FOREIGN KEY(org_id,condition_id) REFERENCES geo_condition(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_attempt (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, observation_id TEXT NOT NULL,
 attempt_index INTEGER NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}',
 request_id TEXT, raw_json TEXT, raw_hash TEXT, cost_micro INTEGER,
 billing_uncertain INTEGER NOT NULL DEFAULT 0, budget_day TEXT NOT NULL,
 reserved_micro INTEGER NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
 UNIQUE(org_id,id), UNIQUE(org_id,observation_id,attempt_index),
 FOREIGN KEY(org_id,observation_id) REFERENCES geo_observation(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_review (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, observation_id TEXT NOT NULL,
 payload_json TEXT NOT NULL, actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(org_id,observation_id) REFERENCES geo_observation(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_citation (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, observation_id TEXT NOT NULL,
 payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(org_id,observation_id) REFERENCES geo_observation(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_diagnostic_review (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 diagnostic_id TEXT NOT NULL, source_hash TEXT NOT NULL, decision TEXT NOT NULL,
 payload_json TEXT NOT NULL, actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE INDEX IF NOT EXISTS geo_diagnostic_review_scope ON geo_diagnostic_review(org_id,project_id,diagnostic_id,created_at);
CREATE TRIGGER IF NOT EXISTS geo_diagnostic_review_immutable BEFORE UPDATE ON geo_diagnostic_review BEGIN SELECT RAISE(ABORT,'immutable GEO diagnostic review'); END;
CREATE TABLE IF NOT EXISTS geo_screenshot (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, observation_id TEXT NOT NULL,
 mime TEXT NOT NULL, content BLOB NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(org_id,observation_id) REFERENCES geo_observation(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_action (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
 payload_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_retest (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, action_id TEXT NOT NULL,
 baseline_batch_id TEXT NOT NULL, batch_id TEXT NOT NULL, payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(org_id,id), UNIQUE(org_id,action_id,batch_id),
 FOREIGN KEY(org_id,action_id) REFERENCES geo_action(org_id,id),
 FOREIGN KEY(org_id,baseline_batch_id) REFERENCES geo_batch(org_id,id),
 FOREIGN KEY(org_id,batch_id) REFERENCES geo_batch(org_id,id),
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE TABLE IF NOT EXISTS geo_audit (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL, event TEXT NOT NULL,
 record_id TEXT NOT NULL, actor TEXT NOT NULL, detail_json TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(org_id,project_id) REFERENCES geo_project(org_id,id)
);
CREATE INDEX IF NOT EXISTS geo_project_scope ON geo_project(org_id,edition,created_at);
CREATE INDEX IF NOT EXISTS geo_question_scope ON geo_question(org_id,project_id,active);
CREATE INDEX IF NOT EXISTS geo_fact_scope ON geo_fact_baseline(org_id,project_id,logical_id,version);
CREATE INDEX IF NOT EXISTS geo_batch_state ON geo_batch(status,paused,created_at);
CREATE INDEX IF NOT EXISTS geo_batch_scope ON geo_batch(org_id,project_id,created_at);
CREATE INDEX IF NOT EXISTS geo_observation_scope ON geo_observation(org_id,project_id,batch_id,channel,status);
CREATE INDEX IF NOT EXISTS geo_observation_lease ON geo_observation(status,lease_expires,next_attempt_at);
CREATE INDEX IF NOT EXISTS geo_attempt_scope ON geo_attempt(org_id,observation_id,attempt_index);
CREATE INDEX IF NOT EXISTS geo_review_scope ON geo_review(org_id,observation_id,created_at);
CREATE INDEX IF NOT EXISTS geo_audit_scope ON geo_audit(org_id,project_id,created_at);
CREATE TRIGGER IF NOT EXISTS geo_question_version_immutable BEFORE UPDATE ON geo_question_version BEGIN SELECT RAISE(ABORT,'immutable GEO question version'); END;
CREATE TRIGGER IF NOT EXISTS geo_condition_immutable BEFORE UPDATE ON geo_condition BEGIN SELECT RAISE(ABORT,'immutable GEO condition'); END;
CREATE TRIGGER IF NOT EXISTS geo_fact_immutable BEFORE UPDATE ON geo_fact_baseline BEGIN SELECT RAISE(ABORT,'immutable GEO fact version'); END;
CREATE TRIGGER IF NOT EXISTS geo_review_immutable BEFORE UPDATE ON geo_review BEGIN SELECT RAISE(ABORT,'immutable GEO review'); END;
CREATE TRIGGER IF NOT EXISTS geo_observation_evidence_immutable BEFORE UPDATE OF answer,raw_json,raw_hash,analysis_json ON geo_observation WHEN OLD.raw_hash IS NOT NULL BEGIN SELECT RAISE(ABORT,'immutable GEO observation evidence'); END;
COMMIT;
