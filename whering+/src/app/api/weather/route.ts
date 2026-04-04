import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const lat = searchParams.get('lat');
  const lon = searchParams.get('lon');

  if (!lat || !lon) {
    return NextResponse.json({ error: 'lat and lon required' }, { status: 400 });
  }

  const apiKey = process.env.OPENWEATHERMAP_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'Weather API not configured' }, { status: 503 });
  }

  try {
    const weatherUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`;
    const res = await fetch(weatherUrl, { next: { revalidate: 1800 } }); // Cache 30 min

    if (!res.ok) {
      throw new Error(`OpenWeatherMap error: ${res.status}`);
    }

    const data = await res.json();

    return NextResponse.json({
      temp: Math.round(data.main.temp),
      feels_like: Math.round(data.main.feels_like),
      description: data.weather[0].description,
      icon: data.weather[0].icon,
      city: data.name,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to fetch weather';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
