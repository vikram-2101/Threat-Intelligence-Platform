import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  Shield, 
  ArrowRight, 
  CheckCircle2, 
  Layers, 
  Activity, 
  Database, 
  RefreshCw, 
  Eye, 
  AlertTriangle, 
  Clock, 
  Cpu,
  Zap,
  ChevronDown,
  Cloud,
  Link as LinkIcon
} from 'lucide-react'


function TiltCard({ children, borderHoverClass, shadowHoverClass }: { children: React.ReactNode, borderHoverClass: string, shadowHoverClass: string }) {
  const [rotateX, setRotateX] = useState(0)
  const [rotateY, setRotateY] = useState(0)
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget
    const rect = card.getBoundingClientRect()
    const width = rect.width
    const height = rect.height
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const xPct = (mouseX / width) - 0.5
    const yPct = (mouseY / height) - 0.5
    const maxTilt = 12
    setRotateY(xPct * maxTilt)
    setRotateX(-yPct * maxTilt)
  }

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false)
        setRotateX(0)
        setRotateY(0)
      }}
      className={`bg-surface-900 border border-slate-800/80 p-8 rounded-2xl transition-all duration-300 group flex flex-col justify-between select-none relative ${isHovered ? borderHoverClass + ' ' + shadowHoverClass : ''}`}
      style={{
        transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(${isHovered ? 1.02 : 1}, ${isHovered ? 1.02 : 1}, 1)`,
        transition: isHovered ? 'none' : 'all 0.4s ease-out',
        transformStyle: 'preserve-3d'
      }}
    >
      <div 
        style={{ 
          transform: isHovered ? 'translateZ(30px)' : 'translateZ(0px)',
          transition: isHovered ? 'none' : 'all 0.4s ease-out'
        }}
      >
        {children}
      </div>
    </div>
  )
}

export function LandingPage() {
  const navigate = useNavigate()

  
  // Dynamic typing-like fade effects for raw feed to enriched intelligence in hero
  const [heroTextIndex, setHeroTextIndex] = useState(0)
  const heroKeywords = ["intelligence", "clarity", "evidence", "certainty"]

  useEffect(() => {
    const interval = setInterval(() => {
      setHeroTextIndex((prev) => (prev + 1) % heroKeywords.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="relative bg-surface-950 text-slate-100 min-h-screen font-sans antialiased overflow-x-hidden select-none selection:bg-brand-500/30 selection:text-brand-200">
      
      {/* ── BACKGROUND ENHANCEMENT: World & Globe Overlay ───────────────────── */}
      <div className="absolute inset-0 bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:24px_24px] opacity-25 pointer-events-none z-0" />
      <div className="absolute top-0 inset-x-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),transparent)] pointer-events-none z-0" />

      {/* Hero Global Map Image backdrop */}
      <div className="absolute top-0 right-0 w-full lg:w-1/2 h-[750px] pointer-events-none opacity-20 z-0">
        <img src="/globe.png" alt="Global Network" className="w-full h-full object-contain object-right-top filter grayscale select-none" />
      </div>

      {/* ── SECTION 1: Navbar ────────────────────────────────────────────────── */}
      <header className="sticky top-0 w-full z-50 border-b border-slate-800 bg-surface-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-brand-600/20 border border-brand-500/30 group-hover:bg-brand-600/30 group-hover:border-brand-400/40 transition-all duration-300 shadow-glow-sm">
              <Shield className="w-5 h-5 text-brand-400 group-hover:scale-110 transition-transform duration-300" />
            </div>
            <div>
              <div className="text-base font-bold tracking-wider text-slate-100 bg-clip-text">THREATLENS</div>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-800/60 px-3 py-1.5 rounded-lg transition-all duration-200">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-800/60 px-3 py-1.5 rounded-lg transition-all duration-200">How It Works</a>
            <a href="#problem" className="text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-800/60 px-3 py-1.5 rounded-lg transition-all duration-200">The Problem</a>
            <a href="#pricing" className="text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-800/60 px-3 py-1.5 rounded-lg transition-all duration-200">Pricing</a>
          </nav>

          {/* CTA Button */}
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-semibold text-slate-400 hover:text-slate-100 px-3 py-2 transition-colors">Sign In</Link>
            <button 
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 border border-brand-500/30 rounded-lg shadow-glow hover:shadow-glow-sm hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 select-none"
            >
              Start Scanning
            </button>
          </div>
        </div>
      </header>

      {/* ── SECTION 2: Hero Section ─────────────────────────────────────────── */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 md:pt-24 pb-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center z-10">
        
        {/* Left Side: Copy */}
        <div className="lg:col-span-6 flex flex-col justify-center animate-fade-in">
          
          {/* Accent tag */}
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-600/10 border border-brand-500/20 rounded-full w-fit mb-6 animate-pulse-slow">
            <Zap className="w-3.5 h-3.5 text-brand-400" />
            <span className="text-xs font-semibold text-brand-300 tracking-wider uppercase">Enrichment-Driven Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 mb-6 leading-[1.1]">
            Raw feeds don't equal <span className="text-brand-400 bg-clip-text">{heroKeywords[heroTextIndex]}</span>. This does.
          </h1>

          <p className="text-base sm:text-lg text-slate-400 mb-8 max-w-xl leading-relaxed">
            ThreatLens ingests raw indicators, enriches them with independent evidence, correlates across sources, and scores confidence to deliver actionable insights, not just data dumps.
          </p>

          {/* CTA Actions */}
          <div className="flex flex-wrap items-center gap-4 mb-8">
            <button 
              onClick={() => navigate('/login')}
              className="px-6 py-3.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-lg shadow-glow hover:shadow-glow-sm hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 flex items-center gap-2 select-none"
            >
              Request Early Access
              <ArrowRight className="w-4 h-4" />
            </button>
            <a 
              href="#how-it-works"
              className="px-6 py-3.5 bg-surface-800 hover:bg-surface-700 text-slate-200 hover:text-slate-100 font-semibold border border-slate-700/50 rounded-lg hover:border-slate-600/80 transition-all duration-200 flex items-center gap-2 select-none"
            >
              See How It Works
              <ChevronDown className="w-4 h-4 animate-bounce" />
            </a>
          </div>

          {/* Core Trust Pillars */}
          <div className="flex items-center gap-2.5 text-xs sm:text-sm text-slate-500 border-t border-slate-800/80 pt-6 mt-4">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500/80 animate-pulse inline-block" />
            No automated blocking. No black-box scores. Human approval, always.
          </div>
        </div>

        {/* Right Side: Hero Floating Visual Panel */}
        <div className="lg:col-span-6 flex justify-center lg:justify-end animate-slide-up select-none">
          <div className="relative max-w-md w-full bg-surface-900 border border-slate-800 p-6 rounded-2xl shadow-2xl backdrop-blur-sm hover:border-slate-700/80 hover:shadow-brand-500/10 transition-all duration-500 group select-none">
            
            {/* Corner Light glow */}
            <div className="absolute -top-3 -right-3 w-32 h-32 bg-brand-600/10 blur-3xl pointer-events-none group-hover:bg-brand-500/20 transition-all duration-500" />
            
            {/* Top right floating Badge */}
            <div className="absolute top-4 right-4 bg-brand-900/40 border border-brand-500/30 px-2.5 py-1 rounded-md flex items-center gap-1.5 shadow-glow-sm animate-pulse-slow">
              <Cpu className="w-3 h-3 text-brand-300" />
              <span className="text-[10px] text-brand-200 uppercase font-mono font-bold tracking-widest">Correlation</span>
            </div>

            {/* Indicator Details */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
              <span className="px-2 py-0.5 bg-surface-800 border border-slate-700 text-slate-400 font-mono text-xs rounded-md">IPv4</span>
              <span className="px-2 py-0.5 bg-green-500/10 border border-green-500/20 text-green-400 font-mono text-xs rounded-md">ACTIVE</span>
            </div>

            <div className="text-xs text-slate-500 font-medium mb-1 tracking-widest uppercase">Indicator</div>
            <div className="text-2xl sm:text-3xl font-mono font-bold text-slate-200 tracking-tight mb-6">
              185.220.101.47
            </div>

            {/* Score Display */}
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs tracking-wider uppercase text-slate-400 font-medium">Confidence Score</div>
              <div className="text-xl font-bold text-slate-100 font-mono">
                73 <span className="text-sm font-normal text-slate-500">/ 100</span>
              </div>
            </div>

            {/* Score Bar */}
            <div className="w-full bg-surface-800 border border-slate-700/50 h-3 rounded-full overflow-hidden mb-6 flex items-center p-0.5 select-none">
              <div className="bg-gradient-to-r from-brand-500 to-blue-500 h-2 rounded-full transition-all duration-1000 w-[73%]" />
            </div>

            {/* Quick Filter Tag Buttons */}
            <div className="flex flex-wrap items-center gap-2 mb-6">
              <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-green-500/10 border border-green-500/20 text-[11px] font-semibold text-green-300 rounded-lg">
                <CheckCircle2 className="w-3 h-3" /> ASN Match
              </span>
              <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-blue-500/10 border border-blue-500/20 text-[11px] font-semibold text-blue-300 rounded-lg">
                <CheckCircle2 className="w-3 h-3" /> Historical
              </span>
            </div>

            {/* Enrichment Timeline */}
            <div className="text-xs font-semibold text-slate-400 mb-3 tracking-wider uppercase border-b border-slate-800 pb-2 flex items-center justify-between">
              <span>Enrichment Evidence</span>
              <span className="text-[10px] text-slate-600 font-mono">Realtime updates</span>
            </div>

            <div className="space-y-2 select-none">
              <div className="flex items-center justify-between p-3 bg-surface-850/60 border border-slate-800/40 rounded-xl hover:bg-surface-800 hover:border-slate-700/50 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-slate-500">10:42</span>
                  <span className="text-xs text-slate-300 font-medium">WHOIS Record Updated</span>
                </div>
                <span className="text-xs font-mono font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20">+8</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-850/60 border border-slate-800/40 rounded-xl hover:bg-surface-800 hover:border-slate-700/50 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-slate-500">10:45</span>
                  <span className="text-xs text-slate-300 font-medium">ASN Reputation Drop</span>
                </div>
                <span className="text-xs font-mono font-bold text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded border border-orange-500/20">+12</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-850/60 border border-slate-800/40 rounded-xl hover:bg-surface-800 hover:border-slate-700/50 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-slate-500">11:02</span>
                  <span className="text-xs text-slate-300 font-medium">Passive DNS Resolution</span>
                </div>
                <span className="text-xs font-mono font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20">+5</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 3: Problem Section ────────────────────────────────────────── */}
      <section id="problem" className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 z-10 border-t border-slate-900 select-none">
        
        {/* Label & Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="text-xs font-bold tracking-widest text-red-400 uppercase mb-3">The Intelligence Gap</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mb-5 leading-tight">
            Stop trusting raw data blindly.
          </h2>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            Feeds are filled with contextless, misleading information. Without clear context, scoring justification, and dynamic updates, raw indicators cause alert fatigue and unmitigated risk.
          </p>
        </div>

        {/* 3 Grid Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <TiltCard borderHoverClass="hover:border-red-500/30" shadowHoverClass="hover:shadow-red-500/5">
            <div className="flex flex-col justify-between h-full min-h-[300px]">
              <div>
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 group-hover:bg-red-500/20 group-hover:border-red-400/40 transition-all duration-300 mb-6 select-none">
                  <Database className="w-5 h-5 text-red-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-100 mb-3 group-hover:text-red-300 transition-colors duration-300 select-none">
                  Raw feeds have no context
                </h3>
                <p className="text-slate-400 group-hover:text-slate-300 text-sm leading-relaxed transition-colors duration-300 select-none">
                  Most threat databases only collect indicators. They don't provide enrichment data like reverse DNS or SSL certificates, forcing analysts to manually check every alarm.
                </p>
              </div>
              <div className="border-t border-slate-800/60 pt-4 mt-6 text-xs text-red-400/60 font-medium">Result: High operational fatigue</div>
            </div>
          </TiltCard>

          <TiltCard borderHoverClass="hover:border-orange-500/30" shadowHoverClass="hover:shadow-orange-500/5">
            <div className="flex flex-col justify-between h-full min-h-[300px]">
              <div>
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/20 group-hover:bg-orange-500/20 group-hover:border-orange-400/40 transition-all duration-300 mb-6 select-none">
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-100 mb-3 group-hover:text-orange-300 transition-colors duration-300 select-none">
                  Scores don't explain themselves
                </h3>
                <p className="text-slate-400 group-hover:text-slate-300 text-sm leading-relaxed transition-colors duration-300 select-none">
                  Black-box calculators drop random values from 0 to 100 on indicators. It leaves engineers guessing, completely unable to justify blocking actions to stakeholders.
                </p>
              </div>
              <div className="border-t border-slate-800/60 pt-4 mt-6 text-xs text-orange-400/60 font-medium">Result: Decision paralysis</div>
            </div>
          </TiltCard>

          <TiltCard borderHoverClass="hover:border-amber-500/30" shadowHoverClass="hover:shadow-amber-500/5">
            <div className="flex flex-col justify-between h-full min-h-[300px]">
              <div>
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 group-hover:bg-amber-500/20 group-hover:border-amber-400/40 transition-all duration-300 mb-6 select-none">
                  <Clock className="w-5 h-5 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-100 mb-3 group-hover:text-amber-300 transition-colors duration-300 select-none">
                  Stale data is dangerous
                </h3>
                <p className="text-slate-400 group-hover:text-slate-300 text-sm leading-relaxed transition-colors duration-300 select-none">
                  Indicator details change within minutes. Yesterday's malware hub is today's clean cloud endpoint. Without continuous time decay, you are doomed to false positives.
                </p>
              </div>
              <div className="border-t border-slate-800/60 pt-4 mt-6 text-xs text-amber-400/60 font-medium">Result: Massive false positives</div>
            </div>
          </TiltCard>
        </div>
      </section>

      {/* ── SECTION 4: Pipeline / How it Works ───────────────────────────────── */}
      <section id="how-it-works" className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 z-10 border-t border-slate-900 select-none">
        
        {/* World Map Backdrop for Workflow */}
        <div className="absolute inset-0 bg-cover bg-center opacity-10 pointer-events-none z-0 filter saturate-0 select-none" style={{ backgroundImage: "url('/world.png')" }} />

        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 select-none relative z-10">
          <div className="text-xs font-bold tracking-widest text-brand-400 uppercase mb-3 flex items-center justify-center gap-1.5 select-none">
            <span className="w-5 h-[1px] bg-brand-500 inline-block" />
            HOW IT WORKS
            <span className="w-5 h-[1px] bg-brand-500 inline-block" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mb-5 leading-snug select-none">
            Seven steps from raw noise to defensible intelligence.
          </h2>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed select-none">
            Every indicator passes through the same rigorous pipeline. Nothing is classified automatically. Every decision is traceable.
          </p>
        </div>

        {/* Middle server layout illustration copied from screenshot */}
        <div className="relative max-w-4xl mx-auto mb-16 flex justify-center z-10 select-none">
          <div className="relative w-full max-w-md bg-surface-900/40 border border-slate-800/80 p-1.5 rounded-2xl shadow-xl hover:border-slate-700/60 hover:shadow-brand-500/5 transition-all duration-500 group select-none">
            {/* Embedded glowing isometric server illustration */}
            <div className="aspect-[16/10] bg-surface-950/80 rounded-xl overflow-hidden border border-slate-800/60 flex items-center justify-center relative select-none">
              <div className="absolute inset-0 bg-gradient-to-t from-transparent to-brand-500/10 pointer-events-none z-10" />
              <img src="/work section.png" alt="Server Infrastructure Illustration" className="w-full h-full object-cover select-none" />
            </div>
          </div>
        </div>

        {/* Step Cards Horizontal Layout from 2nd Image */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 mb-12 relative z-10 select-none">
          
          {/* Card 01 Ingest */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>01</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">INGEST</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">01 INGEST</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Raw indicators enter from any source.</p>
            </div>
            <div className="mt-auto flex justify-center py-2.5 border border-dashed border-slate-800/80 bg-surface-850/50 rounded-lg group-hover:border-brand-500/20 group-hover:bg-brand-500/5 transition-all duration-300 select-none">
              <Cloud className="w-4 h-4 text-slate-500 group-hover:text-brand-400 transition-colors" />
            </div>
          </div>

          {/* Card 02 Normalize */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>02</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">NORMALIZE</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">02 NORMALIZE</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Every indicator is validated.</p>
            </div>
            <div className="mt-auto flex justify-center py-2 border border-dashed border-slate-800/80 bg-surface-850/50 rounded-lg group-hover:border-brand-500/20 group-hover:bg-brand-500/5 transition-all duration-300 select-none">
              <span className="text-[10px] font-mono font-bold text-slate-400 group-hover:text-brand-300 tracking-wider flex items-center gap-1 select-none">
                <CheckCircle2 className="w-3 h-3" /> MERGED
              </span>
            </div>
          </div>

          {/* Card 03 Enrich */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>03</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">ENRICH</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">03 ENRICH</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Independent evidence is gathered.</p>
            </div>
            <div className="mt-auto flex justify-center py-1.5 border border-dashed border-slate-800/80 bg-surface-850/50 rounded-lg group-hover:border-brand-500/20 group-hover:bg-brand-500/5 transition-all duration-300 select-none">
              <Layers className="w-4 h-4 text-slate-500 group-hover:text-brand-400 transition-colors" />
            </div>
          </div>

          {/* Card 04 Correlate */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>04</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">CORRELATE</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">04 CORRELATE</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Indicators sharing infrastructure are linked.</p>
            </div>
            <div className="mt-auto flex justify-center py-2 border border-dashed border-slate-800/80 bg-surface-850/50 rounded-lg group-hover:border-brand-500/20 group-hover:bg-brand-500/5 transition-all duration-300 select-none">
              <LinkIcon className="w-4 h-4 text-slate-500 group-hover:text-brand-400 transition-colors select-none" />
            </div>
          </div>

          {/* Card 05 Score */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>05</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">SCORE</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">05 SCORE</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Confidence is calculated.</p>
            </div>
            <div className="mt-auto flex flex-col gap-1 select-none">
              <div className="flex justify-between text-[10px] text-slate-400 font-mono group-hover:text-slate-300 select-none">
                <span>CONFIDENCE</span>
                <span>73%</span>
              </div>
              <div className="w-full bg-surface-800 h-1.5 rounded-full overflow-hidden flex items-center select-none">
                <div className="bg-gradient-to-r from-brand-500 to-blue-500 h-1 rounded-full transition-all duration-300 w-[73%]" />
              </div>
            </div>
          </div>

          {/* Card 06 Review */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>06</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">REVIEW</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">06 REVIEW</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">A human analyst makes the final call.</p>
            </div>
            <div className="mt-auto flex flex-col gap-1 select-none">
              <span className="text-[9px] py-1 bg-green-500/10 border border-green-500/20 text-green-300 font-bold text-center rounded">PROMOTE</span>
              <span className="text-[9px] py-1 bg-surface-800 border border-slate-700/60 text-slate-400 font-bold text-center rounded">REVOKE</span>
            </div>
          </div>

          {/* Card 07 Export */}
          <div className="bg-surface-900 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between h-[210px] hover:border-brand-500/30 hover:bg-surface-850 hover:shadow-glow-sm hover:scale-[1.02] transition-all duration-300 group select-none">
            <div>
              <div className="text-[11px] font-mono font-extrabold text-brand-300 tracking-wider mb-2 flex justify-between select-none">
                <span>07</span>
                <span className="uppercase text-[9px] bg-brand-500/10 px-1 py-0.5 rounded border border-brand-500/20">EXPORT</span>
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-brand-300 transition-colors mb-2 select-none">07 EXPORT</h4>
              <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors select-none">Enriched intelligence delivered via API.</p>
            </div>
            <div className="mt-auto select-none">
              <div className="flex justify-between text-[8px] text-slate-500 font-mono mb-1 group-hover:text-slate-400 select-none">
                <span>THRESHOLD</span>
                <span>HIGH</span>
              </div>
              <div className="w-full bg-surface-800 h-1 rounded-full overflow-hidden flex items-center relative select-none">
                <div className="absolute right-3 top-0 h-1 w-2 rounded-full bg-orange-500 select-none" />
                <div className="bg-brand-500 h-1 rounded-full w-[70%] select-none" />
              </div>
            </div>
          </div>

        </div>

        {/* Dynamic Trust Card at Bottom */}
        <div className="max-w-4xl mx-auto bg-surface-900 border border-slate-800/80 p-8 rounded-3xl text-center flex flex-col items-center gap-5 relative z-10 select-none">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-brand-500/10 border border-brand-500/20 shadow-glow select-none">
            <Eye className="w-5 h-5 text-brand-400" />
          </div>
          <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 max-w-2xl leading-relaxed select-none">
            "Every step is recorded. Every evidence source is traceable. Every confidence change has a reason. This is not a black box — it's a glass box."
          </h3>
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold tracking-wider text-slate-400 mt-2 select-none">
            <span className="flex items-center gap-2 select-none"><span className="w-1.5 h-1.5 bg-brand-500 rounded-full select-none" /> 7 pipeline stages</span>
            <span className="flex items-center gap-2 select-none"><span className="w-1.5 h-1.5 bg-brand-500 rounded-full select-none" /> 100% traceable</span>
            <span className="flex items-center gap-2 select-none"><span className="w-1.5 h-1.5 bg-brand-500 rounded-full select-none" /> 0 automated blocks</span>
          </div>
        </div>

      </section>

      {/* ── SECTION 5: Features Section ───────────────────────────────────────── */}
      <section id="features" className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 z-10 border-t border-slate-900 select-none">
        
        {/* Title */}
        <div className="text-center max-w-3xl mx-auto mb-20 select-none">
          <div className="text-xs font-bold tracking-widest text-brand-400 uppercase mb-3">Core Platform Features</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mb-5 select-none">
            Built for Analysts Who Need to Explain Decisions
          </h2>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed select-none">
            Say goodbye to black-box conclusions. Every automated intelligence insight produces a clear, auditable evidence trail for your analysts.
          </p>
        </div>

        {/* Feature blocks alternating */}
        <div className="space-y-32 select-none">
          
          {/* Feature Block 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center select-none">
            <div className="lg:col-span-6 animate-fade-in select-none">
              <div className="text-xs font-bold font-mono tracking-widest text-brand-400 uppercase mb-3 flex items-center gap-2 select-none">
                <span className="w-6 h-[1px] bg-brand-500 inline-block select-none" /> Feature 01
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mb-4 tracking-tight leading-snug select-none">
                Confidence That Explains Itself
              </h3>
              <p className="text-slate-400 text-base mb-6 leading-relaxed select-none">
                Our Confidence Scoring is open-book. ThreatLens provides a breakdown of source trust ratings, enrichment depths, multi-feed overlap counts, and dynamic decay values.
              </p>
              <ul className="space-y-3 mb-8 select-none">
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
                  Visual time decay metrics for older evidence
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
                  Score weighting fully explainable down to the source
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
                  Clear dynamic adjustments with audit logging
                </li>
              </ul>
            </div>

            {/* Feature Block visual box */}
            <div className="lg:col-span-6 select-none bg-surface-900 border border-slate-800 p-6 rounded-2xl shadow-xl hover:border-slate-700 hover:shadow-brand-500/5 transition-all duration-300 select-none">
              <div className="bg-surface-850 border border-slate-800/80 rounded-xl p-5 select-none">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800 select-none">
                  <div className="flex items-center gap-2 select-none">
                    <RefreshCw className="w-4 h-4 text-brand-400" />
                    <span className="text-xs font-bold text-slate-300 tracking-wider">Scoring Breakdown</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-brand-300 bg-brand-500/10 border border-brand-500/20 px-2 py-0.5 rounded">73/100</span>
                </div>
                <div className="space-y-4 select-none">
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium select-none">
                      <span>Source Trust</span>
                      <span className="font-mono text-slate-300">88%</span>
                    </div>
                    <div className="w-full bg-surface-800 h-1.5 rounded-full overflow-hidden flex items-center select-none">
                      <div className="bg-brand-500 h-1 rounded-full transition-all duration-300 w-[88%] select-none" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium select-none">
                      <span>Enrichment Validity</span>
                      <span className="font-mono text-slate-300">76%</span>
                    </div>
                    <div className="w-full bg-surface-800 h-1.5 rounded-full overflow-hidden flex items-center select-none">
                      <div className="bg-brand-500 h-1 rounded-full transition-all duration-300 w-[76%] select-none" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium select-none">
                      <span>Time Decay Penalty</span>
                      <span className="font-mono text-red-400">-12%</span>
                    </div>
                    <div className="w-full bg-surface-800 h-1.5 rounded-full overflow-hidden flex items-center select-none">
                      <div className="bg-red-500/80 h-1 rounded-full transition-all duration-300 w-[12%] select-none" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature Block 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center select-none">
            {/* Visual first (alternating layout) */}
            <div className="lg:col-span-6 select-none bg-surface-900 border border-slate-800 p-6 rounded-2xl shadow-xl hover:border-slate-700 hover:shadow-brand-500/5 transition-all duration-300 order-last lg:order-first select-none">
              <div className="bg-surface-850 border border-slate-800/80 rounded-xl p-5 select-none">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800 select-none">
                  <div className="flex items-center gap-2 select-none">
                    <Layers className="w-4 h-4 text-brand-400" />
                    <span className="text-xs font-bold text-slate-300 tracking-wider">Enrichment Trail</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-brand-300 bg-brand-500/10 border border-brand-500/20 px-2 py-0.5 rounded">HISTORIC</span>
                </div>
                <div className="space-y-2 text-xs select-none">
                  <div className="p-2.5 bg-surface-800 rounded-lg border border-slate-700/50 flex justify-between items-center select-none">
                    <span className="text-slate-300 font-medium">WHOIS Registration Date</span>
                    <span className="font-mono text-brand-400 font-semibold">2026-03-24</span>
                  </div>
                  <div className="p-2.5 bg-surface-800 rounded-lg border border-slate-700/50 flex justify-between items-center select-none">
                    <span className="text-slate-300 font-medium">ISP Name (ASN)</span>
                    <span className="font-mono text-brand-400 font-semibold">Cloudflare, Inc.</span>
                  </div>
                  <div className="p-2.5 bg-surface-800 rounded-lg border border-slate-700/50 flex justify-between items-center select-none">
                    <span className="text-slate-300 font-medium">Passive DNS Lookups</span>
                    <span className="font-mono text-brand-400 font-semibold">4 active records</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-6 animate-fade-in select-none">
              <div className="text-xs font-bold font-mono tracking-widest text-brand-400 uppercase mb-3 flex items-center gap-2 select-none">
                <span className="w-6 h-[1px] bg-brand-500 inline-block select-none" /> Feature 02
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mb-4 tracking-tight leading-snug select-none">
                Enrichment as Evidence
              </h3>
              <p className="text-slate-400 text-base mb-6 leading-relaxed select-none">
                Our enrichment framework acts as persistent, immutable proof. Dynamic records such as WHOIS data, passive DNS changes, and SSL configurations are captured and preserved forever with direct timestamps.
              </p>
              <ul className="space-y-3 mb-8 select-none">
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  WHOIS, ASN, Passive DNS, and SSL configurations
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Immutable, time-stamped evidence trails
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Automated background data collection
                </li>
              </ul>
            </div>
          </div>

          {/* Feature Block 3 */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center select-none">
            <div className="lg:col-span-6 animate-fade-in select-none">
              <div className="text-xs font-bold font-mono tracking-widest text-brand-400 uppercase mb-3 flex items-center gap-2 select-none">
                <span className="w-6 h-[1px] bg-brand-500 inline-block select-none" /> Feature 03
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mb-4 tracking-tight leading-snug select-none">
                Correlation Across Sources
              </h3>
              <p className="text-slate-400 text-base mb-6 leading-relaxed select-none">
                Discover linked infrastructure signals. If the same IP appears in multiple threat feeds and shares common attributes like an SSL certificate with a malicious domain, ThreatLens links them instantly.
              </p>
              <ul className="space-y-3 mb-8 select-none">
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Intelligent shared infrastructure discovery
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Advanced multi-feed overlap correlation
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Proactive multi-vector malicious campaign detection
                </li>
              </ul>
            </div>

            <div className="lg:col-span-6 select-none bg-surface-900 border border-slate-800 p-6 rounded-2xl shadow-xl hover:border-slate-700 hover:shadow-brand-500/5 transition-all duration-300 select-none">
              <div className="bg-surface-850 border border-slate-800/80 rounded-xl p-5 select-none">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800 select-none">
                  <div className="flex items-center gap-2 select-none">
                    <Activity className="w-4 h-4 text-brand-400" />
                    <span className="text-xs font-bold text-slate-300 tracking-wider">Source Correlation Graph</span>
                  </div>
                  <span className="text-[10px] font-mono bg-green-500/10 text-green-300 border border-green-500/20 px-2 py-0.5 rounded select-none">STABLE</span>
                </div>
                <div className="relative h-28 border border-dashed border-slate-800/80 rounded-xl flex items-center justify-around select-none">
                  {/* Visual nodes mapping correlation */}
                  <div className="flex flex-col items-center gap-1 select-none">
                    <div className="w-10 h-10 rounded-full bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-300 font-mono text-xs font-bold select-none animate-pulse-slow">IP</div>
                    <span className="text-[10px] text-slate-500 select-none">Indicator</span>
                  </div>
                  <div className="w-10 h-[1px] bg-gradient-to-r from-brand-500/60 via-blue-500/60 to-surface-800 select-none" />
                  <div className="flex flex-col items-center gap-1 select-none">
                    <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-300 font-mono text-xs font-bold select-none">SSL</div>
                    <span className="text-[10px] text-slate-500 select-none">Shared Cert</span>
                  </div>
                  <div className="w-10 h-[1px] bg-gradient-to-r from-blue-500/60 to-surface-800 select-none" />
                  <div className="flex flex-col items-center gap-1 select-none">
                    <div className="w-10 h-10 rounded-full bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-orange-300 font-mono text-xs font-bold select-none">DNS</div>
                    <span className="text-[10px] text-slate-500 select-none">Domain Map</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature Block 4 */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center select-none">
            {/* Visual first (alternating layout) */}
            <div className="lg:col-span-6 select-none bg-surface-900 border border-slate-800 p-6 rounded-2xl shadow-xl hover:border-slate-700 hover:shadow-brand-500/5 transition-all duration-300 order-last lg:order-first select-none">
              <div className="bg-surface-850 border border-slate-800/80 rounded-xl p-5 select-none">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800 select-none">
                  <div className="flex items-center gap-2 select-none">
                    <Eye className="w-4 h-4 text-brand-400" />
                    <span className="text-xs font-bold text-slate-300 tracking-wider">Analyst Decisions</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-brand-300 bg-brand-500/10 border border-brand-500/20 px-2 py-0.5 rounded select-none">PENDING</span>
                </div>
                <div className="flex flex-col gap-3 select-none">
                  <div className="flex items-center justify-between p-2.5 bg-green-500/5 border border-green-500/20 rounded-lg select-none">
                    <span className="text-xs text-green-300 font-semibold select-none">Accept & Promote</span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-green-500/10 border border-green-500/20 text-green-200 rounded select-none">Analyst Action</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 bg-red-500/5 border border-red-500/20 rounded-lg select-none">
                    <span className="text-xs text-red-300 font-semibold select-none">Demote & Revoke</span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-red-500/10 border border-red-500/20 text-red-200 rounded select-none">Analyst Action</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-6 animate-fade-in select-none">
              <div className="text-xs font-bold font-mono tracking-widest text-brand-400 uppercase mb-3 flex items-center gap-2 select-none">
                <span className="w-6 h-[1px] bg-brand-500 inline-block select-none" /> Feature 04
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mb-4 tracking-tight leading-snug select-none">
                Human Approval, Always
              </h3>
              <p className="text-slate-400 text-base mb-6 leading-relaxed select-none">
                Say no to black-box automated blocking. Our system operates as an advisory platform, delivering all the necessary telemetry and reasoning so your security analyst makes the final call.
              </p>
              <ul className="space-y-3 mb-8 select-none">
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Analysts can promote, demote, and annotate manually
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  All analyst actions recorded for defensible audit trails
                </li>
                <li className="flex items-center gap-3 text-sm text-slate-300 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 select-none" />
                  Configurable threshold parameters for automation
                </li>
              </ul>
            </div>
          </div>

        </div>
      </section>

      {/* ── SECTION 6: Trust / Differentiator Section ──────────────────────────── */}
      <section id="pricing" className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 z-10 border-t border-slate-900 select-none">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 select-none">
          <div className="text-xs font-bold tracking-widest text-brand-400 uppercase mb-3">Why ThreatLens?</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mb-5 leading-tight select-none">
            Stop guessing. Use validated evidence.
          </h2>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed select-none">
            See how the ThreatLens intelligence platform compares directly against legacy feed scrapers and raw aggregators.
          </p>
        </div>

        {/* Dynamic Comparison Table */}
        <div className="overflow-x-auto select-none bg-surface-900/60 border border-slate-800 rounded-2xl shadow-xl backdrop-blur-sm select-none">
          <table className="w-full text-left border-collapse select-none">
            <thead>
              <tr className="border-b border-slate-800 select-none">
                <th className="p-5 text-sm font-bold text-slate-300 uppercase tracking-wider select-none">Features</th>
                <th className="p-5 text-sm font-bold text-slate-400 uppercase tracking-wider select-none">Raw Feeds</th>
                <th className="p-5 text-sm font-bold text-slate-400 uppercase tracking-wider select-none">Feed Aggregator</th>
                <th className="p-5 text-sm font-bold text-brand-300 bg-brand-500/5 uppercase tracking-wider border-l border-brand-500/20 select-none">ThreatLens</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 select-none">
              <tr className="hover:bg-surface-850/50 transition-colors duration-150 select-none">
                <td className="p-5 text-sm font-bold text-slate-200 select-none">Context</td>
                <td className="p-5 text-sm text-slate-500 select-none">None</td>
                <td className="p-5 text-sm text-slate-400 select-none">Some Deduplication</td>
                <td className="p-5 text-sm text-brand-300 bg-brand-500/5 font-semibold border-l border-brand-500/20 flex items-center gap-1.5 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 select-none" /> Complete Enriched Evidence
                </td>
              </tr>
              <tr className="hover:bg-surface-850/50 transition-colors duration-150 select-none">
                <td className="p-5 text-sm font-bold text-slate-200 select-none">Confidence Scoring</td>
                <td className="p-5 text-sm text-slate-500 select-none">No scoring</td>
                <td className="p-5 text-sm text-slate-400 select-none">Static single scoring</td>
                <td className="p-5 text-sm text-brand-300 bg-brand-500/5 font-semibold border-l border-brand-500/20 flex items-center gap-1.5 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 select-none" /> Dynamic & Decay-Aware
                </td>
              </tr>
              <tr className="hover:bg-surface-850/50 transition-colors duration-150 select-none">
                <td className="p-5 text-sm font-bold text-slate-200 select-none">Explainability</td>
                <td className="p-5 text-sm text-slate-500 select-none">N/A</td>
                <td className="p-5 text-sm text-slate-500 select-none">Black Box Calculation</td>
                <td className="p-5 text-sm text-brand-300 bg-brand-500/5 font-semibold border-l border-brand-500/20 flex items-center gap-1.5 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 select-none" /> Continuous Audit Trail
                </td>
              </tr>
              <tr className="hover:bg-surface-850/50 transition-colors duration-150 select-none">
                <td className="p-5 text-sm font-bold text-slate-200 select-none">Correlation</td>
                <td className="p-5 text-sm text-slate-500 select-none">Manual lookups</td>
                <td className="p-5 text-sm text-slate-500 select-none">None</td>
                <td className="p-5 text-sm text-brand-300 bg-brand-500/5 font-semibold border-l border-brand-500/20 flex items-center gap-1.5 select-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 select-none" /> Multi-Source Auto-Correlation
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ── SECTION 7: Social Proof / Waitlist ────────────────────────────────── */}
      <section className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center z-10 border-t border-slate-900 select-none">
        <div className="bg-surface-900 border border-slate-800/80 rounded-3xl p-12 relative overflow-hidden select-none hover:border-slate-700/80 transition-all duration-300 group select-none">
          
          {/* Subtle Glow bg inside CTA box */}
          <div className="absolute -top-12 -left-12 w-48 h-48 bg-brand-600/10 blur-3xl pointer-events-none group-hover:bg-brand-500/20 transition-all duration-300 select-none" />

          <div className="text-xs font-bold tracking-widest text-brand-400 uppercase mb-4 select-none">Request early access</div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-100 mb-6 max-w-2xl mx-auto leading-tight select-none">
            Built for threat analysts, SOC hunters, and security engineers.
          </h2>
          <p className="text-slate-400 text-base sm:text-lg mb-10 max-w-xl mx-auto leading-relaxed select-none">
            Get high-fidelity intelligence context that explains its confidence. Start blocking threats confidently using clear, justifiable proof.
          </p>

          <button 
            onClick={() => navigate('/login')}
            className="mx-auto px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white text-base font-semibold rounded-lg shadow-glow hover:shadow-glow-sm hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2 select-none"
          >
            Claim Analyst Access
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* ── SECTION 8: Footer ─────────────────────────────────────────────────── */}
      <footer className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 z-10 border-t border-slate-900 flex flex-col md:flex-row items-center justify-between gap-6 select-none">
        
        {/* Logo and Copyright */}
        <div className="flex flex-col md:items-start items-center gap-2 select-none">
          <div className="flex items-center gap-2.5 select-none">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600/20 border border-brand-500/30 select-none">
              <Shield className="w-4 h-4 text-brand-400" />
            </div>
            <span className="text-sm font-bold tracking-wider text-slate-200 select-none">THREATLENS SECURITY</span>
          </div>
          <span className="text-xs text-slate-500 font-mono select-none">© {new Date().getFullYear()} THREATLENS SECURITY. ALL RIGHTS RESERVED.</span>
        </div>

        {/* Footer links */}
        <div className="flex items-center gap-6 text-xs font-semibold text-slate-500 tracking-wider select-none">
          <a href="#features" className="hover:text-slate-300 transition-colors select-none">Features</a>
          <a href="#how-it-works" className="hover:text-slate-300 transition-colors select-none">How It Works</a>
          <a href="#problem" className="hover:text-slate-300 transition-colors select-none">The Problem</a>
          <a href="#pricing" className="hover:text-slate-300 transition-colors select-none">Pricing</a>
        </div>
      </footer>

    </div>
  )
}
