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
    name: 'Alfa Vállalat',
    cashBalance: 1500,
    paperSheets: 2,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
    description: 'Alfa Vállalat induló erőforráscsomag.',
  },
  {
    profileCode: 'RESOURCE',
    name: 'Béta Vállalat',
    cashBalance: 200,
    paperSheets: 15,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
    description: 'Béta Vállalat induló erőforráscsomag.',
  },
  {
    profileCode: 'TECH',
    name: 'Gamma Vállalat',
    cashBalance: 300,
    paperSheets: 3,
    scissorsCount: 2,
    rulersCount: 2,
    templatesCount: 2,
    description: 'Gamma Vállalat induló erőforráscsomag.',
  },
  {
    profileCode: 'EMERGING',
    name: 'Delta Vállalat',
    cashBalance: 500,
    paperSheets: 5,
    scissorsCount: 1,
    rulersCount: 1,
    templatesCount: 0,
    description: 'Delta Vállalat induló erőforráscsomag.',
  },
];

export const TEAM_PROFILES = TEAM_ARCHETYPES;
