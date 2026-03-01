-- Supabase Migration: 00002_user_profile_trigger.sql
-- Cél: Automatikusan létrehozni egy sort a 'public.profiles' táblában, amint egy új felhasználó regisztrál az 'auth.users' táblába.

-- 1. Függvény létrehozása, ami végrehajtja az insert-et
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, username)
  VALUES (
     new.id,
     COALESCE(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1)) -- Ha nincs username megadva, az email elejét használjuk
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Trigger beállítása, ami figyeli az auth.users táblát
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- BUGFIX a teszteléshez: Ha már regisztráltál játékosokat, de nincsen profiljuk, ezzel visszamenőleg beszúrjuk őket:
INSERT INTO public.profiles (id, username)
SELECT id, COALESCE(raw_user_meta_data->>'username', split_part(email, '@', 1))
FROM auth.users
WHERE id NOT IN (SELECT id FROM public.profiles)
ON CONFLICT (id) DO NOTHING;
