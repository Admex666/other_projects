export type StageId = 'teaser' | 'intro' | 'billiard' | 'food' | 'bar1' | 'bar2' | 'bar3' | 'finale';

export type ProximityState = 'freezing' | 'cold' | 'warm' | 'hot' | 'burning';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface FoodOption {
  id: string;
  title: string;
  category: string;
  description: string;
  badge: string;
  image: string;
  venueName: string;
  venueAddress?: string;
  mapsUrl: string;
  targetLocation: Coordinates;
}

export interface BarOption {
  id: string;
  mysteryPhrase: string;
  note?: string;
  venueName: string;
  venueAddress?: string;
  mapsUrl?: string;
  targetLocation: Coordinates; // coordinates [lat, lng]
}

export interface BarStageConfig {
  id: 'bar1' | 'bar2' | 'bar3';
  title: string;
  riddle: string;
  options: BarOption[];
}

export interface QuestConfig {
  meta: {
    birthdayPerson: string;
    turningAge: number;
    year: number;
    title: string;
    subtitle: string;
    eventDate: string;
  };
  security: {
    unlockCode: string; // PLACEHOLDER
    allowOverride: boolean;
  };
  stages: {
    teaser: {
      title: string;
      lockedMessage: string;
      hint: string;
    };
    intro: {
      title: string;
      briefing: string[];
      rules: string[];
      inventory: string[];
    };
    billiard: {
      title: string;
      venueName: string;
      venueAddress?: string;
      meetingTime: string;
      targetLocation: Coordinates;
      description: string;
      faceScan: {
        title: string;
        subtitle: string;
        imagePath: string;
        soundPath: string;
        identifiedName: string;
        caption: string;
      };
    };
    food: {
      title: string;
      introText: string;
      options: FoodOption[];
    };
    bars: {
      thresholdsMeters: {
        burning: number;
        hot: number;
        warm: number;
        cold: number;
      };
      stages: BarStageConfig[];
    };
    finale: {
      title: string;
      celebrationTitle: string;
      message: string[];
      badges: {
        title: string;
        icon: string;
        desc: string;
      }[];
    };
  };
}

export interface QuestState {
  isUnlocked: boolean;
  currentStageId: StageId;
  stageHistory: StageId[];
  isBilliardUnlockedByScan: boolean;
  selectedFoodId: string | null;
  selectedBarIds: Record<string, string>; // e.g. { bar1: 'bar1_opt1', bar2: 'bar2_opt1', ... }
  unlockedBarClueCount: number;
  soundEnabled: boolean;
  devModeEnabled: boolean;
  simulatedDistance: number | null;
  simulatedHeading: number | null;
}
