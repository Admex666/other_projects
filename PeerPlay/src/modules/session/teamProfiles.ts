// Canonical V2 Team Archetypes (The Trading Game V2)
export interface TeamProfileDefinition {
  profileCode: 'CAPITAL' | 'RESOURCE' | 'TECH' | 'EMERGING';
  name: string;
  cashBalance: number;
  paperSheets: number;
  scissorsCount: number;
  rulersCount: number;
  templatesCount: number;
  description: string;
}

export const TEAM_ARCHETYPES: TeamProfileDefinition[] = [
  {
    profileCode: 'CAPITAL',
    name: 'Tőkeerős Vállalat (Capital Rich)',
    cashBalance: 1500,
    paperSheets: 2,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
    description: 'Bőséges tőke, de eszközök és alapanyag nélkül. Vásárolnia vagy bérelnie kell.',
  },
  {
    profileCode: 'RESOURCE',
    name: 'Nyersanyag-óriás (Resource Rich)',
    cashBalance: 200,
    paperSheets: 15,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
    description: 'Rengeteg papír, minimális tőke és nulla eszköz. Nyersanyagot kell eladnia.',
  },
  {
    profileCode: 'TECH',
    name: 'Technológiai Bajnok (Tech Leader)',
    cashBalance: 300,
    paperSheets: 3,
    scissorsCount: 2,
    rulersCount: 2,
    templatesCount: 2,
    description: 'Kiváló eszközök és sablonok, de szűkös nyersanyag. Bérgyártó vagy eszközbérbeadó.',
  },
  {
    profileCode: 'EMERGING',
    name: 'Feltörekvő Start-up (Emerging Team)',
    cashBalance: 500,
    paperSheets: 5,
    scissorsCount: 1,
    rulersCount: 1,
    templatesCount: 0,
    description: 'Vegyes, de korlátozott induló készlet. Gyors szövetségkötésre kényszerül.',
  },
];

export const TEAM_PROFILES = TEAM_ARCHETYPES;

