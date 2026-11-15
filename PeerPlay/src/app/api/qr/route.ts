import QRCode from 'qrcode'

export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const data = searchParams.get('data') || '{}'

  try {
    const svg = await QRCode.toString(data, {
      type: 'svg',
      margin: 1,
      color: { dark: '#0f172a', light: '#ffffff' },
    })

    return new Response(svg, {
      status: 200,
      headers: {
        'Content-Type': 'image/svg+xml; charset=utf-8',
        'Cache-Control': 'public, max-age=3600',
      },
    })
  } catch (err) {
    const fallbackSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#fff"/></svg>`
    return new Response(fallbackSvg, {
      status: 200,
      headers: { 'Content-Type': 'image/svg+xml; charset=utf-8' },
    })
  }
}
