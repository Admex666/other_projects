import { NextResponse } from 'next/server'
import os from 'os'

export async function GET() {
  const nets = os.networkInterfaces()
  const candidates: { address: string; name: string; priority: number }[] = []

  for (const name of Object.keys(nets)) {
    const netList = nets[name]
    if (!netList) continue

    for (const net of netList) {
      const isIPv4 = net.family === 'IPv4' || (net.family as unknown as number) === 4
      if (isIPv4 && !net.internal) {
        let priority = 1
        const lowerName = name.toLowerCase()
        if (lowerName.includes('wi-fi') || lowerName.includes('wifi') || lowerName.includes('wireless') || lowerName.includes('wlan')) {
          priority = 10
        } else if (lowerName.includes('ethernet') || lowerName.includes('eth') || lowerName.includes('helyi')) {
          if (lowerName.includes('*') || lowerName.includes('vethernet') || lowerName.includes('virtual') || lowerName.includes('vmware') || lowerName.includes('vbox')) {
            priority = 2
          } else {
            priority = 8
          }
        }
        candidates.push({ address: net.address, name, priority })
      }
    }
  }

  candidates.sort((a, b) => b.priority - a.priority)
  const lanIp = candidates.length > 0 ? candidates[0].address : '127.0.0.1'

  return NextResponse.json({
    lanIp,
    interfaces: candidates,
    timestamp: new Date().toISOString()
  })
}
