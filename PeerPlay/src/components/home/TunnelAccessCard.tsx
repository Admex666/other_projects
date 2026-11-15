'use client'

import { useEffect, useState, useMemo, useRef } from 'react'
import QRCode from 'qrcode'

interface TunnelInfo {
  active?: boolean
  provider?: string
  port?: number
  url?: string
  joinUrl?: string
  password?: string
  lanIp?: string
  lanUrl?: string
  lanJoinUrl?: string
  status?: string
  errorMessage?: string
  updatedAt?: string
}

export default function TunnelAccessCard() {
  const [tunnelInfo, setTunnelInfo] = useState<TunnelInfo | null>(null)
  const [networkLanIp, setNetworkLanIp] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'wifi' | 'internet'>('wifi')
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>('')
  const [copiedUrl, setCopiedUrl] = useState(false)
  const [fallbackJoinUrl, setFallbackJoinUrl] = useState('http://localhost:3000/join')
  const autoSwitchedRef = useRef(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const host = window.location.hostname || 'localhost'
      const port = window.location.port ? `:${window.location.port}` : ''
      const protocol = window.location.protocol || 'http:'
      setFallbackJoinUrl(`${protocol}//${host}${port}/join`)
    }
  }, [])

  useEffect(() => {
    let isMounted = true
    fetch('/api/network-info')
      .then((res) => res.json())
      .then((data) => {
        if (isMounted && data?.lanIp) {
          setNetworkLanIp(data.lanIp)
        }
      })
      .catch(() => {})
    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    let isMounted = true
    const checkTunnel = async () => {
      try {
        const res = await fetch(`/tunnel-info.json?t=${Date.now()}`)
        if (res.ok) {
          const data: TunnelInfo = await res.json()
          if (isMounted) {
            setTunnelInfo(data)
            if (
              !autoSwitchedRef.current &&
              data?.active &&
              data?.joinUrl &&
              data?.provider === 'cloudflare'
            ) {
              autoSwitchedRef.current = true
              setActiveTab('internet')
            }
          }
        }
      } catch {}
    }

    checkTunnel()
    const interval = setInterval(checkTunnel, 3000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  const effectiveLanJoinUrl = useMemo(() => {
    if (tunnelInfo?.lanJoinUrl) return tunnelInfo.lanJoinUrl
    const detectedIp = networkLanIp || tunnelInfo?.lanIp
    if (detectedIp && typeof window !== 'undefined') {
      const port = window.location.port ? `:${window.location.port}` : ':3000'
      return `http://${detectedIp}${port}/join`
    }
    return fallbackJoinUrl
  }, [tunnelInfo?.lanJoinUrl, tunnelInfo?.lanIp, networkLanIp, fallbackJoinUrl])

  const isInternetTunnelActive = Boolean(
    tunnelInfo?.active && tunnelInfo?.joinUrl && tunnelInfo?.url
  )

  const displayedJoinUrl = useMemo(() => {
    if (activeTab === 'internet' && isInternetTunnelActive && tunnelInfo?.joinUrl) {
      return tunnelInfo.joinUrl
    }
    return effectiveLanJoinUrl
  }, [activeTab, isInternetTunnelActive, tunnelInfo?.joinUrl, effectiveLanJoinUrl])

  useEffect(() => {
    let isMounted = true
    QRCode.toDataURL(displayedJoinUrl, {
      width: 180,
      margin: 1,
      color: {
        dark: '#0f172a',
        light: '#ffffff',
      },
    })
      .then((url) => {
        if (isMounted) setQrCodeDataUrl(url)
      })
      .catch(() => {})
    return () => {
      isMounted = false
    }
  }, [displayedJoinUrl])

  const copyUrl = () => {
    navigator.clipboard.writeText(displayedJoinUrl)
    setCopiedUrl(true)
    setTimeout(() => setCopiedUrl(false), 2000)
  }

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-3 text-left">
      {/* Header & Tabs in one compact row */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              activeTab === 'wifi' || isInternetTunnelActive
                ? 'bg-emerald-500'
                : 'bg-amber-400'
            }`}
          />
          <span className="text-xs font-bold text-slate-800">
            Mobil Belépés (PIN: <span className="font-mono text-blue-600">DEMO01</span>)
          </span>
        </div>

        <div className="inline-flex p-0.5 bg-slate-200/80 rounded-lg text-[11px] font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('wifi')}
            className={`px-2.5 py-1 rounded-md transition cursor-pointer ${
              activeTab === 'wifi'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Helyi Wi-Fi
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('internet')}
            className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1 ${
              activeTab === 'internet'
                ? 'bg-white text-blue-700 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>Internet</span>
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isInternetTunnelActive ? 'bg-emerald-500' : 'bg-slate-400'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Compact QR + URL */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white border border-slate-200 rounded-lg p-3">
        {qrCodeDataUrl ? (
          <img
            src={qrCodeDataUrl}
            alt="QR Kód"
            className="w-32 h-32 rounded border border-slate-100 shrink-0"
          />
        ) : (
          <div className="w-32 h-32 rounded bg-slate-100 animate-pulse shrink-0" />
        )}

        <div className="flex-1 min-w-0 w-full space-y-2 text-center sm:text-left">
          <div className="text-[11px] text-slate-500 font-medium">
            Olvasd be kamerával vagy nyisd meg:
          </div>
          <a
            href={displayedJoinUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs text-blue-600 hover:underline font-bold break-all block"
          >
            {displayedJoinUrl}
          </a>
          <button
            type="button"
            onClick={copyUrl}
            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-semibold cursor-pointer transition"
          >
            {copiedUrl ? 'Link másolva!' : 'Link másolása'}
          </button>
        </div>
      </div>
    </div>
  )
}
