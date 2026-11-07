import React from 'react'
import { Disc, Radio } from 'lucide-react'

export interface SampleTrackItem {
  id: string
  name: string
  genre: string
  url: string
  filename: string
  description: string
  cardBg: string
}

export const SAMPLE_TRACKS: SampleTrackItem[] = [
  {
    id: 'rock',
    name: 'Overdrive Riff & Beat',
    genre: 'Rock',
    url: '/samples/rock_sample.wav',
    filename: 'sample_rock.wav',
    description: 'Electric guitar harmonics, distortion clipping & driving snare transient',
    cardBg: 'bg-[#FFDF43]',
  },
  {
    id: 'classical',
    name: 'Polyphonic String Ensemble',
    genre: 'Classical',
    url: '/samples/classical_sample.wav',
    filename: 'sample_classical.wav',
    description: 'Sustained chord progression with vibrato and orchestral decay',
    cardBg: 'bg-[#F49ACB]',
  },
  {
    id: 'jazz',
    name: 'Walking Bass & Rhodes 7ths',
    genre: 'Jazz',
    url: '/samples/jazz_sample.wav',
    filename: 'sample_jazz.wav',
    description: 'Acoustic upright bassline, syncopated electric piano and ride tap',
    cardBg: 'bg-[#8CA4E8]',
  },
]

interface SampleTracksProps {
  onSelectSample: (sample: SampleTrackItem) => void
  disabled?: boolean
}

export const SampleTracks: React.FC<SampleTracksProps> = ({ onSelectSample, disabled = false }) => {
  return (
    <div className="bg-[#FFFDF7] border-2 border-[#4B2B23] shadow-brutal rounded-2xl p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <span className="w-8 h-8 rounded-lg bg-[#FFDF43] border-2 border-[#4B2B23] shadow-brutal-sm flex items-center justify-center text-[#4B2B23]">
            <Radio className="w-4 h-4" />
          </span>
          <div>
            <h3 className="text-lg font-display tracking-tight text-[#4B2B23]">
              WHAT ARE YOU JAMMING ON?
            </h3>
            <p className="text-xs text-[#7A5247] font-medium">
              Pick a synthesized demonstration track from the crate to test instant classification
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {SAMPLE_TRACKS.map((sample) => (
          <div
            key={sample.id}
            className={`flex flex-col justify-between p-4 rounded-xl border-2 border-[#4B2B23] shadow-brutal-sm transition-all hover:translate-y-[-2px] hover:shadow-brutal ${sample.cardBg}`}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-base font-bold text-[#4B2B23] leading-snug">
                  {sample.name}
                </span>
                <span className="text-xs font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-white text-[#4B2B23] border-2 border-[#4B2B23]">
                  {sample.genre}
                </span>
              </div>
              <p className="text-xs text-[#4B2B23]/80 leading-relaxed font-medium mb-4">
                {sample.description}
              </p>
            </div>

            <button
              onClick={() => onSelectSample(sample)}
              disabled={disabled}
              className="w-full py-2 px-3 rounded-lg bg-white hover:bg-[#4B2B23] text-[#4B2B23] hover:text-white border-2 border-[#4B2B23] shadow-brutal-sm text-xs font-bold tracking-wide flex items-center justify-center gap-2 transition-all active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50"
            >
              <Disc className="w-3.5 h-3.5" />
              <span>JAM WITH THIS</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
