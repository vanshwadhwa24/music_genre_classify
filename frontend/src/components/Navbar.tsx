import React, { useState } from 'react'
import { Disc, Radio, Info, Download, RefreshCw, Menu, X } from 'lucide-react'
import { NeonLogo } from './NeonLogo'

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
    <header className="sticky top-0 z-50 w-full border-b-2 border-[#FF3CAC]/60 bg-[#14032A]/90 backdrop-blur shadow-[0_2px_24px_rgba(255,60,172,0.25)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
        {/* Brand Wordmark & Mascot */}
        <div
          onClick={() => handleSelect('discover')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-11 h-11 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm flex items-center justify-center group-hover:rotate-6 transition-transform overflow-hidden">
            <NeonLogo size={46} variant="icon" />
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-2xl sm:text-3xl font-display tracking-tight text-[#FFE9FF] leading-none">
                NEON RADIO
              </span>
              <span className="text-[10px] font-mono font-bold uppercase bg-[#FF3CAC] px-1.5 py-0.5 rounded border border-[#FF3CAC]">
                AI
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#FFE9FF]/80 uppercase">
              Tell your tunes what you&apos;re jamming on
            </span>
          </div>
        </div>

        {/* Center Desktop Navigation */}
        <nav
          className="hidden md:flex items-center gap-2 bg-[#2A0A4A]/70 p-1.5 rounded-2xl border-2 border-[#FF3CAC] shadow-brutal-sm"
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
                    ? 'bg-[#FF3CAC] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm translate-x-[-1px] translate-y-[-1px]'
                    : 'text-[#FFE9FF]/80 hover:bg-[#FF3CAC]/20'
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
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-[#FF3CAC] text-[#1A0536] hover:bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm transition-all brutal-btn"
              title="Install PWA to desktop or mobile home screen"
            >
              <Download className="w-3.5 h-3.5" />
              <span>INSTALL</span>
            </button>
          )}

          {/* Backend Health Status badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm text-xs font-mono font-bold">
            <span
              className={`w-2.5 h-2.5 rounded-full border border-[#FF3CAC] ${
                isBackendHealthy === true
                  ? 'bg-[#3DFFD0] shadow-[0_0_8px_#3DFFD0]'
                  : isBackendHealthy === false
                  ? 'bg-[#FF6B8A] shadow-[0_0_8px_#FF6B8A]'
                  : 'bg-[#FFB347]'
              }`}
            />
            <span className="text-[#FFE9FF]">
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
                className="ml-1 p-0.5 rounded text-[#FFE9FF] hover:text-[#FF6B8A] transition-colors"
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
              className="p-2 rounded-xl bg-[#FF3CAC] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm"
              aria-label="Install app"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl bg-[#2A0A4A] text-[#FFE9FF] border-2 border-[#FF3CAC] shadow-brutal-sm"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t-2 border-[#FF3CAC] bg-[#1A0536] px-4 py-4 space-y-2">
          {navItems.map((item) => {
            const isActive = currentTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-base font-bold transition-all ${
                  isActive
                    ? 'bg-[#FF3CAC] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm'
                    : 'text-[#1A0536] bg-[#2A0A4A] border-2 border-[#FF3CAC]'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            )
          })}

          <div className="pt-3 border-t-2 border-[#FF3CAC]/20 flex items-center justify-between text-xs font-mono font-bold text-[#FFE9FF]">
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full border border-[#FF3CAC] ${
                  isBackendHealthy ? 'bg-[#3DFFD0]' : 'bg-[#FF6B8A]'
                }`}
              />
              <span>{isBackendHealthy ? 'Backend Connected' : 'Backend Offline'}</span>
            </div>
            {isBackendHealthy === false && (
              <button
                onClick={onRetryConnection}
                className="px-3 py-1 rounded-lg bg-[#FFB347] border border-[#FF3CAC] text-[#1A0536]"
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
