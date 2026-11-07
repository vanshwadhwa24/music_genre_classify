import React, { useState } from 'react'
import { Disc, Radio, Info, Download, RefreshCw, Menu, X } from 'lucide-react'
import { JambirdMascot } from './JambirdMascot'

export type NavTab = 'discover' | 'live' | 'about'

interface NavbarProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
  isBackendHealthy: boolean | null
  onRetryConnection: () => void
  isCheckingHealth: boolean
  canInstallPwa: boolean
  onInstallPwa: () => void
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  isBackendHealthy,
  onRetryConnection,
  isCheckingHealth,
  canInstallPwa,
  onInstallPwa,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'discover', label: 'Discover', icon: <Disc className="w-4 h-4" /> },
    { id: 'live', label: 'Live', icon: <Radio className="w-4 h-4" /> },
    { id: 'about', label: 'About', icon: <Info className="w-4 h-4" /> },
  ]

  const handleSelect = (tab: NavTab) => {
    onSelectTab(tab)
    setMobileMenuOpen(false)
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b-2 border-[#4B2B23] bg-[#FFDF43] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
        {/* Brand Wordmark & Mascot */}
        <div
          onClick={() => handleSelect('discover')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-11 h-11 rounded-xl bg-white border-2 border-[#4B2B23] shadow-brutal-sm flex items-center justify-center group-hover:rotate-6 transition-transform overflow-hidden">
            <JambirdMascot size={46} variant="icon" />
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-2xl sm:text-3xl font-display tracking-tight text-[#4B2B23] leading-none">
                JAMBIRD
              </span>
              <span className="text-[10px] font-mono font-bold uppercase bg-[#F49ACB] px-1.5 py-0.5 rounded border border-[#4B2B23]">
                AI
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#4B2B23]/80 uppercase">
              Tell your tunes what you&apos;re jamming on
            </span>
          </div>
        </div>

        {/* Center Desktop Navigation */}
        <nav
          className="hidden md:flex items-center gap-2 bg-white/70 p-1.5 rounded-2xl border-2 border-[#4B2B23] shadow-brutal-sm"
          aria-label="Main Navigation"
        >
          {navItems.map((item) => {
            const isActive = currentTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-bold transition-all ${
                  isActive
                    ? 'bg-[#F49ACB] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm translate-x-[-1px] translate-y-[-1px]'
                    : 'text-[#4B2B23] hover:bg-[#FFF9E9]'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <span>{item.icon}</span>
                <span className="tracking-wide">{item.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Right Action Area */}
        <div className="hidden md:flex items-center gap-3">
          {/* PWA Install Button */}
          {canInstallPwa && (
            <button
              onClick={onInstallPwa}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-[#F49ACB] text-[#4B2B23] hover:bg-white border-2 border-[#4B2B23] shadow-brutal-sm transition-all brutal-btn"
              title="Install PWA to desktop or mobile home screen"
            >
              <Download className="w-3.5 h-3.5" />
              <span>INSTALL</span>
            </button>
          )}

          {/* Backend Health Status badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border-2 border-[#4B2B23] shadow-brutal-sm text-xs font-mono font-bold">
            <span
              className={`w-2.5 h-2.5 rounded-full border border-[#4B2B23] ${
                isBackendHealthy === true
                  ? 'bg-[#288C56] shadow-[0_0_8px_#288C56]'
                  : isBackendHealthy === false
                  ? 'bg-[#E5484D] shadow-[0_0_8px_#E5484D]'
                  : 'bg-[#FFDF43]'
              }`}
            />
            <span className="text-[#4B2B23]">
              {isBackendHealthy === true
                ? 'ONLINE'
                : isBackendHealthy === false
                ? 'OFFLINE'
                : 'CHECKING...'}
            </span>

            {isBackendHealthy === false && (
              <button
                onClick={onRetryConnection}
                disabled={isCheckingHealth}
                className="ml-1 p-0.5 rounded text-[#4B2B23] hover:text-[#E5484D] transition-colors"
                title="Retry backend connection"
                aria-label="Retry backend connection"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isCheckingHealth ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex md:hidden items-center gap-2">
          {canInstallPwa && (
            <button
              onClick={onInstallPwa}
              className="p-2 rounded-xl bg-[#F49ACB] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm"
              aria-label="Install app"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl bg-white text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t-2 border-[#4B2B23] bg-[#FFF9E9] px-4 py-4 space-y-2">
          {navItems.map((item) => {
            const isActive = currentTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-base font-bold transition-all ${
                  isActive
                    ? 'bg-[#F49ACB] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm'
                    : 'text-[#4B2B23] bg-white border-2 border-[#4B2B23]'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            )
          })}

          <div className="pt-3 border-t-2 border-[#4B2B23]/20 flex items-center justify-between text-xs font-mono font-bold text-[#4B2B23]">
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full border border-[#4B2B23] ${
                  isBackendHealthy ? 'bg-[#288C56]' : 'bg-[#E5484D]'
                }`}
              />
              <span>{isBackendHealthy ? 'Backend Connected' : 'Backend Offline'}</span>
            </div>
            {isBackendHealthy === false && (
              <button
                onClick={onRetryConnection}
                className="px-3 py-1 rounded-lg bg-[#FFDF43] border border-[#4B2B23] text-[#4B2B23]"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
