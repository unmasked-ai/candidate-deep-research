-- Enable/confirm pgmq and create the agent_runs queue
create extension if not exists pgmq;
select pgmq.create('agent_runs');






