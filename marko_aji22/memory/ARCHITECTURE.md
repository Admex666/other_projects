# Technical Architecture

## Stack
- **Framework:** React 18+ / Vite + TypeScript
- **Styling:** Tailwind CSS + Custom CSS Keyframe Animations + Glassmorphism tokens
- **Icons:** `lucide-react`
- **Effects:** `canvas-confetti`
- **PWA:** `vite-plugin-pwa` (ServiceWorker, Web App Manifest)

## State & Flow Management
- **`useQuestState` Hook:** Manages persistent state in `localStorage`:
  - `isUnlocked: boolean`
  - `currentStageIndex: number`
  - `completedStages: string[]`
  - `selectedFoodOption: string | null`
  - `history: LogEntry[]`
  - `debugMode: boolean`
- **`questConfig.ts`:** Single point of truth for:
  - App metadata, birthday person details ("Markó 22")
  - Unlock passcode (`PLACEHOLDER`)
  - Bowling stage details & mini-tasks
  - Food options & locations (`PLACEHOLDER`)
  - Bar/Pub GPS coordinates & navigation thresholds (`PLACEHOLDER`)
  - Custom hints, dialogues, and badges

## Navigation Subsystem
- **GPS Watcher:** Continuous or on-demand coordinates tracking.
- **Compass / DeviceOrientation:** Calculates heading delta to target bearing.
- **Hot-Cold Logic:** Computes meters to destination; categorizes into `Freezing`, `Cold`, `Warm`, `Hot`, `Burning / Arrived` with animated HUD indicators.
- **Manual / Fallback mode:** Easy check-in button or debug slider for when testing or if permissions fail.
