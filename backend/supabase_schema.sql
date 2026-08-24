-- Run this once in Supabase SQL Editor before deploying the API.
create table if not exists public.app_metrics (
    name text primary key,
    value bigint not null default 0
);

insert into public.app_metrics (name, value)
values ('page_visits', 0)
on conflict (name) do nothing;

create or replace function public.increment_app_visits()
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
    next_value bigint;
begin
    update public.app_metrics
    set value = value + 1
    where name = 'page_visits'
    returning value into next_value;

    return next_value;
end;
$$;

revoke all on function public.increment_app_visits() from public;
grant execute on function public.increment_app_visits() to service_role;
