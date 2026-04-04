import { SupabaseClient } from '@supabase/supabase-js';

export interface Repetition {
  itemIds: string[];
  count: number;
  lastWorn: string;
}

export async function detectRepetitions(supabase: SupabaseClient, userId: string): Promise<Repetition | null> {
  const tenDaysAgo = new Date();
  tenDaysAgo.setDate(tenDaysAgo.getDate() - 10);

  const { data: recentOutfits } = await supabase
    .from('outfits')
    .select('id, item_ids, created_at')
    .eq('user_id', userId)
    .gte('created_at', tenDaysAgo.toISOString())
    .order('created_at', { ascending: false });

  if (!recentOutfits || recentOutfits.length < 3) return null;

  // Hash item combinations to find repeats
  const counts = new Map<string, { count: number; lastWorn: string; itemIds: string[] }>();
  
  for (const outfit of recentOutfits) {
    const sortedIds = [...outfit.item_ids].sort().join(',');
    const existing = counts.get(sortedIds);
    if (existing) {
      existing.count += 1;
    } else {
      counts.set(sortedIds, { 
        count: 1, 
        lastWorn: outfit.created_at, 
        itemIds: outfit.item_ids 
      });
    }
  }

  // Find the most repeated combination
  let mostRepeated: Repetition | null = null;
  for (const entry of counts.values()) {
    if (entry.count >= 2) { // 2 or more times in 10 days is a "loop"
      if (!mostRepeated || entry.count > mostRepeated.count) {
        mostRepeated = entry;
      }
    }
  }

  return mostRepeated;
}
