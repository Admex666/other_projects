export type StageId = 'teaser' | 'intro' | 'bowling' | 'food' | 'bar' | 'finale';

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
  venueAddress: string;
  mapsUrl: string;
  targetLocation: Coordinates; // PLACEHOLDER coordinates
}

export interface BarOption {
  id: string;
  mysteryPhrase: string;
  note: string;
  venueName: string;
  venueAddress: string;
  mapsUrl: string;
  targetLocation: Coordinates; // DUMMY coordinates [lat, lng]
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
    bowling: {
      title: string;
      venueName: string;
      venueAddress: string;
      meetingTime: string;
      description: string;
      challenge: {
        goalText: string;
        targetStrikes: number;
      };
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
    bar: {
      title: string;
      riddle: string;
      options: BarOption[];
      thresholdsMeters: {
        burning: number;
        hot: number;
        warm: number;
        cold: number;
      };
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
  isBowlingUnlockedByScan: boolean;
  selectedFoodId: string | null;
  selectedBarId: string | null;
  bowlingStrikesCount: number;
  unlockedBarClueCount: number;
  soundEnabled: boolean;
  devModeEnabled: boolean;
  simulatedDistance: number | null;
  simulatedHeading: number | null;
}
