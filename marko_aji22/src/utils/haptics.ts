/**
 * Mobile vibration haptics helper
 */
export function triggerHaptic(type: 'light' | 'medium' | 'success' | 'warning' | 'error' = 'light') {
  if (typeof navigator === 'undefined' || !navigator.vibrate) return;

  try {
    switch (type) {
      case 'light':
        navigator.vibrate(15);
        break;
      case 'medium':
        navigator.vibrate(35);
        break;
      case 'success':
        navigator.vibrate([30, 40, 60]);
        break;
      case 'warning':
        navigator.vibrate([60, 50, 60]);
        break;
      case 'error':
        navigator.vibrate([80, 50, 80, 50, 100]);
        break;
    }
  } catch {
    // Vibration might not be supported or blocked
  }
}
