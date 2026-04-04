import { createClient } from '@/lib/supabase/server';
import { WardrobeGrid } from './WardrobeGrid';

export default async function WardrobePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: items, count } = await supabase
    .from('wardrobe_items')
    .select('id, category, color, image_urls, tags', { count: 'exact' })
    .eq('user_id', user?.id)
    .eq('is_archived', false)
    .order('created_at', { ascending: false });

  return (
    <WardrobeGrid
      items={items ?? []}
      totalCount={count ?? 0}
    />
  );
}
