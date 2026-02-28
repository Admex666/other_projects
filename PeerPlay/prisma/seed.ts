import prisma from '../src/lib/prisma'

async function main() {
    // Create an Organization
    const org = await prisma.organization.create({
        data: {
            name: 'Acme Corp',
            industry: 'Technology',
            orgStructure: { departments: ['Engineering', 'Sales', 'HR'] }
        }
    })

    // Create some users
    const user1 = await prisma.user.create({
        data: { name: 'Alice', role: 'Engineer', organizationId: org.id, teamMembership: 'Engineering' }
    })
    const user2 = await prisma.user.create({
        data: { name: 'Bob', role: 'Sales rep', organizationId: org.id, teamMembership: 'Sales' }
    })

    // Create a Scenario 
    const scenario = await prisma.scenario.create({
        data: {
            name: 'Economic Trade V1',
            behavioralFocus: 'Cross-functional dependency and negotiation',
            version: '1.0',
            config: {
                startingResources: {
                    Engineering: { tech: 10, cash: 2 },
                    Sales: { tech: 2, cash: 10 }
                },
                rounds: 3,
                roundDurationMinutes: 5
            }
        }
    })

    console.log('Seed completed successfully.')
    console.log('Org ID:', org.id)
    console.log('Scenario ID:', scenario.id)
}

main()
    .catch((e) => {
        console.error(e)
        process.exit(1)
    })
    .finally(async () => {
        await prisma.$disconnect()
    })
