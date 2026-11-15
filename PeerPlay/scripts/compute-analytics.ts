import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  const session = await prisma.session.findUnique({
    where: { joinCode: 'DEMO01' },
    include: {
      teams: {
        include: {
          participants: {
            include: {
              user: true
            }
          },
          bankSales: true,
          sentTrades: true,
          receivedTrades: true
        }
      },
      tradeTransactions: {
        include: {
          senderTeam: true,
          receiverTeam: true
        }
      },
      bankSales: {
        include: {
          team: true
        }
      },
      marketEvents: true,
      surveyResponses: {
        include: {
          user: {
            include: {
              teamMemberships: {
                include: { team: true }
              }
            }
          }
        }
      },
      onaInvitations: {
        include: {
          user: true,
          responses: true
        }
      }
    }
  })

  if (!session) {
    console.error('Session DEMO01 not found!')
    return
  }

  console.log('=== PEERPLAY SESSION DATA ANALYSIS (DEMO01) ===')
  console.log(`Session: ${session.name} (${session.joinCode}), Phase: ${session.currentPhase}, Status: ${session.status}`)

  const teams = session.teams
  const teamMap = new Map()
  teams.forEach((t: any) => teamMap.set(t.id, t))

  // 1. Asset standard values
  // In the workshop game: Paper = 30, Scissor = 150, Ruler = 100, Template = 200
  const itemValuations: Record<string, number> = {
    paperSheets: 30,
    scissorsCount: 150,
    rulersCount: 100,
    templatesCount: 200,
  }

  console.log('\n--- 1. TEAMS & WEALTH SUMMARY ---')
  const teamWealthData: any[] = []
  teams.forEach((t: any) => {
    const assetValue = 
      t.paperSheets * itemValuations.paperSheets +
      t.scissorsCount * itemValuations.scissorsCount +
      t.rulersCount * itemValuations.rulersCount +
      t.templatesCount * itemValuations.templatesCount
    const totalWealth = t.cashBalance + assetValue
    teamWealthData.push({
      id: t.id,
      name: t.name,
      profile: t.profileCode,
      cash: t.cashBalance,
      paper: t.paperSheets,
      scissors: t.scissorsCount,
      rulers: t.rulersCount,
      templates: t.templatesCount,
      assetValue,
      totalWealth
    })
  })
  teamWealthData.sort((a, b) => b.totalWealth - a.totalWealth)
  console.table(teamWealthData)

  // 2. Trades & Network Analysis (ONA)
  console.log('\n--- 2. TRADE & NETWORK ANALYSIS (ONA) ---')
  const trades = session.tradeTransactions
  console.log(`Total trade transactions: ${trades.length}`)

  const teamTradeMatrix: Record<string, Record<string, number>> = {}
  const teamAcceptedMatrix: Record<string, Record<string, number>> = {}

  teams.forEach((t1: any) => {
    teamTradeMatrix[t1.name] = {}
    teamAcceptedMatrix[t1.name] = {}
    teams.forEach((t2: any) => {
      teamTradeMatrix[t1.name][t2.name] = 0
      teamAcceptedMatrix[t1.name][t2.name] = 0
    })
  })

  const teamDegrees: Record<string, { inDegree: number, outDegree: number, totalDegree: number, acceptedIn: number, acceptedOut: number, acceptedTotal: number }> = {}
  teams.forEach((t: any) => {
    teamDegrees[t.name] = { inDegree: 0, outDegree: 0, totalDegree: 0, acceptedIn: 0, acceptedOut: 0, acceptedTotal: 0 }
  })

  const individualActivity: Record<string, { proposed: number, accepted: number, team: string }> = {}

  trades.forEach((tr: any) => {
    const sender = teamMap.get(tr.senderTeamId).name
    const receiver = teamMap.get(tr.receiverTeamId).name
    teamTradeMatrix[sender][receiver]++
    teamDegrees[sender].outDegree++
    teamDegrees[receiver].inDegree++
    teamDegrees[sender].totalDegree++
    teamDegrees[receiver].totalDegree++

    if (tr.status === 'ACCEPTED') {
      teamAcceptedMatrix[sender][receiver]++
      teamDegrees[sender].acceptedOut++
      teamDegrees[receiver].acceptedIn++
      teamDegrees[sender].acceptedTotal++
      teamDegrees[receiver].acceptedTotal++
    }

    if (tr.createdByName) {
      if (!individualActivity[tr.createdByName]) individualActivity[tr.createdByName] = { proposed: 0, accepted: 0, team: sender }
      individualActivity[tr.createdByName].proposed++
    }
    if (tr.acceptedByName) {
      if (!individualActivity[tr.acceptedByName]) individualActivity[tr.acceptedByName] = { proposed: 0, accepted: 0, team: receiver }
      individualActivity[tr.acceptedByName].accepted++
    }
  })

  console.log('Trade Status Counts:')
  const statusCounts: Record<string, number> = {}
  trades.forEach((tr: any) => statusCounts[tr.status] = (statusCounts[tr.status] || 0) + 1)
  console.log(statusCounts)

  console.log('\nTrade Proposal Matrix (Sender -> Receiver):')
  console.table(teamTradeMatrix)

  console.log('\nAccepted Trades Matrix (Sender -> Receiver):')
  console.table(teamAcceptedMatrix)

  console.log('\nTeam Degrees (ONA Centrality):')
  console.table(teamDegrees)

  console.log('\nIndividual Trader Activity:')
  console.table(individualActivity)

  // Network Density & Reciprocity
  const directedProposedEdges = Object.values(teamTradeMatrix).flatMap(row => Object.values(row)).filter(v => v > 0).length
  // distinct directed pairs
  let proposedPairs = 0
  let acceptedPairs = 0
  let undirectedAcceptedPairs = new Set<string>()

  teams.forEach((t1: any) => {
    teams.forEach((t2: any) => {
      if (t1.name !== t2.name) {
        if (teamTradeMatrix[t1.name][t2.name] > 0) proposedPairs++
        if (teamAcceptedMatrix[t1.name][t2.name] > 0) {
          acceptedPairs++
          undirectedAcceptedPairs.add([t1.name, t2.name].sort().join(' <-> '))
        }
      }
    })
  })

  const maxDirectedPairs = 4 * 3 // 12
  const maxUndirectedPairs = (4 * 3) / 2 // 6

  let mutualPairs = 0
  const mutualList: string[] = []
  teams.forEach((t1: any, i: number) => {
    teams.forEach((t2: any, j: number) => {
      if (i < j) {
        const aToB = teamAcceptedMatrix[t1.name][t2.name] > 0
        const bToA = teamAcceptedMatrix[t2.name][t1.name] > 0
        if (aToB && bToA) {
          mutualPairs++
          mutualList.push(`${t1.name} <-> ${t2.name}`)
        }
      }
    })
  })

  console.log(`Directed Proposed Density: ${proposedPairs} / ${maxDirectedPairs} = ${(proposedPairs / maxDirectedPairs * 100).toFixed(1)}%`)
  console.log(`Directed Accepted Density: ${acceptedPairs} / ${maxDirectedPairs} = ${(acceptedPairs / maxDirectedPairs * 100).toFixed(1)}%`)
  console.log(`Undirected Connected Pairs: ${undirectedAcceptedPairs.size} / ${maxUndirectedPairs} = ${(undirectedAcceptedPairs.size / maxUndirectedPairs * 100).toFixed(1)}%`)
  console.log(`Reciprocal (Mutual) Trading Pairs: ${mutualPairs} (${mutualList.join(', ') || 'None'})`)

  // 3. Trade Cashflows & Asset Transfers
  console.log('\n--- 3. TRADE CASHFLOWS & ASSET TRANSFERS ---')
  const teamTradeCashflow: Record<string, { cashIn: number, cashOut: number, netCash: number, paperIn: number, paperOut: number, toolsIn: number, toolsOut: number }> = {}
  teams.forEach((t: any) => {
    teamTradeCashflow[t.name] = { cashIn: 0, cashOut: 0, netCash: 0, paperIn: 0, paperOut: 0, toolsIn: 0, toolsOut: 0 }
  })

  trades.filter((t: any) => t.status === 'ACCEPTED').forEach((tr: any) => {
    const sender = teamMap.get(tr.senderTeamId).name
    const receiver = teamMap.get(tr.receiverTeamId).name
    const offered = JSON.parse(tr.offeredItems)
    const requested = JSON.parse(tr.requestedItems)

    // Sender transfers offered to Receiver, Receiver transfers requested to Sender
    // Cash:
    const senderCashDelta = (requested.cash || 0) - (offered.cash || 0)
    const receiverCashDelta = -senderCashDelta

    if (senderCashDelta > 0) {
      teamTradeCashflow[sender].cashIn += senderCashDelta
      teamTradeCashflow[receiver].cashOut += senderCashDelta
    } else if (senderCashDelta < 0) {
      teamTradeCashflow[sender].cashOut += -senderCashDelta
      teamTradeCashflow[receiver].cashIn += -senderCashDelta
    }
    teamTradeCashflow[sender].netCash += senderCashDelta
    teamTradeCashflow[receiver].netCash += receiverCashDelta

    // Paper:
    const senderPaperDelta = (requested.paperSheets || 0) - (offered.paperSheets || 0)
    if (senderPaperDelta > 0) {
      teamTradeCashflow[sender].paperIn += senderPaperDelta
      teamTradeCashflow[receiver].paperOut += senderPaperDelta
    } else if (senderPaperDelta < 0) {
      teamTradeCashflow[sender].paperOut += -senderPaperDelta
      teamTradeCashflow[receiver].paperIn += -senderPaperDelta
    }

    // Tools:
    const senderToolsDelta = ((requested.scissorsCount || 0) + (requested.rulersCount || 0) + (requested.templatesCount || 0)) -
                             ((offered.scissorsCount || 0) + (offered.rulersCount || 0) + (offered.templatesCount || 0))
    if (senderToolsDelta > 0) {
      teamTradeCashflow[sender].toolsIn += senderToolsDelta
      teamTradeCashflow[receiver].toolsOut += senderToolsDelta
    } else if (senderToolsDelta < 0) {
      teamTradeCashflow[sender].toolsOut += -senderToolsDelta
      teamTradeCashflow[receiver].toolsIn += -senderToolsDelta
    }
  })
  console.table(teamTradeCashflow)

  // 4. Central Bank Sales & Market Shock
  console.log('\n--- 4. CENTRAL BANK SALES & MARKET SHOCK ---')
  const bankSales = session.bankSales
  const teamBankRevenue: Record<string, { totalPayout: number, shapesCount: number, premiumRevenue: number, standardRevenue: number, shapes: Record<string, number> }> = {}
  teams.forEach((t: any) => {
    teamBankRevenue[t.name] = { totalPayout: 0, shapesCount: 0, premiumRevenue: 0, standardRevenue: 0, shapes: {} }
  })

  bankSales.forEach((bs: any) => {
    const tName = teamMap.get(bs.teamId).name
    teamBankRevenue[tName].totalPayout += bs.totalPayout
    teamBankRevenue[tName].shapesCount += bs.quantity
    if (bs.multiplier > 1.0) {
      teamBankRevenue[tName].premiumRevenue += bs.totalPayout
    } else {
      teamBankRevenue[tName].standardRevenue += bs.totalPayout
    }
    teamBankRevenue[tName].shapes[bs.shapeType] = (teamBankRevenue[tName].shapes[bs.shapeType] || 0) + bs.quantity
  })
  console.table(teamBankRevenue)

  // Bank dependency
  console.log('\n--- BANK DEPENDENCY & REVENUE COMPOSITION ---')
  const revenueComp: any[] = []
  teams.forEach((t: any) => {
    const bankRev = teamBankRevenue[t.name].totalPayout
    const tradeIn = teamTradeCashflow[t.name].cashIn
    const totalCashGenerated = bankRev + tradeIn
    const bankDependency = totalCashGenerated > 0 ? (bankRev / totalCashGenerated) * 100 : 0
    revenueComp.push({
      team: t.name,
      bankRevenue: `$${bankRev}`,
      tradeInflow: `$${tradeIn}`,
      tradeOutflow: `$${teamTradeCashflow[t.name].cashOut}`,
      netTradeCash: `$${teamTradeCashflow[t.name].netCash}`,
      totalCashGenerated: `$${totalCashGenerated}`,
      bankDependencyRate: `${bankDependency.toFixed(1)}%`
    })
  })
  console.table(revenueComp)

  // 5. Psychometrics & Surveys
  console.log('\n--- 5. PSYCHOMETRIC & TEAM DYNAMICS ---')
  const surveys = session.surveyResponses
  const preSurveys: Record<string, any> = {}
  const postSurveys: Record<string, any> = {}

  surveys.forEach((s: any) => {
    const payload = JSON.parse(s.payloadJson)
    const teamName = s.user.teamMemberships[0]?.team?.name || 'Unknown'
    if (s.phaseType === 'PRE_GAME') {
      preSurveys[s.userId] = { user: s.user.name, team: teamName, role: s.user.role, ...payload }
    } else if (s.phaseType === 'POST_GAME') {
      postSurveys[s.userId] = { user: s.user.name, team: teamName, role: s.user.role, ...payload }
    }
  })

  const individualMetrics: any[] = []
  const teamDeltas: Record<string, { sumDeltaEnergy: number, count: number, avgPreSafety: number, avgPreTrust: number, avgCollab: number }> = {}
  teams.forEach((t: any) => {
    teamDeltas[t.name] = { sumDeltaEnergy: 0, count: 0, avgPreSafety: 0, avgPreTrust: 0, avgCollab: 0 }
  })

  Object.keys(preSurveys).forEach(uid => {
    const pre = preSurveys[uid]
    const post = postSurveys[uid]
    if (post) {
      const deltaEnergy = post.finalEnergyLevel - pre.initialEnergyLevel
      individualMetrics.push({
        name: pre.user,
        team: pre.team,
        role: pre.role,
        preEnergy: pre.initialEnergyLevel,
        postEnergy: post.finalEnergyLevel,
        deltaEnergy,
        psychSafety: pre.psychologicalSafety,
        initialTrust: pre.initialTrust,
        collabRating: post.collaborationRating,
        negotiationSat: post.negotiationSatisfaction
      })

      const td = teamDeltas[pre.team]
      if (td) {
        td.sumDeltaEnergy += deltaEnergy
        td.avgPreSafety += pre.psychologicalSafety
        td.avgPreTrust += pre.initialTrust
        td.avgCollab += post.collaborationRating
        td.count++
      }
    }
  })

  console.log('\nIndividual Psychometrics (N=8):')
  console.table(individualMetrics)

  const teamPsychSummary: any[] = []
  Object.keys(teamDeltas).forEach(tName => {
    const td = teamDeltas[tName]
    teamPsychSummary.push({
      team: tName,
      avgDeltaEnergy: (td.sumDeltaEnergy / td.count).toFixed(2),
      avgPsychSafety: (td.avgPreSafety / td.count).toFixed(2),
      avgInitialTrust: (td.avgPreTrust / td.count).toFixed(2),
      avgCollabRating: (td.avgCollab / td.count).toFixed(2),
      wealth: teamWealthData.find(w => w.name === tName)?.totalWealth
    })
  })
  console.log('\nTeam Psychometrics Aggregated:')
  console.table(teamPsychSummary)

  // 6. Post-Game Network Recognitions
  console.log('\n--- 6. POST-GAME ONA RECOGNITIONS ---')
  const recognitionsReceived: Record<string, { count: number, voters: string[], reasons: string[] }> = {}
  Object.values(postSurveys).forEach((p: any) => {
    if (p.networkRecognitions && Array.isArray(p.networkRecognitions)) {
      p.networkRecognitions.forEach((nr: any) => {
        if (!recognitionsReceived[nr.nomineeName]) {
          recognitionsReceived[nr.nomineeName] = { count: 0, voters: [], reasons: [] }
        }
        recognitionsReceived[nr.nomineeName].count++
        recognitionsReceived[nr.nomineeName].voters.push(p.user)
        recognitionsReceived[nr.nomineeName].reasons.push(nr.reason)
      })
    }
  })
  console.table(Object.keys(recognitionsReceived).map(k => ({
    nominee: k,
    votes: recognitionsReceived[k].count,
    voters: recognitionsReceived[k].voters.join(', '),
    reasons: recognitionsReceived[k].reasons.join(' | ')
  })))

  // 7. Silo Index (Krackhardt E-I Index)
  // E-I Index = (External Trades - Internal Trades) / (External Trades + Internal Trades)
  // In our simulation all trades are across teams, so let's look at dyadic isolation (unconnected team pairs).
  console.log('\n--- 7. SILO & ISOLATION ANALYSIS ---')
  teams.forEach((t1: any) => {
    const tradedPartners = teams.filter((t2: any) => t1.name !== t2.name && (teamAcceptedMatrix[t1.name][t2.name] > 0 || teamAcceptedMatrix[t2.name][t1.name] > 0))
    const isolatedPartners = teams.filter((t2: any) => t1.name !== t2.name && (teamAcceptedMatrix[t1.name][t2.name] === 0 && teamAcceptedMatrix[t2.name][t1.name] === 0))
    console.log(`${t1.name}: Connected with ${tradedPartners.length}/3 teams (${tradedPartners.map((p: any) => p.name).join(', ')}). Isolated from: ${isolatedPartners.map((p: any) => p.name).join(', ') || 'None'}`)
  })
}

main().catch(console.error).finally(() => prisma.$disconnect())
