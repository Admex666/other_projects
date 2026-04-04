'use client';

import { useState } from 'react';
import { Cloud, Briefcase } from 'lucide-react';
import { WeatherWidget } from '@/components/weather/WeatherWidget';
import styles from './page.module.css';

const EVENT_OPTIONS = ['No event', 'Office', 'Client meeting', 'Casual', 'Formal event', 'Evening out'];

export function WeatherDashboardSection() {
  const [event, setEvent] = useState('No event');
  const [editing, setEditing] = useState(false);

  return (
    <div className={styles.contextBar}>
      <div className={styles.contextChip}>
        <Cloud size={14} />
        <WeatherWidget compact />
      </div>
      <div className={styles.contextSeparator} />
      <div className={styles.contextChip}>
        <Briefcase size={14} />
        {editing ? (
          <select
            style={{
              background: 'none',
              border: 'none',
              fontFamily: 'var(--font-family-body)',
              fontSize: '0.8rem',
              color: 'var(--color-on-surface-variant)',
              outline: 'none',
            }}
            value={event}
            onChange={(e) => { setEvent(e.target.value); setEditing(false); }}
            autoFocus
          >
            {EVENT_OPTIONS.map((o) => <option key={o}>{o}</option>)}
          </select>
        ) : (
          <span>{event}</span>
        )}
      </div>
      <button className={styles.contextAction} onClick={() => setEditing(true)}>Edit</button>
    </div>
  );
}
