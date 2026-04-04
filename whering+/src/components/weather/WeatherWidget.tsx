'use client';

import { useState, useEffect, useRef } from 'react';
import { Cloud, Sun, CloudRain, CloudSnow, Wind, Thermometer } from 'lucide-react';

interface WeatherData {
  temp: number;
  feels_like: number;
  description: string;
  icon: string;
  city: string;
}

interface WeatherContextProps {
  onWeatherLoad?: (weather: WeatherData) => void;
  compact?: boolean;
}

function getWeatherIcon(iconCode: string, size = 14) {
  if (iconCode.startsWith('01') || iconCode.startsWith('02')) return <Sun size={size} />;
  if (iconCode.startsWith('09') || iconCode.startsWith('10')) return <CloudRain size={size} />;
  if (iconCode.startsWith('13')) return <CloudSnow size={size} />;
  if (iconCode.startsWith('50')) return <Wind size={size} />;
  return <Cloud size={size} />;
}

export function WeatherWidget({ onWeatherLoad, compact = false }: WeatherContextProps) {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    
    if (!navigator.geolocation) {
      setError('Location unavailable');
      setLoading(false);
      return;
    }

    fetchedRef.current = true;

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const res = await fetch(`/api/weather?lat=${latitude}&lon=${longitude}`);
          if (!res.ok) throw new Error('Weather fetch failed');
          const data: WeatherData = await res.json();
          setWeather(data);
          onWeatherLoad?.(data);
        } catch {
          setError('Weather unavailable');
        } finally {
          setLoading(false);
        }
      },
      () => {
        setError('Location denied');
        setLoading(false);
      },
      { timeout: 8000 }
    );
  }, []); // Only run on mount

  if (loading) {
    return (
      <span style={{ color: 'var(--color-on-surface-variant)', fontFamily: 'var(--font-family-body)', fontSize: '0.8rem' }}>
        Fetching weather…
      </span>
    );
  }

  if (error || !weather) {
    return (
      <span style={{ color: 'var(--color-on-surface-variant)', fontFamily: 'var(--font-family-body)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}>
        <Cloud size={14} /> No weather data
      </span>
    );
  }

  if (compact) {
    return (
      <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-family-body)', fontSize: '0.8rem', color: 'var(--color-on-surface-variant)' }}>
        {getWeatherIcon(weather.icon)}
        <strong style={{ color: 'var(--color-on-surface)' }}>{weather.temp}°C</strong>
        <span style={{ textTransform: 'capitalize' }}>{weather.description}</span>
      </span>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-family-body)', fontSize: '0.8rem', color: 'var(--color-on-surface-variant)' }}>
        {getWeatherIcon(weather.icon)}
        <strong style={{ color: 'var(--color-on-surface)', fontSize: '1rem' }}>{weather.temp}°C</strong>
        <span style={{ textTransform: 'capitalize' }}>{weather.description}</span>
      </span>
      <span style={{ fontFamily: 'var(--font-family-body)', fontSize: '0.7rem', color: 'var(--color-on-surface-variant)' }}>
        Feels like {weather.feels_like}°C · {weather.city}
      </span>
    </div>
  );
}
