create extension if not exists pgcrypto;

create table if not exists public.relatorios (
    id uuid primary key default gen_random_uuid(),
    data_relatorio text not null unique,
    conteudo_json jsonb not null,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

alter table public.relatorios enable row level security;

drop policy if exists "Permitir leitura dos relatorios" on public.relatorios;
create policy "Permitir leitura dos relatorios"
on public.relatorios
for select
using (true);

drop policy if exists "Permitir gravacao dos relatorios" on public.relatorios;
create policy "Permitir gravacao dos relatorios"
on public.relatorios
for insert
with check (true);

drop policy if exists "Permitir atualizacao dos relatorios" on public.relatorios;
create policy "Permitir atualizacao dos relatorios"
on public.relatorios
for update
using (true)
with check (true);
