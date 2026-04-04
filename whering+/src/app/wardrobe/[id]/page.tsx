import { notFound } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { ItemDetailClient } from './ItemDetailClient';

export default async function ItemPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return null; // Handled by middleware/proxy
  }

  const { data: item, error } = await supabase
    .from('wardrobe_items')
    .select('*')
    .eq('id', params.id)
    .eq('user_id', user.id)
    .single();

  if (error || !item) {
    notFound();
  }

  return <ItemDetailClient item={item} />;
}
