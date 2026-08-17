/**
 * Web Audio API synthesizer + Custom Audio File loader for offline/online SFX
 */
class SoundEffects {
  private ctx: AudioContext | null = null;
  public enabled: boolean = true;

  private initCtx() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  /**
   * Attempts to play a custom audio file (e.g. /sounds/arrival.mp3).
   * If not found or blocked, falls back automatically to synthesized fanfare.
   */
  playCustomAudio(soundPath: string, fallbackSynthFn?: () => void) {
    if (!this.enabled) return;

    try {
      const audio = new Audio(soundPath);
      audio.play().catch(() => {
        // Fallback to synthesizer if file does not exist or cannot be played
        if (fallbackSynthFn) {
          fallbackSynthFn();
        }
      });
    } catch {
      if (fallbackSynthFn) {
        fallbackSynthFn();
      }
    }
  }

  // Tactical click / tap sound
  playClick() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.05);

      gain.gain.setValueAtTime(0.15, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.05);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.05);
    } catch {
      // Audio context might be restricted before interaction
    }
  }

  // Stage unlock / positive chime
  playUnlock() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
      notes.forEach((freq, index) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, this.ctx!.currentTime + index * 0.08);

        gain.gain.setValueAtTime(0, this.ctx!.currentTime + index * 0.08);
        gain.gain.linearRampToValueAtTime(0.2, this.ctx!.currentTime + index * 0.08 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx!.currentTime + index * 0.08 + 0.35);

        osc.connect(gain);
        gain.connect(this.ctx!.destination);

        osc.start(this.ctx!.currentTime + index * 0.08);
        osc.stop(this.ctx!.currentTime + index * 0.08 + 0.35);
      });
    } catch {
      // Ignored
    }
  }

  // Destination Arrival Victory Sound (plays custom /sounds/arrival.mp3 with rich synth fallback)
  playArrivalVictory() {
    if (!this.enabled) return;

    this.playCustomAudio('/sounds/arrival.mp3', () => {
      try {
        this.initCtx();
        if (!this.ctx) return;

        // Triumphant RPG / Quest complete chords: C Maj -> F Maj -> G Maj -> C Maj (Octave up)
        const chords = [
          { notes: [523.25, 659.25, 783.99], time: 0, duration: 0.18 },      // C5 chord
          { notes: [587.33, 698.46, 880.00], time: 0.18, duration: 0.18 },   // Dm chord
          { notes: [659.25, 783.99, 987.77], time: 0.36, duration: 0.22 },   // Em chord
          { notes: [783.99, 987.77, 1174.66], time: 0.58, duration: 0.22 },  // G5 chord
          { notes: [1046.50, 1318.51, 1567.98], time: 0.80, duration: 0.65 } // C6 High Victory
        ];

        chords.forEach(({ notes, time, duration }) => {
          notes.forEach((freq) => {
            const osc = this.ctx!.createOscillator();
            const gain = this.ctx!.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, this.ctx!.currentTime + time);

            gain.gain.setValueAtTime(0.01, this.ctx!.currentTime + time);
            gain.gain.linearRampToValueAtTime(0.18, this.ctx!.currentTime + time + 0.03);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx!.currentTime + time + duration);

            osc.connect(gain);
            gain.connect(this.ctx!.destination);

            osc.start(this.ctx!.currentTime + time);
            osc.stop(this.ctx!.currentTime + time + duration);
          });
        });
      } catch {
        // Ignored
      }
    });
  }

  // Error buzz
  playError() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(150, this.ctx.currentTime);
      osc.frequency.linearRampToValueAtTime(110, this.ctx.currentTime + 0.2);

      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.2);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.2);
    } catch {
      // Ignored
    }
  }

  // Radar ping beep
  playRadarPing(proximity: 'freezing' | 'cold' | 'warm' | 'hot' | 'burning') {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const freqMap = {
        freezing: 350,
        cold: 450,
        warm: 600,
        hot: 850,
        burning: 1200
      };

      const freq = freqMap[proximity];
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.15);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.15);
    } catch {
      // Ignored
    }
  }

  // Grand celebratory fanfare
  playVictoryFanfare() {
    if (!this.enabled) return;

    this.playCustomAudio('/sounds/victory.mp3', () => {
      try {
        this.initCtx();
        if (!this.ctx) return;

        const melody = [
          { f: 523.25, d: 0.15 },
          { f: 523.25, d: 0.15 },
          { f: 523.25, d: 0.15 },
          { f: 659.25, d: 0.4 },
          { f: 783.99, d: 0.2 },
          { f: 1046.5, d: 0.6 }
        ];

        let t = this.ctx.currentTime;
        melody.forEach(note => {
          const osc = this.ctx!.createOscillator();
          const gain = this.ctx!.createGain();

          osc.type = 'triangle';
          osc.frequency.setValueAtTime(note.f, t);

          gain.gain.setValueAtTime(0.2, t);
          gain.gain.exponentialRampToValueAtTime(0.01, t + note.d);

          osc.connect(gain);
          gain.connect(this.ctx!.destination);

          osc.start(t);
          osc.stop(t + note.d);

          t += note.d * 0.9;
        });
      } catch {
        // Ignored
      }
    });
  }
}

export const sound = new SoundEffects();
