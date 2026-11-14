'use client'

import { useEffect, useState } from 'react'
import QRCode from 'qrcode'

interface TunnelInfo {
  active?: boolean
  url?: string
  joinUrl?: string
  password?: string
  updatedAt?: string
}

export default function TunnelAccessCard() {
  const [tunnelInfo, setTunnelInfo] = useState<TunnelInfo | null>(null)
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>('')
  const [copiedPass, setCopiedPass] = useState(false)

  const activeJoinUrl =
    tunnelInfo?.active && tunnelInfo.joinUrl
      ? tunnelInfo.joinUrl
      : 'http://192.168.0.112:3000/join'

  const isTunnelActive = Boolean(tunnelInfo?.active && tunnelInfo?.joinUrl)

  // Fetch tunnel info on mount & poll every 4 seconds
  useEffect(() => {
    let isMounted = true

    const checkTunnel = async () => {
      try {
        const res = await fetch(`/tunnel-info.json?t=${Date.now()}`)
        if (res.ok) {
          const data: TunnelInfo = await res.json()
          if (isMounted) {
            setTunnelInfo(data)
          }
        }
      } catch {
        // Silently ignore if file not yet present
      }
    }

    checkTunnel()
    const interval = setInterval(checkTunnel, 4000)

    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  // Regenerate QR Code whenever activeJoinUrl changes
  useEffect(() => {
    let isMounted = true

    QRCode.toDataURL(activeJoinUrl, {
      width: 220,
      margin: 2,
      color: {
        dark: '#0f172a',
        light: '#ffffff',
      },
    })
      .then((url) => {
        if (isMounted) {
          setQrCodeDataUrl(url)
        }
      })
      .catch((err) => {
        console.error('QR code generation error:', err)
      })

    return () => {
      isMounted = false
    }
  }, [activeJoinUrl])

  const copyPassword = () => {
    if (tunnelInfo?.password) {
      navigator.clipboard.writeText(tunnelInfo.password)
      setCopiedPass(true)
      setTimeout(() => setCopiedPass(false), 2000)
    }
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5 text-left">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isTunnelActive ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
            }`}
          />
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            {isTunnelActive ? 'Nyilvános Mobil Tunnel' : 'Helyi Wi-Fi Csatlakozás'}
          </span>
        </div>
        <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
          PIN: DEMO01
        </span>
      </div>

      {/* QR Code Container */}
      <div className="flex flex-col items-center justify-center p-4 bg-slate-50 border border-slate-100 rounded-xl">
        {qrCodeDataUrl ? (
          <img
            src={qrCodeDataUrl}
            alt="Mobil Csatlakozás QR Kód"
            className="w-48 h-48 rounded-lg shadow-2xs border border-slate-200 bg-white p-1.5"
          />
        ) : (
          <div className="w-48 h-48 rounded-lg bg-slate-200 animate-pulse flex items-center justify-center text-xs text-slate-400">
            QR Kód generálása...
          </div>
        )}
        <p className="text-xs text-slate-500 font-medium mt-3 text-center">
          Olvasd be a telefonod kamerájával a gyors belépéshez!
        </p>
      </div>

      {/* Connection Details */}
      <div className="space-y-2.5 text-xs">
        <div>
          <span className="text-slate-500 block mb-0.5 font-medium">Közvetlen Webcím:</span>
          <a
            href={activeJoinUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-blue-600 hover:text-blue-700 hover:underline font-semibold break-all inline-flex items-center gap-1"
          >
            {activeJoinUrl}
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>

        {isTunnelActive && tunnelInfo?.password && (
          <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] text-blue-900 font-bold">
                Tunnel Jelszó (ha a weboldal kéri):
              </div>
              <div className="font-mono text-xs font-black text-blue-800 tracking-wider">
                {tunnelInfo.password}
              </div>
            </div>
            <button
              type="button"
              onClick={copyPassword}
              className="px-2.5 py-1.5 bg-white border border-blue-300 hover:bg-blue-50 text-blue-700 rounded-lg text-xs font-semibold cursor-pointer transition shadow-2xs shrink-0"
            >
              {copiedPass ? 'Másolva!' : 'Másolás'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
