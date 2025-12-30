import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { GameProvider } from './context/GameContext';
import { DashboardLayout } from './layout/DashboardLayout';
import { Lobby } from './views/Lobby';
import { TheGrid } from './views/TheGrid';
import { DeckView } from './views/DeckView';
import { Settings } from './views/Settings';

const router = createBrowserRouter([
  {
    path: "/",
    element: <DashboardLayout />,
    children: [
      {
        index: true,
        element: <TheGrid />,
      },
      {
        path: "lobby",
        element: <Lobby />,
      },
      {
        path: "deck",
        element: <DeckView />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
    ],
  },
]);

function App() {
  return (
    <GameProvider>
      <RouterProvider router={router} />
    </GameProvider>
  );
}

export default App;
