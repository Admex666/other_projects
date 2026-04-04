import { createClient } from '@/lib/supabase/server';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest, props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const { score } = await req.json();

  if (typeof score !== 'number' || score < 1 || score > 5) {
    return NextResponse.json({ error: 'Invalid score' }, { status: 400 });
  }

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Update the outfit table directly with the user rating
  const { error } = await supabase
    .from('outfits')
    .update({ feedback_score: score })
    .eq('id', params.id)
    .eq('user_id', user.id);

  if (error) {
    console.error('Rating error:', error);
    return NextResponse.json({ error: 'Failed to save rating' }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
