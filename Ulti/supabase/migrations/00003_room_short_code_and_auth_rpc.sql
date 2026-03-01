-- Supabase Migration: 00003_room_short_code_and_auth_rpc.sql
-- 1. Add short_code to rooms
ALTER TABLE public.rooms ADD COLUMN IF NOT EXISTS short_code TEXT UNIQUE;

-- 2. Create RPC for resolving email by username for login
CREATE OR REPLACE FUNCTION public.get_email_by_username(p_username TEXT)
RETURNS TEXT AS $$
DECLARE
  v_email TEXT;
BEGIN
  SELECT u.email INTO v_email
  FROM auth.users u
  JOIN public.profiles p ON u.id = p.id
  WHERE p.username = p_username
  LIMIT 1;

  RETURN v_email;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
