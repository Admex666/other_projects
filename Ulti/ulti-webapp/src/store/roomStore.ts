import { create } from 'zustand'

export type RoomStatus = 'waiting' | 'playing' | 'finished'

export interface Room {
    id: string
    short_code: string
    name: string
    host_id: string
    is_private: boolean
    status: RoomStatus
    player1_id: string
    player2_id: string | null
    player3_id: string | null
}

interface RoomState {
    currentRoom: Room | null
    setCurrentRoom: (room: Room | null) => void
}

export const useRoomStore = create<RoomState>((set) => ({
    currentRoom: null,
    setCurrentRoom: (room) => set({ currentRoom: room }),
}))
