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
    console.log('Session DEMO01 not found!')
    return
  }

  console.log(JSON.stringify(session, null, 2))
}

main().catch(console.error).finally(() => prisma.$disconnect())
