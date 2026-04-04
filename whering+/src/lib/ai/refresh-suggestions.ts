import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function generateRefreshSuggestion(
  items: { category: string; color: string; fabric?: string }[],
  context: string
) {
  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash-latest' }, { apiVersion: 'v1beta' } as any);

  const prompt = `
    The user has worn this outfit 3 times in 10 days for ${context}:
    ${items.map(i => `- ${i.color} ${i.category} (${i.fabric || 'unknown'})`).join('\n')}

    Provide ONE short, creative suggestion (max 15 words) to "break the loop" by swapping ONE item or adding an accessory.
    Focus on making it feel fresh and different.
  `;

  try {
    const result = await model.generateContent(prompt);
    return result.response.text().trim();
  } catch (error) {
    console.error('Failed to generate refresh suggestion', error);
    return "Try swapping your shoes or adding a statement accessory to mix things up!";
  }
}
