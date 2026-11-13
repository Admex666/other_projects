import prisma from '../src/lib/prisma'
import {
  createWorkshopSession,
  initializeTeamArchetypes,
  advanceSessionPhase,
  adjustPhaseTimer,
} from '../src/modules/session/actions'
import {
  createTradeOffer,
  acceptTradeOffer,
  rejectTradeOffer,
  cancelTradeOffer,
  autoRefundOnPhaseEnd,
} from '../src/modules/trade/actions'
import {
  executeBankSale,
  executeBatchBankSale,
  triggerMarketEvent,
} from '../src/modules/bank/actions'
import {
  submitPreGameSurvey,
  submitPostGameFeedback,
  submitWorkplaceOna,
  createOnaInvitation,
} from '../src/modules/survey/actions'

async function runTests() {
  console.log('--- 🧪 STARTING MILESTONE 1 VERIFICATION TESTS ---')

  // 1. Organization & Session Creation
  console.log('1. Testing Organization & Session Creation...')
  const org = await prisma.organization.create({
    data: {
      name: 'Acme Test Corp',
      industry: 'Technology',
    },
  })

  const testCode = 'T' + Math.floor(1000 + Math.random() * 9000).toString()
  const session = await createWorkshopSession(org.id, testCode, 'Test Workshop Session')
  console.log(`✓ Session created: ${session.id} with joinCode: ${session.joinCode}`)
  if (session.currentPhase !== 'PHASE_0_SETUP') {
    throw new Error(`Expected PHASE_0_SETUP, got ${session.currentPhase}`)
  }

  // 2. Team Archetypes Verification
  console.log('2. Verifying 4 Team Archetypes...')
  const teams = await prisma.sessionTeam.findMany({
    where: { sessionId: session.id },
    orderBy: { profileCode: 'asc' },
  })
  console.log(`✓ Found ${teams.length} teams initialized`)
  if (teams.length !== 4) {
    throw new Error(`Expected 4 teams, got ${teams.length}`)
  }

  const capitalTeam = teams.find((t) => t.profileCode === 'CAPITAL')!
  const resourceTeam = teams.find((t) => t.profileCode === 'RESOURCE')!
  const techTeam = teams.find((t) => t.profileCode === 'TECH')!
  const emergingTeam = teams.find((t) => t.profileCode === 'EMERGING')!

  if (capitalTeam.cashBalance !== 1500 || capitalTeam.paperSheets !== 2) {
    throw new Error('CAPITAL team initial inventory mismatch!')
  }
  if (resourceTeam.cashBalance !== 200 || resourceTeam.paperSheets !== 15) {
    throw new Error('RESOURCE team initial inventory mismatch!')
  }
  if (techTeam.scissorsCount !== 2 || techTeam.rulersCount !== 2 || techTeam.templatesCount !== 2) {
    throw new Error('TECH team initial inventory mismatch!')
  }
  if (emergingTeam.cashBalance !== 500 || emergingTeam.paperSheets !== 5 || emergingTeam.scissorsCount !== 1) {
    throw new Error('EMERGING team initial inventory mismatch!')
  }
  console.log('✓ All 4 team archetypes verified with exact canonical inventory balances.')

  // 3. User Setup & Pre-Game Survey
  console.log('3. Testing User Setup & Pre-Game Survey...')
  const ts = Date.now()
  const user1 = await prisma.user.create({
    data: {
      email: `alice_${ts}@acme.com`,
      name: 'Alice Capitalist',
      organizationId: org.id,
    },
  })
  const user2 = await prisma.user.create({
    data: {
      email: `bob_${ts}@acme.com`,
      name: 'Bob Technologist',
      organizationId: org.id,
    },
  })

  // Advance to PHASE_1_PRE_SURVEY
  await advanceSessionPhase(session.id, 'PHASE_1_PRE_SURVEY')
  const preSurvey = await submitPreGameSurvey(session.id, user1.id, 8, 9)
  console.log(`✓ Pre-Game Survey submitted: ID ${preSurvey.id}`)
  const prePayload = JSON.parse(preSurvey.payloadJson)
  if (prePayload.initialEnergyLevel !== 8 || prePayload.initialEngagementLevel !== 9) {
    throw new Error('Pre-game payload mismatch!')
  }

  // 4. Timer Adjustment
  console.log('4. Testing Timer Adjustment...')
  const adjusted = await adjustPhaseTimer(session.id, 120, false)
  if (adjusted.phaseDurationSeconds !== 420) {
    throw new Error(`Expected 420s duration, got ${adjusted.phaseDurationSeconds}`)
  }
  console.log(`✓ Timer adjusted: duration is ${adjusted.phaseDurationSeconds}s`)

  // 5. Advance to PHASE_4_ROUND_1 for Trading
  console.log('5. Advancing to PHASE_4_ROUND_1 (Trading Active)...')
  await advanceSessionPhase(session.id, 'PHASE_4_ROUND_1')

  // 6. Immediate Escrow Trade Offer
  console.log('6. Testing Trade Offer with Immediate Escrow...')
  // Capital Team offers $300 for 4 Paper Sheets from Resource Team
  const trade1 = await createTradeOffer(
    session.id,
    capitalTeam.id,
    resourceTeam.id,
    { cash: 300 },
    { paperSheets: 4 },
    'Need paper for mass production!'
  )
  console.log(`✓ Trade created with ID: ${trade1.id}, Status: ${trade1.status}`)

  const capitalAfterOffer = await prisma.sessionTeam.findUnique({ where: { id: capitalTeam.id } })
  if (capitalAfterOffer!.cashBalance !== 1200) {
    throw new Error(`Escrow failed! Capital team should have 1200 cash, got ${capitalAfterOffer!.cashBalance}`)
  }
  console.log(`✓ Immediate Escrow verified: Capital balance decreased from 1500 to ${capitalAfterOffer!.cashBalance}`)

  // 7. Accept Trade Offer (Atomic settlement)
  console.log('7. Testing Trade Acceptance & Atomic Settlement...')
  await acceptTradeOffer(session.id, trade1.id, resourceTeam.id)

  const capitalAfterAccept = await prisma.sessionTeam.findUnique({ where: { id: capitalTeam.id } })
  const resourceAfterAccept = await prisma.sessionTeam.findUnique({ where: { id: resourceTeam.id } })

  if (capitalAfterAccept!.cashBalance !== 1200 || capitalAfterAccept!.paperSheets !== 6) {
    throw new Error(`Capital team settlement error: paperSheets should be 6 (2 + 4), got ${capitalAfterAccept!.paperSheets}`)
  }
  if (resourceAfterAccept!.cashBalance !== 500 || resourceAfterAccept!.paperSheets !== 11) {
    throw new Error(`Resource team settlement error: cash should be 500 (200 + 300), paper should be 11 (15 - 4), got cash: ${resourceAfterAccept!.cashBalance}, paper: ${resourceAfterAccept!.paperSheets}`)
  }
  console.log('✓ Trade accepted and atomic asset exchange verified!')

  // 8. Test Trade Rejection & Escrow Refund
  console.log('8. Testing Trade Rejection & Escrow Refund...')
  const trade2 = await createTradeOffer(
    session.id,
    techTeam.id,
    capitalTeam.id,
    { scissorsCount: 1 },
    { cash: 500 }
  )
  const techAfterOffer = await prisma.sessionTeam.findUnique({ where: { id: techTeam.id } })
  if (techAfterOffer!.scissorsCount !== 1) {
    throw new Error('Tech team scissors not escrowed!')
  }

  await rejectTradeOffer(session.id, trade2.id, capitalTeam.id)
  const techAfterReject = await prisma.sessionTeam.findUnique({ where: { id: techTeam.id } })
  if (techAfterReject!.scissorsCount !== 2) {
    throw new Error(`Escrow refund on reject failed! Expected 2 scissors, got ${techAfterReject!.scissorsCount}`)
  }
  console.log('✓ Reject escrow refund verified successfully!')

  // 9. Test Trade Cancellation & Escrow Refund
  console.log('9. Testing Trade Cancellation & Escrow Refund...')
  const trade3 = await createTradeOffer(
    session.id,
    emergingTeam.id,
    resourceTeam.id,
    { cash: 100 },
    { paperSheets: 2 }
  )
  await cancelTradeOffer(session.id, trade3.id, emergingTeam.id)
  const emergingAfterCancel = await prisma.sessionTeam.findUnique({ where: { id: emergingTeam.id } })
  if (emergingAfterCancel!.cashBalance !== 500) {
    throw new Error(`Escrow refund on cancel failed! Expected 500 cash, got ${emergingAfterCancel!.cashBalance}`)
  }
  console.log('✓ Cancel escrow refund verified successfully!')

  // 10. Test Auto-Refund on Phase End
  console.log('10. Testing Auto-Refund on Phase End...')
  const trade4 = await createTradeOffer(
    session.id,
    capitalTeam.id,
    techTeam.id,
    { cash: 400 },
    { scissorsCount: 1 }
  )
  // Advance phase to PHASE_5_EVENT_1 (trading round ends -> autoRefund triggered!)
  await advanceSessionPhase(session.id, 'PHASE_5_EVENT_1')

  const trade4Record = await prisma.tradeTransaction.findUnique({ where: { id: trade4.id } })
  if (trade4Record!.status !== 'EXPIRED') {
    throw new Error(`Expected trade status EXPIRED, got ${trade4Record!.status}`)
  }
  const capitalAfterExpire = await prisma.sessionTeam.findUnique({ where: { id: capitalTeam.id } })
  if (capitalAfterExpire!.cashBalance !== 1200) {
    throw new Error(`Auto-refund failed! Expected 1200 cash, got ${capitalAfterExpire!.cashBalance}`)
  }
  console.log('✓ Auto-refund on phase end verified successfully!')

  // 11. Bank Commodity Sale & Market Event
  console.log('11. Testing Bank Commodity Sale & Market Event...')
  // Trigger Market Event: CIRCLE price +50% (multiplier: 1.5)
  await triggerMarketEvent(
    session.id,
    'TECH_BOOM',
    'High Demand for Circles',
    'Government contract for high-precision circles.',
    { CIRCLE: 1.5 },
    180
  )

  // Normal square sale (base: $300)
  const squareSale = await executeBankSale(session.id, techTeam.id, 'SQUARE', 2, true, 'Good corners')
  if (squareSale.saleRecord.totalPayout !== 600) {
    throw new Error(`Expected $600 payout for 2 squares, got ${squareSale.saleRecord.totalPayout}`)
  }

  // Circle sale with 1.5x multiplier (base $250 -> $375 each * 2 = $750)
  const circleSale = await executeBankSale(session.id, techTeam.id, 'CIRCLE', 2, true, 'Precision cut')
  if (circleSale.saleRecord.finalUnitPrice !== 375 || circleSale.saleRecord.totalPayout !== 750) {
    throw new Error(`Expected $750 payout for 2 circles with 1.5 multiplier, got ${circleSale.saleRecord.totalPayout}`)
  }
  console.log(`✓ Bank sale with market event verified: $${circleSale.saleRecord.totalPayout} payout`)

  // Batch Bank Sale
  const batchResult = await executeBatchBankSale(
    session.id,
    techTeam.id,
    [
      { shapeType: 'TRIANGLE', quantity: 3 }, // 3 * 150 = 450
      { shapeType: 'RECTANGLE', quantity: 2 }, // 2 * 100 = 200
    ],
    'Batch inspection S-FAC-03'
  )
  if (batchResult.totalBatchPayout !== 650) {
    throw new Error(`Expected $650 for batch, got ${batchResult.totalBatchPayout}`)
  }
  console.log(`✓ Batch bank sale verified: $${batchResult.totalBatchPayout} payout across ${batchResult.saleRecords.length} items`)

  // 12. Post-Game Peer Feedback & Workplace ONA
  console.log('12. Testing Post-Game Peer Feedback & Workplace ONA...')
  await advanceSessionPhase(session.id, 'PHASE_10_POST_SURVEY')

  const postSurvey = await submitPostGameFeedback(
    session.id,
    user1.id,
    [user2.id], // nominated user2 as broker
    [],
    9,
    'Great collaboration with tech team.'
  )
  const postPayload = JSON.parse(postSurvey.payloadJson)
  if (postPayload.brokerNominations[0] !== user2.id || postPayload.finalEnergyLevel !== 9) {
    throw new Error('Post-game feedback mismatch!')
  }
  console.log('✓ Post-game peer feedback recorded successfully.')

  // Workplace ONA
  const invitation = await createOnaInvitation(session.id, user1.id)
  const onaResult = await submitWorkplaceOna(invitation.uniqueToken, user1.id, [
    { targetUserId: user2.id, relationType: 'COLLABORATION', frequency: 'DAILY' },
    { targetUserId: 'colleague_ext', relationType: 'ADVICE', frequencyScore: 4 },
  ])

  if (!onaResult.success || onaResult.connectionsCount !== 2) {
    throw new Error('Workplace ONA submission failed!')
  }
  const completedInvitation = await prisma.onaInvitation.findUnique({
    where: { id: invitation.id },
    include: { responses: true },
  })
  if (!completedInvitation!.isCompleted || completedInvitation!.responses.length !== 2) {
    throw new Error('ONA response persistence error!')
  }
  console.log('✓ Workplace ONA token invitation and 2 connections verified.')

  console.log('\n🎉 ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉')
}

runTests()
  .catch((e) => {
    console.error('❌ Test failed with error:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
