-- Extensions
create extension if not exists vector;

-- Basic enums
create type run_status as enum ('queued','running','succeeded','failed','cancelled');

-- Core tables
create table public.agents (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  kind text not null,                    -- e.g. "orchestrator" | "candidate-research" | "company-research"
  config jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table public.companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  website text,
  profile jsonb not null default '{}',
  embedding vector(1536),                -- adjust to your model
  created_at timestamptz not null default now()
);

create table public.candidates (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  linkedin_url text,
  github_url text,
  cv_url text,
  profile jsonb not null default '{}',
  embedding vector(1536),
  created_at timestamptz not null default now()
);

create table public.runs (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid references public.agents(id) on delete set null,
  candidate_id uuid references public.candidates(id) on delete set null,
  company_id uuid references public.companies(id) on delete set null,
  status run_status not null default 'queued',
  started_at timestamptz,
  finished_at timestamptz,
  error text,
  params jsonb not null default '{}',
  created_by uuid,                       -- optional: auth.user id
  created_at timestamptz not null default now()
);

create table public.messages (
  id bigserial primary key,
  run_id uuid not null references public.runs(id) on delete cascade,
  role text not null,                    -- "system" | "user" | "assistant" | "tool"
  content text,                          -- raw text
  data jsonb,                            -- structured tool calls / traces
  token_count int,
  created_at timestamptz not null default now()
);

create table public.artifacts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.runs(id) on delete cascade,
  kind text not null,                    -- "resume-snapshot" | "company-profile" | "report" | "attachment"
  uri text,                              -- storage path or external url
  data jsonb,                            -- extra metadata
  created_at timestamptz not null default now()
);

-- Helpful indexes (vector and lookups)
create index on public.companies using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index on public.candidates using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index messages_run_created_at on public.messages(run_id, created_at desc);

-- (Optional) simple RLS off while hacking; tighten later
alter table public.agents     enable row level security;
alter table public.companies  enable row level security;
alter table public.candidates enable row level security;
alter table public.runs       enable row level security;
alter table public.messages   enable row level security;
alter table public.artifacts  enable row level security;

-- Open policies for service role / development (lock down before demo)
create policy dev_read_all on public.runs for select using (true);
create policy dev_ins_all  on public.runs for insert with check (true);
create policy dev_upd_all  on public.runs for update using (true);






