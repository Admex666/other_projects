-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)

-- Wardrobe Items table
CREATE TABLE IF NOT EXISTS wardrobe_items (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  image_urls  TEXT[] DEFAULT '{}',
  category    TEXT NOT NULL,
  color       TEXT,
  fabric      TEXT,
  tags        TEXT[] DEFAULT '{}',
  is_archived BOOLEAN DEFAULT false,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- RLS: Enable row-level security
ALTER TABLE wardrobe_items ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see and edit their own items
CREATE POLICY "Users can CRUD their own wardrobe items"
  ON wardrobe_items
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Outfits table
CREATE TABLE IF NOT EXISTS outfits (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  item_ids         UUID[] DEFAULT '{}',
  name             TEXT,
  confidence_score INTEGER,
  rationale        TEXT,
  context          JSONB DEFAULT '{}',
  created_at       TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE outfits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD their own outfits"
  ON outfits
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- History table
CREATE TABLE IF NOT EXISTS history (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  outfit_id      UUID REFERENCES outfits(id) ON DELETE SET NULL,
  worn_date      DATE NOT NULL DEFAULT CURRENT_DATE,
  feedback_score INTEGER CHECK (feedback_score BETWEEN 1 AND 5)
);

ALTER TABLE history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD their own history"
  ON history
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Storage bucket: wardrobe-images (create via Dashboard or run:)
-- insert into storage.buckets (id, name, public) values ('wardrobe-images', 'wardrobe-images', true);

-- Storage RLS: users can only upload to their own folder
CREATE POLICY "Users upload to their own folder"
  ON storage.objects
  FOR INSERT
  WITH CHECK (bucket_id = 'wardrobe-images' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Public read of wardrobe images"
  ON storage.objects
  FOR SELECT
  USING (bucket_id = 'wardrobe-images');

CREATE POLICY "Users can delete their own images"
  ON storage.objects
  FOR DELETE
  USING (bucket_id = 'wardrobe-images' AND (storage.foldername(name))[1] = auth.uid()::text);
