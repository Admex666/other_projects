import { GoogleGenerativeAI, Part } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// genAI is initialized inside the POST handler for better env safety

interface ValidateOutfitRequest {
  itemIds: string[];
  context: {
    eventType: string;   // e.g. "office meeting", "casual day", "formal dinner"
    weather?: {
      temp: number;       // Celsius
      description: string; // e.g. "light rain", "sunny"
    };
  };
}

export async function POST(req: NextRequest) {
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Gemini API key is not configured in .env.local' }, { status: 503 });
    }

    // Auth check
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel(
      { model: 'gemini-1.5-flash-latest' },
      { apiVersion: 'v1beta' } as any
    );

    // Debugging: If this fails again, let's see what models are actually available
    if (process.env.NODE_ENV === 'development') {
      try {
        const models = await genAI.listModels();
        console.log('[DEBUG] Available Gemini Models:', models.models.map(m => m.name));
      } catch (e) {
        console.error('[DEBUG] Failed to list models', e);
      }
    }

    const body: ValidateOutfitRequest = await req.json();
    const { itemIds, context } = body;

    if (!itemIds || itemIds.length === 0) {
      return NextResponse.json({ error: 'No outfit items provided' }, { status: 400 });
    }

    // Fetch item details from Supabase
    const { data: items, error: fetchError } = await supabase
      .from('wardrobe_items')
      .select('id, category, color, fabric, tags, image_urls')
      .in('id', itemIds)
      .eq('user_id', user.id);

    if (fetchError || !items) {
      return NextResponse.json({ error: 'Failed to fetch wardrobe items' }, { status: 500 });
    }

    // Build the outfit description for the AI
    const outfitDescription = items.map(item =>
      `- ${item.category} (${item.color ?? 'unknown colour'}, ${item.fabric ?? 'unknown fabric'}, tags: ${item.tags?.join(', ') || 'none'})`
    ).join('\n');

    const weatherContext = context.weather
      ? `Current weather: ${context.weather.temp}°C, ${context.weather.description}.`
      : 'Weather: unknown.';

    const prompt = `You are a professional stylist and fashion advisor. Analyse the following outfit and provide structured feedback.

OUTFIT ITEMS:
${outfitDescription}

CONTEXT:
- Event: ${context.eventType}
- ${weatherContext}

Your response must be a JSON object with EXACTLY this structure:
{
  "confidence_score": <integer from 0 to 100>,
  "headline": "<one short sentence summarising the outfit, max 10 words>",
  "rationale": "<2-3 sentences explaining why this outfit works or doesn't work for the context, referencing specific items>",
  "suggestions": [
    "<one specific actionable improvement, or null if outfit is great>"
  ],
  "strengths": [
    "<one specific strength of this outfit>"
  ]
}

Be specific, warm, and supportive in tone. Consider colour harmony, occasion appropriateness, weather suitability, and fabric choices. Respond ONLY with the raw JSON object, no markdown fences.`;

    // Build the parts array for Gemini
    // We include image URLs if available for Vision analysis
    const parts: Part[] = [{ text: prompt }];

    // If items have images, attach the first image of each for Vision analysis
    for (const item of items) {
      if (item.image_urls?.[0]) {
        try {
          const imageResp = await fetch(item.image_urls[0]);
          if (imageResp.ok) {
            const imageBuffer = await imageResp.arrayBuffer();
            const base64 = Buffer.from(imageBuffer).toString('base64');
            const contentType = imageResp.headers.get('content-type') ?? 'image/jpeg';
            parts.push({
              inlineData: {
                mimeType: contentType as 'image/jpeg' | 'image/png' | 'image/webp',
                data: base64,
              },
            });
          }
        } catch {
          // Skip image if fetch fails — fall back to text-only analysis
        }
      }
    }

    const result = await model.generateContent(parts);
    const responseText = result.response.text().trim();

    // Parse the JSON response from Gemini
    let structured;
    try {
      structured = JSON.parse(responseText);
    } catch {
      // If Gemini returned something unexpected, extract JSON from it
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return NextResponse.json({ error: 'AI returned invalid response' }, { status: 500 });
      }
      structured = JSON.parse(jsonMatch[0]);
    }

    return NextResponse.json({
      confidence_score: structured.confidence_score,
      headline: structured.headline,
      rationale: structured.rationale,
      suggestions: structured.suggestions ?? [],
      strengths: structured.strengths ?? [],
    });

  } catch (err: unknown) {
    console.error('[validate-outfit]', err);
    const message = err instanceof Error ? err.message : 'Internal server error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
