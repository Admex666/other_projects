-- ==========================================
-- VITASTEPS SUPABASE DATABASE SCHEMA (UPDATED 2026-07-17)
-- Normalized Schema: Google Sheets removed as datastore
-- ==========================================

-- 1. Create the 'runners' table (Personal identity & details)
create table if not exists public.runners (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  name text,
  phone text,
  billing_name text,
  billing_address text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on runners
alter table public.runners enable row level security;

-- Create policies for runners
create policy "Users can view their own profile" on public.runners
  for select using (auth.jwt() ->> 'email' = email);

create policy "Allow all actions for service role on runners" on public.runners
  for all using (true);


-- 2. Create the 'orders' table (Stripe transactions)
create table if not exists public.orders (
  id uuid default gen_random_uuid() primary key,
  runner_id uuid references public.runners(id) on delete cascade,
  stripe_session_id text unique not null,
  stripe_payment_status text,
  amount_total integer,
  currency text default 'HUF',
  campaign text,
  is_test boolean default false,
  billing_name text,
  billing_email text,
  billing_address text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on orders
alter table public.orders enable row level security;

-- Create policies for orders
create policy "Users can view their own orders" on public.orders
  for select using (
    exists (
      select 1 from public.runners 
      where public.runners.id = public.orders.runner_id 
      and auth.jwt() ->> 'email' = public.runners.email
    )
  );

create policy "Allow all actions for service role on orders" on public.orders
  for all using (true);


-- 3. Create the 'runs' table (Challenge entries)
create table if not exists public.runs (
  id uuid default gen_random_uuid() primary key,
  runner_id uuid references public.runners(id) on delete cascade,
  order_id uuid references public.orders(id) on delete set null,
  name text,
  completed boolean default false,
  completion_date text,
  shipped boolean default false,
  received_date text,
  serial_number text unique,
  distance_km numeric,
  campaign text,
  is_test boolean default false,
  proof_submitted boolean default false,
  proof_urls text[] default '{}'::text[],
  proof_submitted_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  -- Legacy columns (kept for compatibility until migration complete)
  stripe_session_id text,
  referred_by text
);

-- Enable RLS on runs
alter table public.runs enable row level security;

-- Create policies for runs
create policy "Users can view their own runs" on public.runs
  for select using (
    exists (
      select 1 from public.runners 
      where public.runners.id = public.runs.runner_id 
      and auth.jwt() ->> 'email' = public.runners.email
    )
  );

create policy "Users can view runs they referred" on public.runs
  for select using (
    referred_by = auth.jwt() ->> 'email'
  );

create policy "Allow all actions for service role on runs" on public.runs
  for all using (true);


-- 4. Create the 'shipments' table (Shipping details)
create table if not exists public.shipments (
  id uuid default gen_random_uuid() primary key,
  run_id uuid references public.runs(id) on delete cascade,
  method text,
  phone text,
  parcel_id text,
  parcel_name text,
  parcel_address text,
  home_address text,
  shipped boolean default false,
  shipped_at timestamp with time zone,
  received boolean default false,
  received_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on shipments
alter table public.shipments enable row level security;

-- Create policies for shipments
create policy "Users can view their own shipments" on public.shipments
  for select using (
    exists (
      select 1 from public.runs
      join public.runners on public.runners.id = public.runs.runner_id
      where public.runs.id = public.shipments.run_id
      and auth.jwt() ->> 'email' = public.runners.email
    )
  );

create policy "Allow all actions for service role on shipments" on public.shipments
  for all using (true);


-- 5. Create the 'feedbacks' table (NPS and reviews linked via runner_id)
create table if not exists public.feedbacks (
  id uuid default gen_random_uuid() primary key,
  runner_id uuid references public.runners(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  erem_minoseg integer check (erem_minoseg >= 1 and erem_minoseg <= 5),
  szallitas_elegedett integer check (szallitas_elegedett >= 1 and szallitas_elegedett <= 5),
  reszvetel_ujra text,
  nps_score integer check (nps_score >= 0 and nps_score <= 10),
  kovetkezo_tajegyseg text,
  tetszett_legjobban text,
  jobba_tenne text,
  photo_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on feedbacks
alter table public.feedbacks enable row level security;

-- Create policies for feedbacks
create policy "Users can insert their own feedback" on public.feedbacks
  for insert with check (
    exists (
      select 1 from public.runners
      where public.runners.id = public.feedbacks.runner_id
      and auth.jwt() ->> 'email' = public.runners.email
    )
  );

create policy "Users can view their own feedback" on public.feedbacks
  for select using (
    exists (
      select 1 from public.runners
      where public.runners.id = public.feedbacks.runner_id
      and auth.jwt() ->> 'email' = public.runners.email
    )
  );


-- 6. Storage Bucket Policies (medals bucket)
create policy "Allow authenticated uploads to medals" on storage.objects
  for insert with check (
    bucket_id = 'medals' 
    and auth.role() = 'authenticated'
  );

create policy "Allow public read access to medals" on storage.objects
  for select using (bucket_id = 'medals');
