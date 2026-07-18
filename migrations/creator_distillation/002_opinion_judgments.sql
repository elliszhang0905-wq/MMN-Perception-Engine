create table if not exists opinion_judgments (
    id text primary key,
    creator_id text not null references creators(id),
    version integer not null,
    status text not null,
    scope text not null,
    judgment_json jsonb not null,
    model_validation_json jsonb not null,
    evidence_ids_json jsonb not null,
    created_at timestamptz not null default now(),
    unique (creator_id, version)
);

create index if not exists idx_opinion_creator_version
    on opinion_judgments(creator_id, version desc);
