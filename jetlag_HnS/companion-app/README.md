# Jet Lag Companion App - Phase 5 Complete

This is a web-based companion application for **Jet Lag: The Game - Hide + Seek**, built with React, Vite, and Tailwind CSS.
It is designed to be "Desktop-First" as requested.

## Features

1.  **Lobby**: Role selection (Hider / Seeker).
2.  **The Grid**: 
    *   Interactive Map (Leaflet) with Dark Mode.
    *   Real-time Geolocation tracking.
    *   **Station POIs**: View stations and set "Hiding Spot" (Hider only).
3.  **Hider Deck**:
    *   Draw cards logic (Draw 3, Pick 1).
    *   Hand management.
    *   Parsed directly from the provided Excel data.
4.  **Investigation Tools**:
    *   Seeker questions interface (Radar, Thermometer, etc.).
    *   Smart parameter selection.
5.  **Communication**:
    *   In-app Chat Drawer.
    *   Activity Feed (logs game events and questions).
    *   Photo sharing (local preview).

## Setup

1.  **Install Dependencies**:
    ```bash
    npm install
    ```
2.  **Run Development Server**:
    ```bash
    npm run dev
    ```
3.  **App Access**:
    Open `http://localhost:5173` in your browser.

## Configuration

*   **Firebase**: The app currently uses a placeholder `firebase.js`. To enable real cloud syncing:
    1.  Create a project at [console.firebase.google.com](https://console.firebase.google.com).
    2.  Enable Firestore and Auth.
    3.  Copy your config keys into `src/firebase.js`.
*   **Data**: Game data is in `src/data/` (JSON format), converted from the original Excel file.

## Architecture

*   **Framework**: React + Vite
*   **Styling**: Tailwind CSS (v3) + Lucide Icons
*   **State**: React Context API (`GameContext`) for global game state (Role, Hand, Logs, Chat).
*   **Map**: React-Leaflet (OpenStreetMap/CartoDB tiles).

## Next Steps (Future)

*   Connect `GameContext` to Firestore `onSnapshot` for real-time multiplayer syncing.
*   Implement "Curse" mechanics fully.
*   Add authentication (Google Login).
