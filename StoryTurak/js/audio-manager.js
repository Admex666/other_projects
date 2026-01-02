export class AudioManager {
    constructor() {
        this.bgm = null; // Background Music / Ambience
        this.sfx = null; // Sound Effects / Voiceover
        this.isMuted = false;
        this.fadeDuration = 1000;
    }

    playAmbience(url) {
        if (this.bgm && this.bgm.src.includes(url)) return; // Already playing

        if (this.bgm) {
            this.fadeOut(this.bgm, () => {
                this.bgm = this._createAudio(url, true);
                this.fadeIn(this.bgm);
            });
        } else {
            this.bgm = this._createAudio(url, true);
            this.fadeIn(this.bgm);
        }
    }

    playVoiceover(url) {
        if (this.sfx) {
            this.sfx.pause();
        }
        this.sfx = this._createAudio(url, false);
        this.sfx.play().catch(e => console.warn('Audio play failed:', e));
    }

    stopAll() {
        if (this.bgm) {
            this.fadeOut(this.bgm, () => {
                this.bgm = null;
            });
        }
        if (this.sfx) {
            this.sfx.pause();
            this.sfx = null;
        }
    }

    _createAudio(url, loop) {
        const audio = new Audio(url);
        audio.loop = loop;
        audio.volume = 0;
        return audio;
    }

    fadeIn(audio) {
        audio.volume = 0;
        audio.play().catch(e => console.warn('Audio play failed:', e));

        const step = 0.05;
        const interval = this.fadeDuration * step;

        const timer = setInterval(() => {
            if (audio.volume < 1 - step) {
                audio.volume += step;
            } else {
                audio.volume = 1;
                clearInterval(timer);
            }
        }, interval);
    }

    fadeOut(audio, callback) {
        const step = 0.05;
        const interval = this.fadeDuration * step;

        const timer = setInterval(() => {
            if (audio.volume > step) {
                audio.volume -= step;
            } else {
                audio.volume = 0;
                audio.pause();
                clearInterval(timer);
                if (callback) callback();
            }
        }, interval);
    }
}

export const audioManager = new AudioManager();
