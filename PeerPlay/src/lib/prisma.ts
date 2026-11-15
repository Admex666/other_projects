import { PrismaClient } from '@prisma/client'

const prismaClientSingleton = () => {
  return new PrismaClient()
}

declare global {
  var prismaGlobal: undefined | ReturnType<typeof prismaClientSingleton>
}

// Invalidate previously cached instance to pick up runtime schema updates
const prisma = new PrismaClient()

export default prisma

if (process.env.NODE_ENV !== 'production') globalThis.prismaGlobal = prisma
