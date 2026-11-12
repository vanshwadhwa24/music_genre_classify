import React, { useEffect, useState } from 'react'
import {
  Database,
  Cpu,
  Sliders,
  AlertTriangle,
  Music2,
} from 'lucide-react'

import { apiService } from '../services/api'
import type { ModelArchitectureInfo } from '../types/api'
import { MarqueeBanner } from '../components/MarqueeBanner'
import { NeonLogo } from '../components/NeonLogo'

export const AboutPage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelArchitectureInfo | null>(null)

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const info = await apiService.getModelInfo()
        setModelInfo(info)
      } catch (err) {
        console.warn('Could not fetch model info:', err)
      }
    }
    fetchInfo()
  }, [])

  const genres = [
    { name: 'Blues', desc: 'Dominant 7th progressions, shuffle rhythms, acoustic and electric slide guitars.', color: 'bg-[#FFB347]' },
    { name: 'Classical', desc: 'Complex polyphony, wide dynamic range, acoustic orchestral and chamber instrumentation.', color: 'bg-[#FF3CAC]' },
    { name: 'Country', desc: 'String band acoustic timbres, twangy guitar, pedal steel, narrative vocal structures.', color: 'bg-[#3DFFD0]' },
    { name: 'Disco', desc: 'Four-on-the-floor kick pattern, syncopated electric basslines, rhythm guitar chops.', color: 'bg-[#FFB347]' },
    { name: 'Hip-Hop', desc: 'Heavy sub-bass, 808/acoustic drum breaks, syncopated vocal cadence, sampled hooks.', color: 'bg-[#FF3CAC]' },
    { name: 'Jazz', desc: 'Extended 7th/9th/11th chord harmonies, swing syncopation, improvisational phrasing.', color: 'bg-[#3DFFD0]' },
    { name: 'Metal', desc: 'High-gain harmonic distortion, palm-muted power riffs, rapid double-kick percussion.', color: 'bg-[#FFB347]' },
    { name: 'Pop', desc: 'Catchy melodic hooks, polished vocal-centric mix, structured verse-chorus arrangements.', color: 'bg-[#FF3CAC]' },
    { name: 'Reggae', desc: 'Accented offbeat skank guitar/keys, prominent dub bassline, rim-click percussion.', color: 'bg-[#3DFFD0]' },
    { name: 'Rock', desc: 'Overdriven guitar riffs, 4/4 driving drum beat, verse-chorus dynamic energy.', color: 'bg-[#FFB347]' },
  ]

  return (
    <div className="w-full">
      {/* Editorial Header Section */}
      <section className="bg-gradient-to-b from-[#14032A] to-[#4A0E4E] border-b-2 border-[#FF3CAC] pt-10 pb-8 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#FFE9FF] bg-[#2A0A4A] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm inline-block">
              RESEARCH & METHODOLOGY
            </span>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display tracking-tight text-[#FFE9FF] leading-none uppercase">
              HOW NEON RADIO HEARS SOUND
            </h1>
            <p className="text-sm sm:text-base font-bold text-[#FFE9FF] max-w-xl leading-relaxed">
              From raw audio waveforms to 128 Mel-frequency spectrogram bins, powering a 4-stage convolutional neural network.
            </p>
          </div>

          <div className="shrink-0">
            <NeonLogo size={150} variant="headphones" className="hover:rotate-6 transition-transform" />
          </div>
        </div>
      </section>

      <MarqueeBanner
        text="★ GTZAN 1,000 AUDIO TRACKS ★ 22,050 HZ SPECTRAL ANALYSIS ★ 4-STAGE 2D-CNN ★ 422,506 PARAMETERS ★"
        bg="bg-[#14032A]"
      />

      <div className="max-w-5xl mx-auto px-4 py-10 sm:py-14 space-y-12">
        {/* 1. Dataset Overview */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 pb-3 border-b-2 border-[#FF3CAC]">
            <Database className="w-6 h-6 text-[#FFE9FF]" />
            <h2 className="text-3xl font-display uppercase tracking-tight text-[#FFE9FF]">
              THE GTZAN MUSIC GENRE BENCHMARK
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-5 rounded-2xl bg-[#FFB347] border-2 border-[#FF3CAC] shadow-brutal">
              <span className="text-xs font-mono font-bold text-[#FFE9FF]/70 uppercase block mb-1">
                Audio Tracks
              </span>
              <span className="text-4xl font-display text-[#FFE9FF]">1,000 TRACKS</span>
              <span className="text-xs font-medium text-[#FFE9FF] block mt-1">100 excerpts per musical genre</span>
            </div>
            <div className="p-5 rounded-2xl bg-[#FF3CAC] border-2 border-[#FF3CAC] shadow-brutal">
              <span className="text-xs font-mono font-bold text-[#FFE9FF]/70 uppercase block mb-1">
                Clip Length
              </span>
              <span className="text-4xl font-display text-[#FFE9FF]">30.0 SECONDS</span>
              <span className="text-xs font-medium text-[#FFE9FF] block mt-1">Single continuous excerpt</span>
            </div>
            <div className="p-5 rounded-2xl bg-[#3DFFD0] border-2 border-[#FF3CAC] shadow-brutal">
              <span className="text-xs font-mono font-bold text-[#FFE9FF]/70 uppercase block mb-1">
                Sampling Rate
              </span>
              <span className="text-4xl font-display text-[#FFE9FF]">22,050 HZ</span>
              <span className="text-xs font-medium text-[#FFE9FF] block mt-1">16-bit uncompressed mono PCM</span>
            </div>
          </div>

          <p className="text-sm font-medium text-[#FFE9FF] leading-relaxed">
            Compiled by George Tzanetakis and Perry Cook in 2001, GTZAN remains the benchmark standard in Music Information Retrieval (MIR) research. It spans 10 distinct styles:
          </p>

          {/* 10 Genres Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {genres.map((g) => (
              <div
                key={g.name}
                className={`p-4 rounded-xl border-2 border-[#FF3CAC] shadow-brutal-sm ${g.color}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Music2 className="w-4 h-4 text-[#FFE9FF]" />
                  <span className="text-base font-bold text-[#FFE9FF] tracking-tight">{g.name}</span>
                </div>
                <p className="text-xs font-medium text-[#FFE9FF]/90 leading-relaxed">{g.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 2. Audio Processing Pipeline */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 pb-3 border-b-2 border-[#FF3CAC]">
            <Sliders className="w-6 h-6 text-[#FFE9FF]" />
            <h2 className="text-3xl font-display uppercase tracking-tight text-[#FFE9FF]">
              ACOUSTIC PREPROCESSING PIPELINE
            </h2>
          </div>

          <div className="bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal rounded-2xl p-6 space-y-4">
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3.5 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex items-start gap-3">
                <span className="w-7 h-7 rounded-lg bg-[#FFB347] border border-[#FF3CAC] font-bold text-sm text-[#1A0536] flex items-center justify-center shrink-0">
                  1
                </span>
                <div>
                  <strong className="text-sm text-[#FFE9FF] block">Resampling & Downmixing</strong>
                  <span className="text-[#C9A8E0] font-sans text-xs font-medium leading-relaxed block mt-0.5">
                    Audio inputs are converted to 22,050 Hz and downmixed to a single monophonic channel.
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex items-start gap-3">
                <span className="w-7 h-7 rounded-lg bg-[#FF3CAC] border border-[#FF3CAC] font-bold text-sm text-[#1A0536] flex items-center justify-center shrink-0">
                  2
                </span>
                <div>
                  <strong className="text-sm text-[#FFE9FF] block">Short-Time Fourier Transform (STFT)</strong>
                  <span className="text-[#C9A8E0] font-sans text-xs font-medium leading-relaxed block mt-0.5">
                    FFT window size of <strong>2,048 samples</strong> (~93ms) with hop size of <strong>512 samples</strong> (~23ms), generating 75% frame overlap.
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex items-start gap-3">
                <span className="w-7 h-7 rounded-lg bg-[#3DFFD0] border border-[#FF3CAC] font-bold text-sm text-[#1A0536] flex items-center justify-center shrink-0">
                  3
                </span>
                <div>
                  <strong className="text-sm text-[#FFE9FF] block">Triangular Mel Filterbanks</strong>
                  <span className="text-[#C9A8E0] font-sans text-xs font-medium leading-relaxed block mt-0.5">
                    Linear frequency bins are warped into <strong>128 triangular Mel filters</strong> from 20 Hz to 11,025 Hz, simulating human pitch sensation.
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex items-start gap-3">
                <span className="w-7 h-7 rounded-lg bg-[#FFB347] border border-[#FF3CAC] font-bold text-sm text-[#1A0536] flex items-center justify-center shrink-0">
                  4
                </span>
                <div>
                  <strong className="text-sm text-[#FFE9FF] block">Decibel Scaling & Normalization</strong>
                  <span className="text-[#C9A8E0] font-sans text-xs font-medium leading-relaxed block mt-0.5">
                    Powers are converted to decibels (dB) via <code>librosa.power_to_db</code>, followed by z-score standardization <code>(S - μ) / σ</code>.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 3. Deep CNN Architecture */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 pb-3 border-b-2 border-[#FF3CAC]">
            <Cpu className="w-6 h-6 text-[#FFE9FF]" />
            <h2 className="text-3xl font-display uppercase tracking-tight text-[#FFE9FF]">
              DEEP 2D-CNN ARCHITECTURE
            </h2>
          </div>

          <div className="bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal rounded-2xl p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-4 rounded-xl bg-[#FFB347] border-2 border-[#FF3CAC]">
                <span className="text-[#FFE9FF]/70 font-bold block mb-1">Input Spectrogram Shape</span>
                <strong className="text-lg font-bold text-[#FFE9FF]">(Batch, 1, 128, T)</strong>
              </div>
              <div className="p-4 rounded-xl bg-[#FF3CAC] border-2 border-[#FF3CAC]">
                <span className="text-[#FFE9FF]/70 font-bold block mb-1">Trainable Parameters</span>
                <strong className="text-lg font-bold text-[#FFE9FF]">
                  {modelInfo?.parameters_total ? modelInfo.parameters_total.toLocaleString() : '422,506'}
                </strong>
              </div>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="p-3 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                <span className="font-bold text-[#1A0536] bg-[#FFB347] px-2 py-0.5 rounded border border-[#FF3CAC] inline-block w-fit">
                  Block 1
                </span>
                <span className="text-[#FFE9FF]">Conv2d(1→32, k=3) · BatchNorm · ELU · MaxPool(2x2) · Dropout(0.15)</span>
              </div>
              <div className="p-3 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                <span className="font-bold text-[#1A0536] bg-[#FFB347] px-2 py-0.5 rounded border border-[#FF3CAC] inline-block w-fit">
                  Block 2
                </span>
                <span className="text-[#FFE9FF]">Conv2d(32→64, k=3) · BatchNorm · ELU · MaxPool(2x2) · Dropout(0.20)</span>
              </div>
              <div className="p-3 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                <span className="font-bold text-[#1A0536] bg-[#FF3CAC] px-2 py-0.5 rounded border border-[#FF3CAC] inline-block w-fit">
                  Block 3
                </span>
                <span className="text-[#FFE9FF]">Conv2d(64→128, k=3) · BatchNorm · ELU · MaxPool(2x2) · Dropout(0.25)</span>
              </div>
              <div className="p-3 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                <span className="font-bold text-[#1A0536] bg-[#3DFFD0] px-2 py-0.5 rounded border border-[#FF3CAC] inline-block w-fit">
                  Block 4
                </span>
                <span className="text-[#FFE9FF]">Conv2d(128→256, k=3) · BatchNorm · ELU · AdaptiveAvgPool2d((1, 1))</span>
              </div>
              <div className="p-3 rounded-xl bg-[#2A0A4A] border-2 border-[#FF3CAC] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                <span className="font-bold text-[#FFE9FF] bg-[#1A0536] px-2 py-0.5 rounded border border-[#FF3CAC] inline-block w-fit">
                  Classifier
                </span>
                <span className="text-[#FFE9FF]">Linear(256→128) · ReLU · Dropout(0.4) · Linear(128→10) · Softmax</span>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Limitations & Caveats */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 pb-3 border-b-2 border-[#FF3CAC]">
            <AlertTriangle className="w-6 h-6 text-[#FFE9FF]" />
            <h2 className="text-3xl font-display uppercase tracking-tight text-[#FFE9FF]">
              ACOUSTIC CAVEATS & LIMITATIONS
            </h2>
          </div>

          <div className="p-6 rounded-2xl bg-[#FFB347] border-2 border-[#FF3CAC] shadow-brutal space-y-3 text-xs text-[#1A0536] font-medium leading-relaxed">
            <p>
              <strong>1. GTZAN Historical Label Noise:</strong> Several musicology studies have noted occasional mislabeled tracks, artist repetitions across folds, and low-fidelity compression artifacts in the original 2001 GTZAN corpus.
            </p>
            <p>
              <strong>2. Window Duration Sensitivity:</strong> The network is optimized for 30-second studio excerpts. Live microphone listening uses rolling 2.5-second windows; shorter segments lack long-term rhythmic and structural progression.
            </p>
            <p>
              <strong>3. Acoustic Hardware coloration:</strong> Studio recordings feature balanced master tracks, whereas microphone feeds introduce room reverberation, ambient background noise, and microphone frequency coloration.
            </p>
            <p>
              <strong>4. Uncalibrated Activations:</strong> Softmax scores represent relative model activation strength across the 10 GTZAN categories, rather than calibrated posterior probabilities.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
