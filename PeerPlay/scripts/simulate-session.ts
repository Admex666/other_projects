import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🚀 [SIMULATION] Starting PeerPlay comprehensive session data generator...')

  // 1. Get or create Organization
  let org = await prisma.organization.findFirst({
    where: { name: 'PeerPlay Demonstration Corp' },
  })
  if (!org) {
    org = await prisma.organization.create({
      data: {
        name: 'PeerPlay Demonstration Corp',
        industry: 'Management Consulting & Simulation Games',
      },
    })
    console.log('🏢 [SIMULATION] Created Organization:', org.name, org.id)
  }

  // 2. Get or create Session DEMO01
  let session = await prisma.session.findUnique({
    where: { joinCode: 'DEMO01' },
    include: { teams: true },
  })

  if (!session) {
    session = await prisma.session.create({
      data: {
        joinCode: 'DEMO01',
        name: 'Vállalati Kereskedelmi Játék & ONA Szimuláció (DEMO01)',
        organizationId: org.id,
        status: 'ACTIVE',
        currentPhase: 'PHASE_11_DEBRIEF',
        phaseStartedAt: new Date(),
        phaseDurationSeconds: 600,
        timerRemainingSeconds: 0,
        isTimerPaused: true,
      },
      include: { teams: true },
    })
    console.log('🎮 [SIMULATION] Created Session:', session.joinCode, session.id)
  } else {
    // Update to debrief phase
    await prisma.session.update({
      where: { id: session.id },
      data: {
        currentPhase: 'PHASE_11_DEBRIEF',
        status: 'ACTIVE',
      },
    })
    console.log('🎮 [SIMULATION] Using existing Session:', session.joinCode, session.id)
  }

  // 3. Ensure the 4 canonical teams exist
  const teamSpecs = [
    {
      name: 'Alfa Vállalat',
      profileCode: 'CAPITAL',
      cashBalance: 1250,
      paperSheets: 4,
      scissorsCount: 2,
      rulersCount: 1,
      templatesCount: 1,
    },
    {
      name: 'Béta Vállalat',
      profileCode: 'RESOURCE',
      cashBalance: 980,
      paperSheets: 6,
      scissorsCount: 1,
      rulersCount: 1,
      templatesCount: 0,
    },
    {
      name: 'Gamma Vállalat',
      profileCode: 'TECH',
      cashBalance: 1100,
      paperSheets: 3,
      scissorsCount: 2,
      rulersCount: 2,
      templatesCount: 2,
    },
    {
      name: 'Delta Vállalat',
      profileCode: 'EMERGING',
      cashBalance: 820,
      paperSheets: 5,
      scissorsCount: 1,
      rulersCount: 1,
      templatesCount: 1,
    },
  ]

  const teamsMap = new Map<string, any>()
  for (const spec of teamSpecs) {
    const existing = await prisma.sessionTeam.findFirst({
      where: { sessionId: session.id, name: spec.name },
    })
    if (existing) {
      const updated = await prisma.sessionTeam.update({
        where: { id: existing.id },
        data: spec,
      })
      teamsMap.set(spec.name, updated)
    } else {
      const created = await prisma.sessionTeam.create({
        data: {
          sessionId: session.id,
          ...spec,
        },
      })
      teamsMap.set(spec.name, created)
    }
  }
  console.log('👥 [SIMULATION] Configured 4 Teams with inventory & wealth.')

  const teamAlfa = teamsMap.get('Alfa Vállalat')
  const teamBeta = teamsMap.get('Béta Vállalat')
  const teamGamma = teamsMap.get('Gamma Vállalat')
  const teamDelta = teamsMap.get('Delta Vállalat')

  // 4. Create 8 Participants (2 per team) with Real Organizational Departments
  const participantUsers = [
    { email: 'alfa.peter@peerplay.demo', name: 'Kovács Péter', role: 'Vezető Elemző', department: 'Pénzügy & Kontrolling', team: teamAlfa },
    { email: 'alfa.anna@peerplay.demo', name: 'Nagy Anna', role: 'Pénzügyi Stratéga', department: 'Pénzügy & Kontrolling', team: teamAlfa },
    { email: 'beta.tamas@peerplay.demo', name: 'Szabó Tamás', role: 'Gyártási Igazgató', department: 'Termelés & Gyártás', team: teamBeta },
    { email: 'beta.eszter@peerplay.demo', name: 'Tóth Eszter', role: 'Beszerzési Menedzser', department: 'Beszerzés & Logisztika', team: teamBeta },
    { email: 'gamma.balazs@peerplay.demo', name: 'Horváth Balázs', role: 'Főmérnök', department: 'Kutatás-Fejlesztés (K+F)', team: teamGamma },
    { email: 'gamma.dora@peerplay.demo', name: 'Varga Dóra', role: 'Minőségellenőr', department: 'Minőségbiztosítás (QA)', team: teamGamma },
    { email: 'delta.gergely@peerplay.demo', name: 'Kiss Gergely', role: 'Operatív Vezető', department: 'Értékesítés & Ügyfélkapcsolatok', team: teamDelta },
    { email: 'delta.zsofia@peerplay.demo', name: 'Molnár Zsófia', role: 'Termékfejlesztő', department: 'Termékmenedzsment', team: teamDelta },
  ]

  const createdUsers: any[] = []
  const userByName = new Map<string, any>()
  for (const p of participantUsers) {
    let user = await prisma.user.findUnique({ where: { email: p.email } })
    if (!user) {
      user = await prisma.user.create({
        data: {
          email: p.email,
          name: p.name,
          role: p.role,
          department: p.department,
          organizationId: org.id,
        },
      })
    } else {
      user = await prisma.user.update({
        where: { id: user.id },
        data: {
          role: p.role,
          department: p.department,
        },
      })
    }
    const fullUser = { ...user, team: p.team, department: p.department }
    createdUsers.push(fullUser)
    userByName.set(p.name, fullUser)

    // Upsert participant membership
    const existingPart = await prisma.teamParticipant.findFirst({
      where: { sessionId: session.id, userId: user.id },
    })
    if (!existingPart) {
      await prisma.teamParticipant.create({
        data: {
          sessionId: session.id,
          teamId: p.team.id,
          userId: user.id,
        },
      })
    }
  }
  console.log(`👤 [SIMULATION] Enrolled ${createdUsers.length} participants with real departments across the 4 teams.`)

  // 5. Create Pre-Game Pulse Survey responses
  for (const u of createdUsers) {
    const prePayload = JSON.stringify({
      initialEnergyLevel: Math.floor(Math.random() * 3) + 6, // 6 to 8
      psychologicalSafety: Math.floor(Math.random() * 2) + 7, // 7 to 8
      initialTrust: Math.floor(Math.random() * 3) + 7, // 7 to 9
      preExpectations: 'Nyitott vagyok a konstruktív tárgyalásokra és a szövetségépítésre.',
    })

    await prisma.surveyResponse.upsert({
      where: {
        sessionId_userId_phaseType: {
          sessionId: session.id,
          userId: u.id,
          phaseType: 'PRE_GAME',
        },
      },
      create: {
        sessionId: session.id,
        userId: u.id,
        phaseType: 'PRE_GAME',
        payloadJson: prePayload,
      },
      update: {
        payloadJson: prePayload,
      },
    })
  }
  console.log('📋 [SIMULATION] Recorded Pre-Game Pulse survey responses for all 8 players.')

  // 6. Generate Peer-to-Peer Trade Transactions
  await prisma.tradeTransaction.deleteMany({
    where: { sessionId: session.id },
  })

  const sampleTrades = [
    {
      senderTeamId: teamBeta.id,
      receiverTeamId: teamAlfa.id,
      createdByName: 'Szabó Tamás',
      createdByUserId: userByName.get('Szabó Tamás')?.id,
      acceptedByName: 'Kovács Péter',
      acceptedByUserId: userByName.get('Kovács Péter')?.id,
      offeredItems: JSON.stringify({ cash: 0, paperSheets: 2, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 40, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 0, paperSheets: 2, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      status: 'ACCEPTED',
      notes: 'Papír szállítása készpénzért a kezdeti termelés beindításához.',
    },
    {
      senderTeamId: teamGamma.id,
      receiverTeamId: teamDelta.id,
      createdByName: 'Horváth Balázs',
      createdByUserId: userByName.get('Horváth Balázs')?.id,
      acceptedByName: 'Kiss Gergely',
      acceptedByUserId: userByName.get('Kiss Gergely')?.id,
      offeredItems: JSON.stringify({ cash: 0, paperSheets: 0, scissorsCount: 0, rulersCount: 1, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 20, paperSheets: 1, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 0, paperSheets: 0, scissorsCount: 0, rulersCount: 1, templatesCount: 0 }),
      status: 'ACCEPTED',
      notes: 'Vonalzó bérlet papírlapért és készpénz kompenzációért.',
    },
    {
      senderTeamId: teamAlfa.id,
      receiverTeamId: teamGamma.id,
      createdByName: 'Nagy Anna',
      createdByUserId: userByName.get('Nagy Anna')?.id,
      acceptedByName: 'Varga Dóra',
      acceptedByUserId: userByName.get('Varga Dóra')?.id,
      offeredItems: JSON.stringify({ cash: 50, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 0, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 1 }),
      escrowedItems: JSON.stringify({ cash: 50, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      status: 'ACCEPTED',
      notes: 'Sablon használat kör alakú formák kivágásához.',
    },
    {
      senderTeamId: teamDelta.id,
      receiverTeamId: teamBeta.id,
      createdByName: 'Molnár Zsófia',
      createdByUserId: userByName.get('Molnár Zsófia')?.id,
      acceptedByName: 'Tóth Eszter',
      acceptedByUserId: userByName.get('Tóth Eszter')?.id,
      offeredItems: JSON.stringify({ cash: 0, paperSheets: 0, scissorsCount: 1, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 0, paperSheets: 3, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 0, paperSheets: 0, scissorsCount: 1, rulersCount: 0, templatesCount: 0 }),
      status: 'ACCEPTED',
      notes: 'Olló átadása nyersanyagéhes szövetségesnek.',
    },
    {
      senderTeamId: teamBeta.id,
      receiverTeamId: teamGamma.id,
      createdByName: 'Szabó Tamás',
      createdByUserId: userByName.get('Szabó Tamás')?.id,
      acceptedByName: null,
      offeredItems: JSON.stringify({ cash: 0, paperSheets: 2, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 60, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 0, paperSheets: 2, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      status: 'REJECTED',
      notes: 'Túl magas árajánlat a technológiai csapatnak.',
    },
    {
      senderTeamId: teamAlfa.id,
      receiverTeamId: teamDelta.id,
      createdByName: 'Kovács Péter',
      createdByUserId: userByName.get('Kovács Péter')?.id,
      acceptedByName: 'Kiss Gergely',
      acceptedByUserId: userByName.get('Kiss Gergely')?.id,
      offeredItems: JSON.stringify({ cash: 30, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 0, paperSheets: 1, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 30, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      status: 'ACCEPTED',
      notes: 'Készpénzes vásárlás a felzárkózó csapattól.',
    },
    {
      senderTeamId: teamDelta.id,
      receiverTeamId: teamAlfa.id,
      createdByName: 'Kiss Gergely',
      createdByUserId: userByName.get('Kiss Gergely')?.id,
      acceptedByName: null,
      offeredItems: JSON.stringify({ cash: 0, paperSheets: 1, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      requestedItems: JSON.stringify({ cash: 50, paperSheets: 0, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      escrowedItems: JSON.stringify({ cash: 0, paperSheets: 1, scissorsCount: 0, rulersCount: 0, templatesCount: 0 }),
      status: 'PENDING',
      notes: 'Ajánlat tárgyalás alatt az utolsó körben.',
    },
  ]

  for (const tr of sampleTrades) {
    await prisma.tradeTransaction.create({
      data: {
        sessionId: session.id,
        ...tr,
        resolvedAt: tr.status === 'ACCEPTED' || tr.status === 'REJECTED' ? new Date() : null,
      },
    })
  }
  console.log(`🤝 [SIMULATION] Generated ${sampleTrades.length} peer trade offers (ACCEPTED, REJECTED, PENDING).`)

  // 7. Generate Bank Commodity Sales
  await prisma.bankSale.deleteMany({
    where: { sessionId: session.id },
  })

  const sampleBankSales = [
    { teamId: teamAlfa.id, shapeType: 'SQUARE', quantity: 2, unitBasePrice: 300, multiplier: 1.0, finalUnitPrice: 300, totalPayout: 600, submittedByName: 'Kovács Péter' },
    { teamId: teamBeta.id, shapeType: 'TRIANGLE', quantity: 3, unitBasePrice: 200, multiplier: 1.0, finalUnitPrice: 200, totalPayout: 600, submittedByName: 'Szabó Tamás' },
    { teamId: teamGamma.id, shapeType: 'CIRCLE', quantity: 1, unitBasePrice: 300, multiplier: 1.5, finalUnitPrice: 450, totalPayout: 450, submittedByName: 'Horváth Balázs' },
    { teamId: teamGamma.id, shapeType: 'PREMIUM_PACK', quantity: 1, unitBasePrice: 800, multiplier: 1.5, finalUnitPrice: 1200, totalPayout: 1200, submittedByName: 'Varga Dóra' },
    { teamId: teamDelta.id, shapeType: 'SQUARE', quantity: 1, unitBasePrice: 300, multiplier: 1.0, finalUnitPrice: 300, totalPayout: 300, submittedByName: 'Kiss Gergely' },
    { teamId: teamDelta.id, shapeType: 'RECTANGLE', quantity: 2, unitBasePrice: 250, multiplier: 1.0, finalUnitPrice: 250, totalPayout: 500, submittedByName: 'Molnár Zsófia' },
    { teamId: teamBeta.id, shapeType: 'PREMIUM_PACK', quantity: 1, unitBasePrice: 800, multiplier: 1.0, finalUnitPrice: 800, totalPayout: 800, submittedByName: 'Tóth Eszter' },
    { teamId: teamAlfa.id, shapeType: 'CIRCLE', quantity: 1, unitBasePrice: 300, multiplier: 1.5, finalUnitPrice: 450, totalPayout: 450, submittedByName: 'Nagy Anna' },
  ]

  for (const bs of sampleBankSales) {
    await prisma.bankSale.create({
      data: {
        sessionId: session.id,
        teamId: bs.teamId,
        shapeType: bs.shapeType,
        quantity: bs.quantity,
        unitBasePrice: bs.unitBasePrice,
        multiplier: bs.multiplier,
        finalUnitPrice: bs.finalUnitPrice,
        totalPayout: bs.totalPayout,
        status: 'APPROVED',
        submittedByName: bs.submittedByName,
        approvedAt: new Date(),
        soldAt: new Date(),
      },
    })
  }
  console.log(`🏦 [SIMULATION] Generated ${sampleBankSales.length} approved Central Bank sales.`)

  // 8. Market Event
  await prisma.marketEvent.deleteMany({
    where: { sessionId: session.id },
  })

  await prisma.marketEvent.create({
    data: {
      sessionId: session.id,
      title: 'Geometriai Boom (Prémium Felvásárlás)',
      description: 'A Központi Bank 50%-os árprémiumot fizet a Körökre és Prémium Csomagokra!',
      code: 'TECH_BOOM',
      priceMultipliers: JSON.stringify({ CIRCLE: 1.5, PREMIUM_PACK: 1.5 }),
      durationSeconds: 300,
      isActive: true,
      triggeredAt: new Date(),
    },
  })
  console.log('⚡ [SIMULATION] Activated Market Event: Geometriai Boom (+50% Kör & Prémium).')

  // 9. Post-Game Peer Feedback Survey Responses with Cross-Team & Intra-Team ONA Nominations
  for (const u of createdUsers) {
    // Find internal teammate
    const teammate = createdUsers.find((p) => p.team.id === u.team.id && p.id !== u.id)
    // Find other external partners
    const externalPeers = createdUsers.filter((p) => p.team.id !== u.team.id)
    const nominatedBrokers = [
      externalPeers[(createdUsers.indexOf(u) + 1) % externalPeers.length],
      externalPeers[(createdUsers.indexOf(u) + 3) % externalPeers.length],
    ].filter(Boolean)

    const postPayload = JSON.stringify({
      finalEnergyLevel: Math.floor(Math.random() * 2) + 8, // 8 to 9
      finalEnergy: Math.floor(Math.random() * 2) + 8,
      brokerNominations: nominatedBrokers.map((b) => b.id),
      internalEnablerNominations: teammate ? [teammate.id] : [],
      collaborationRating: Math.floor(Math.random() * 2) + 8, // 8 to 9
      negotiationSatisfaction: 9,
      networkRecognitions: [
        {
          nomineeId: nominatedBrokers[0]?.id,
          nomineeName: nominatedBrokers[0]?.name,
          reason: 'Kiváló keresztfunkcionális partnerség és korrekt megállapodások.',
        },
        teammate
          ? {
              nomineeId: teammate.id,
              nomineeName: teammate.name,
              reason: 'Megbízható belső támasz és precíz végrehajtás a vállalatunkban.',
            }
          : null,
      ].filter(Boolean),
      keyLearnings: 'A szakterületek közötti gyors információcsere és a bizalmi tőke volt a legnagyobb versenyelőnyünk.',
    })

    await prisma.surveyResponse.upsert({
      where: {
        sessionId_userId_phaseType: {
          sessionId: session.id,
          userId: u.id,
          phaseType: 'POST_GAME',
        },
      },
      create: {
        sessionId: session.id,
        userId: u.id,
        phaseType: 'POST_GAME',
        payloadJson: postPayload,
      },
      update: {
        payloadJson: postPayload,
      },
    })
  }
  console.log('📊 [SIMULATION] Recorded Post-Game Peer Feedback survey responses with ONA votes.')

  // Final summary query
  const finalSales = await prisma.bankSale.findMany({ where: { sessionId: session.id } })
  const totalBankPayout = finalSales.reduce((acc, s) => acc + s.totalPayout, 0)
  const finalTrades = await prisma.tradeTransaction.findMany({ where: { sessionId: session.id } })
  const acceptedCount = finalTrades.filter((t) => t.status === 'ACCEPTED').length

  console.log('\n======================================================')
  console.log('🎯 [SIMULATION COMPLETED SUCCESSFULLY]')
  console.log('======================================================')
  console.log(`📌 Munkamenet PIN: ${session.joinCode}`)
  console.log(`📌 Munkamenet ID: ${session.id}`)
  console.log(`🏢 Központi Bank Összes Kifizetés: $${totalBankPayout}`)
  console.log(`🤝 Sikeres Csapatközi Ügyletek: ${acceptedCount} db`)
  console.log(`👥 Résztvevők száma: ${createdUsers.length} fő`)
  console.log(`📈 Aktuális Fázis: PHASE_11_DEBRIEF (Eredményhirdetés & ONA)`)
  console.log('\n🔗 Hasznos linkek megtekintéshez:')
  console.log(`   - Facilitátori Konzol: http://localhost:3001/sessions/${session.id}`)
  console.log(`   - Eredményhirdetés Kivetítő: http://localhost:3001/sessions/${session.id}/debrief`)
  console.log(`   - Csapat Pult (Tablet): http://localhost:3001/play/${session.id}`)
  console.log(`   - Játékos Mobil (Alfa): http://localhost:3001/survey/${session.id}?userId=${createdUsers[0].id}`)
  console.log(`   - Játékos Mobil (Béta): http://localhost:3001/survey/${session.id}?userId=${createdUsers[2].id}`)
  console.log('======================================================\n')
}

main()
  .catch((e) => {
    console.error('❌ [SIMULATION ERROR]:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
