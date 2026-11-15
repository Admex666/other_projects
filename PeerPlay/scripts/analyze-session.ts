import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  const sessions = await prisma.session.findMany({
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
      tradeTransactions: true,
      bankSales: true,
      marketEvents: true,
      surveyResponses: {
        include: {
          user: true
        }
      },
      onaInvitations: {
        include: {
          responses: true
        }
      }
    }
  })

  console.log(`Found ${sessions.length} sessions.`)
  for (const s of sessions) {
    console.log(`\n========================================`)
    console.log(`Session ID: ${s.id}, Code: ${s.joinCode}, Name: ${s.name}, Phase: ${s.currentPhase}, Status: ${s.status}`)
    console.log(`Teams (${s.teams.length}):`)
    for (const t of s.teams) {
      console.log(`  - Team: ${t.name} (${t.profileCode}) | Cash: $${t.cashBalance} | Paper: ${t.paperSheets} | Scissors: ${t.scissorsCount} | Rulers: ${t.rulersCount} | Templates: ${t.templatesCount}`)
      console.log(`    Participants (${t.participants.length}): ${t.participants.map(p => `${p.user.name} (${p.user.role})`).join(', ')}`)
      console.log(`    Bank Sales (${t.bankSales.length}): total $${t.bankSales.reduce((acc, bs) => acc + bs.totalPayout, 0)}`)
    }

    console.log(`\nTrades (${s.tradeTransactions.length}):`)
    for (const tr of s.tradeTransactions) {
      const sender = s.teams.find(t => t.id === tr.senderTeamId)?.name
      const receiver = s.teams.find(t => t.id === tr.receiverTeamId)?.name
      console.log(`  - [${tr.status}] ${sender} -> ${receiver} | Offered: ${tr.offeredItems} | Requested: ${tr.requestedItems} | Notes: ${tr.notes}`)
    }

    console.log(`\nBank Sales (${s.bankSales.length}):`)
    for (const bs of s.bankSales) {
      const team = s.teams.find(t => t.id === bs.teamId)?.name
      console.log(`  - ${team} sold ${bs.quantity}x ${bs.shapeType} @ base ${bs.unitBasePrice} * ${bs.multiplier} = $${bs.totalPayout} (Submitted by: ${bs.submittedByName})`)
    }

    console.log(`\nMarket Events (${s.marketEvents.length}):`)
    for (const me of s.marketEvents) {
      console.log(`  - ${me.title} (${me.code}): Multipliers: ${me.priceMultipliers}, Active: ${me.isActive}`)
    }

    console.log(`\nSurveys (${s.surveyResponses.length}):`)
    for (const sr of s.surveyResponses) {
      console.log(`  - User: ${sr.user.name} | Phase: ${sr.phaseType} | Payload: ${sr.payloadJson}`)
    }

    console.log(`\nONA Invitations (${s.onaInvitations.length}):`)
    for (const oi of s.onaInvitations) {
      console.log(`  - Invitation: ${oi.id} | User: ${oi.userId} | Responses: ${oi.responses.length}`)
    }
  }
}

main().catch(console.error).finally(() => prisma.$disconnect())
