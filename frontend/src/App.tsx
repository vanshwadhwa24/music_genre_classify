import React, { useState, useEffect, useCallback } from 'react'
import { WifiOff } from 'lucide-react'

import { Navbar, type NavTab } from './components/Navbar'
import { DiscoverPage } from './pages/DiscoverPage'
import { LivePage } from './pages/LivePage'
import { AboutPage } from './pages/AboutPage'
import { apiService } from './services/api'
import { NeonLogo } from './components/NeonLogo'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export const App: React.FC = () => {
  const getTabFromHash = (): NavTab => {
    const hash = window.location.hash.replace('#', '').toLowerCase()
    if (hash === 'live' || hash === 'about') return hash
    return 'discover'
  }

  const [currentTab, setCurrentTab] = useState<NavTab>(getTabFromHash)
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null)
  const [isCheckingHealth, setIsCheckingHealth] = useState<boolean>(false)
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine)
  const [deferredInstallPrompt, setDeferredInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  const handleSelectTab = (tab: NavTab) => {
    setCurrentTab(tab)
    window.location.hash = tab
  }

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentTab(getTabFromHash())
    }
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const checkHealth = useCallback(async () => {
    setIsCheckingHealth(true)
    try {
      const res = await apiService.checkHealth()
      setIsBackendHealthy(res.status === 'healthy')
    } catch {
      setIsBackendHealthy(false)
    } finally {
      setIsCheckingHealth(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()

    // Periodic health heartbeat every 15 seconds
    const interval = setInterval(checkHealth, 15000)

    // Online / Offline listeners
    const handleOnline = () => {
      setIsOffline(false)
      checkHealth()
    }
    const handleOffline = () => setIsOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // PWA Install prompt listener
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredInstallPrompt(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handleBeforeInstall)

    return () => {
      clearInterval(interval)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
    }
  }, [checkHealth])

  const handleInstallPwa = async () => {
    if (!deferredInstallPrompt) return
    await deferredInstallPrompt.prompt()
    const { outcome } = await deferredInstallPrompt.userChoice
    if (outcome === 'accepted') {
      setDeferredInstallPrompt(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#1A0536] text-[#1A0536] flex flex-col selection:bg-[#FF3CAC] selection:text-[#1A0536]">
      {/* Offline Notification Banner */}
      {isOffline && (
        <div className="bg-[#FFB347] border-b-2 border-[#FF3CAC] px-4 py-2.5 text-center text-xs font-bold text-[#1A0536] flex items-center justify-center gap-2">
          <WifiOff className="w-4 h-4" />
          <span>
            YOU ARE OFFLINE · The application shell is cached via PWA, but genre inference requires a live backend.
          </span>
        </div>
      )}

      {/* Main Navigation */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
        isBackendHealthy={isBackendHealthy}
        onRetryConnection={checkHealth}
        isCheckingHealth={isCheckingHealth}
        canInstallPwa={deferredInstallPrompt !== null}
        onInstallPwa={handleInstallPwa}
      />

      {/* Page Content */}
      <main className="flex-1 w-full">
        {currentTab === 'discover' && (
          <DiscoverPage isBackendHealthy={isBackendHealthy} />
        )}
        {currentTab === 'live' && (
          <LivePage isBackendHealthy={isBackendHealthy} />
        )}
        {currentTab === 'about' && <AboutPage />}
      </main>

      {/* Playful Editorial Footer */}
      <footer className="border-t-2 border-[#FF3CAC] bg-[#FFB347] py-8 px-4 text-xs font-bold text-[#1A0536]">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm flex items-center justify-center overflow-hidden">
              <NeonLogo size={40} variant="icon" />
            </div>
            <div>
              <span className="text-xl font-display tracking-tight text-[#FFE9FF] leading-none block">
                NEON RADIO
              </span>
              <span className="text-[11px] font-mono text-[#FFE9FF]/80">
                SOUND, MADE VISIBLE · GTZAN CNN PWA
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 font-mono text-[11px]">
            <span className="bg-[#2A0A4A] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm">
              PYTORCH 2D-CNN
            </span>
            <span className="bg-[#FF3CAC] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm">
              22.05 KHZ MONO
            </span>
            <span className="bg-[#3DFFD0] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm">
              128 MEL BANDS
            </span>
            <span className="bg-[#2A0A4A] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm">
              PWA ENABLED
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
