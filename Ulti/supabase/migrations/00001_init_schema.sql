-- Supabase Migration: 00001_init_schema.sql
-- Description: Initialize the database schema for the Ulti Webapp

-- 1. Profiles Table (Users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    games_played INT DEFAULT 0,
    games_won INT DEFAULT 0,
    total_score INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Row Level Security (RLS) for profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public profiles are viewable by everyone." ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users can insert their own profile." ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile." ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Rooms Table
-- Stores active game rooms and their configuration/state
CREATE TYPE room_status AS ENUM ('waiting', 'playing', 'finished');

CREATE TABLE public.rooms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    host_id UUID REFERENCES public.profiles(id) NOT NULL,
    name TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    password_hash TEXT, -- Null if public
    status room_status DEFAULT 'waiting' NOT NULL,
    player1_id UUID REFERENCES public.profiles(id) NOT NULL, -- The host
    player2_id UUID REFERENCES public.profiles(id),
    player3_id UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Row Level Security (RLS) for rooms
ALTER TABLE public.rooms ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Rooms are viewable by everyone." ON public.rooms FOR SELECT USING (true);
-- Anyone authenticated can create a room
CREATE POLICY "Authenticated users can create rooms." ON public.rooms FOR INSERT WITH CHECK (auth.role() = 'authenticated');
-- Only host or players in the room can update it
CREATE POLICY "Players in the room can update it." ON public.rooms FOR UPDATE USING (
    auth.uid() = player1_id OR auth.uid() = player2_id OR auth.uid() = player3_id
);

-- 3. Games Table
-- Represents a single play (osztás) within a room
CREATE TYPE game_status AS ENUM ('dealing', 'bidding', 'playing', 'finished');

CREATE TABLE public.games (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    room_id UUID REFERENCES public.rooms(id) ON DELETE CASCADE NOT NULL,
    dealer_id UUID REFERENCES public.profiles(id) NOT NULL,
    active_player_id UUID REFERENCES public.profiles(id) NOT NULL,
    status game_status DEFAULT 'dealing' NOT NULL,
    
    -- Game State (JSONB for flexibility, since it updates frequently and contains array of cards)
    -- E.g. { "hands": { "player1_id": ["piros_asz", ...], ... }, "talon": ["zold_vii", "tok_also"] }
    -- We keep the hands hidden from the client via API, the database stores the truth.
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Current Bid (Vállalás)
    -- E.g. { "type": "ulti", "value": 4, "player_id": "...", "doubles": [] }
    current_bid JSONB,
    
    -- Trump suit (Adu szín: Tök, Zöld, Piros, Makk, vagy null ha színnélküli)
    trump_suit TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Row Level Security (RLS) for games
-- Important: Clients shouldn't read the raw state if the hands are there!
-- Usually, we let clients read the game, but the actual hands are NOT in this state column IF we want full security,
-- OR we use a database function to strip other players' hands before returning.
-- For a hobby project, RLS can just allow players in the room to read it.
ALTER TABLE public.games ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Players in the room can view the game." ON public.games FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.rooms r 
        WHERE r.id = games.room_id AND (auth.uid() = r.player1_id OR auth.uid() = r.player2_id OR auth.uid() = r.player3_id)
    )
);
-- We might not want clients to directly update the game state, only via Edge Functions / API routes.
-- If we use next.js serverless functions (API routes) with a Service Role key, we don't need update policies here for the clients.

-- 4. Tricks Table (Ütések)
-- Logs every trick played for replay and validation
CREATE TABLE public.tricks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    game_id UUID REFERENCES public.games(id) ON DELETE CASCADE NOT NULL,
    trick_number INT NOT NULL CHECK (trick_number >= 1 AND trick_number <= 10),
    lead_player_id UUID REFERENCES public.profiles(id) NOT NULL,
    winner_player_id UUID REFERENCES public.profiles(id),
    
    -- The cards played in this trick
    -- E.g. { "player1_id": "piros_asz", "player2_id": "piros_x", ... }
    cards_played JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.tricks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Players in the room can view tricks." ON public.tricks FOR SELECT USING (
    EXISTS (
         SELECT 1 FROM public.games g
         JOIN public.rooms r ON g.room_id = r.id
         WHERE g.id = tricks.game_id AND (auth.uid() = r.player1_id OR auth.uid() = r.player2_id OR auth.uid() = r.player3_id)
    )
);

-- Enable Realtime for specific tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.rooms;
ALTER PUBLICATION supabase_realtime ADD TABLE public.games;
ALTER PUBLICATION supabase_realtime ADD TABLE public.tricks;
