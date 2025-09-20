-- Seed minimal reference data for the multi-agent demo.
-- Assumes your tables from the migration exist:
--   public.agents, public.companies, public.candidates

-- Fixed UUIDs to make local/dev predictable
-- (avoid duplicates if seed runs more than once)
insert into public.agents (id, name, kind, config)
values
  ('11111111-1111-1111-1111-111111111111','orchestrator','orchestrator','{}'),
  ('22222222-2222-2222-2222-222222222222','candidate-research','worker','{}'),
  ('33333333-3333-3333-3333-333333333333','company-research','worker','{}')
on conflict (id) do nothing;

insert into public.companies (id, name, website, profile, embedding)
values
  ('44444444-4444-4444-4444-444444444444','Hypersigma Labs','https://hypersigma.example','{"stack":["ts","nextjs","pg"],"notes":"seeded"}', null)
on conflict (id) do nothing;

insert into public.candidates (id, full_name, linkedin_url, github_url, cv_url, profile, embedding)
values
  ('55555555-5555-5555-5555-555555555555','Aisha Karim','https://linkedin.com/in/aishak','https://github.com/aishak', null,'{"skills":["go","python","agents"]}', null),
  ('66666666-6666-6666-6666-666666666666','Ben Ortega','https://linkedin.com/in/bortega','https://github.com/bortega', null,'{"skills":["ts","react","retrieval"]}', null)
on conflict (id) do nothing;






