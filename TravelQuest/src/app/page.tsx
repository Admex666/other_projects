import Image from "next/image";

export default function Home() {
  return (
    <main>
      <section className="hero">
        <Image
          src="/logo_nobg_text.png"
          alt="CityPulse Logo"
          width={220}
          height={220}
          priority
          style={{ marginBottom: '2rem', animation: 'pulse 3s infinite ease-in-out' }}
        />
        <h1 className="title">
          The City is Your <span>Playground</span>
        </h1>
        <p className="subtitle">
          Turn boring city exploration into a game. Join missions, beat the timer, and compete with others, while exploring any city.
        </p>
        <button
          data-tally-open="5Bvpjv"
          data-tally-layout="modal"
          data-tally-emoji-text="👋"
          data-tally-emoji-animation="wave"
          className="cta-button"
        >
          Let me take a look
        </button>
      </section>

      <div style={{ textAlign: 'center', paddingTop: '8rem', marginBottom: '-6rem' }}>
        <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 900, textTransform: 'uppercase' }}>
          <span>Some of the Missions</span>
        </h2>
      </div>
      <section className="features">
        <div className="card">
          <div className="card-icon">🚆</div>
          <h3 className="card-title">Transit Dash</h3>
          <p className="card-text">
            Maximize your trajectory. Use public transport to hit as many targets as possible within 60 minutes. Every ride counts.
          </p>
        </div>
        <div className="card">
          <div className="card-icon">🕵️</div>
          <h3 className="card-title">Hide & Seek</h3>
          <p className="card-text">
            Stay off the radar. Use clues to find your friends or hide in plain sight at iconic landmarks.
          </p>
        </div>
        <div className="card">
          <div className="card-icon">⚡</div>
          <h3 className="card-title">Mystery Quests</h3>
          <p className="card-text">
            Get spontaneous. Every 15 minutes, the city throws a new challenge at you. Decipher clues and act fast.
          </p>
        </div>
      </section>

      <section className="comparison" style={{ background: 'var(--card-bg)', paddingBottom: '10rem' }}>
        <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 900, marginBottom: '4rem', textTransform: 'uppercase' }}>
          Experience the <span>Game</span>
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '2rem',
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 1rem'
        }}>
          <div style={{ borderRadius: '1.5rem', overflow: 'hidden', border: '1px solid var(--border)', background: '#000' }}>
            <Image
              src="/shot_1.2.png"
              alt="Quest Selection"
              width={400}
              height={800}
              style={{ width: '100%', height: 'auto' }}
              priority
            />
          </div>
          <div style={{ borderRadius: '1.5rem', overflow: 'hidden', border: '1px solid var(--border)', background: '#000' }}>
            <Image
              src="/shot_2.3.png"
              alt="Active Map"
              width={400}
              height={800}
              style={{ width: '100%', height: 'auto' }}
              priority
            />
          </div>
          <div style={{ borderRadius: '1.5rem', overflow: 'hidden', border: '1px solid var(--border)', background: '#000' }}>
            <Image
              src="/shot_3.3.png"
              alt="Victory Screen"
              width={400}
              height={800}
              style={{ width: '100%', height: 'auto' }}
              priority
            />
          </div>
        </div>
      </section>

      <footer className="footer">
        <p>&copy; 2026 CityPulse. All rights reserved. Created for the urban adventurers.</p>
        <p style={{ marginTop: '1rem', opacity: 0.5 }}>Currently in development for any city worldwide.</p>
      </footer>
    </main>
  );
}
