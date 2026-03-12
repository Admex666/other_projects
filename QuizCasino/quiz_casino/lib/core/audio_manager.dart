import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

class AudioManager {
  static final AudioManager _instance = AudioManager._internal();
  factory AudioManager() => _instance;

  AudioManager._internal();

  final AudioPlayer _sfxPlayer = AudioPlayer();
  final AudioPlayer _tickPlayer = AudioPlayer();

  bool _isMuted = false;

  Future<void> init() async {
    await _sfxPlayer.setVolume(1.0);
    await _sfxPlayer.setReleaseMode(ReleaseMode.stop);

    await _tickPlayer.setVolume(0.5);
    await _tickPlayer.setReleaseMode(ReleaseMode.stop);
  }

  void toggleMute() {
    _isMuted = !_isMuted;
  }

  Future<void> playClick() async {
    _playSfx('sounds/click.wav');
  }

  Future<void> playTick() async {
    if (_isMuted) return;
    try {
      if (_tickPlayer.state == PlayerState.playing) {
        await _tickPlayer.stop();
      }
      await _tickPlayer.play(AssetSource('sounds/tick.wav'));
    } catch (e) {
      debugPrint("Error playing tick sound: $e");
    }
  }

  Future<void> playWin() async {
    _playSfx('sounds/win.wav');
  }

  Future<void> playLose() async {
    _playSfx('sounds/lose.mp3');
  }

  Future<void> playCash() async {
    _playSfx('sounds/cash.wav');
  }

  Future<void> _playSfx(String source) async {
    if (_isMuted) return;
    try {
      if (_sfxPlayer.state == PlayerState.playing) {
        await _sfxPlayer.stop();
      }
      await _sfxPlayer.play(AssetSource(source), volume: 0.8);
    } catch (e) {
      debugPrint("Error playing sound $source: $e");
    }
  }
}
