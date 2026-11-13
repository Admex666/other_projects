import prisma from '../src/lib/prisma'
import { createWorkshopSession, initializeTeamArchetypes } from '../src/modules/session/actions'

async function main() {
  console.log('Seeding V2 database...')

  // 1. Upsert Organization
  let org = await prisma.organization.findFirst({
    where: { name: 'Acme Corp' },
  })
  if (!org) {
    org = await prisma.organization.create({
      data: {
        name: 'Acme Corp',
        industry: 'Technology',
      },
    })
  }

  // 2. Upsert Users
  const user1 = await prisma.user.upsert({
    where: { email: 'alice@acme.com' },
    create: {
      name: 'Alice Kovács',
      email: 'alice@acme.com',
      role: 'Engineering Lead',
      organizationId: org.id,
    },
    update: {
      name: 'Alice Kovács',
      role: 'Engineering Lead',
    },
  })

  const user2 = await prisma.user.upsert({
    where: { email: 'bob@acme.com' },
    create: {
      name: 'Bob Nagy',
      email: 'bob@acme.com',
      role: 'Commercial Lead',
      organizationId: org.id,
    },
    update: {
      name: 'Bob Nagy',
      role: 'Commercial Lead',
    },
  })

  // 3. Upsert Demo Session
  let session = await prisma.session.findUnique({
    where: { joinCode: 'DEMO01' },
  })
  if (!session) {
    session = await createWorkshopSession(org.id, 'DEMO01', 'Trading Game Pilot Workshop')
  } else {
    await initializeTeamArchetypes(session.id)
  }

  console.log('✓ Seed completed successfully.')
  console.log('Org ID:', org.id)
  console.log('Session ID:', session.id, 'Join Code:', session.joinCode)
  console.log('Users:', user1.email, user2.email)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
