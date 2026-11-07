import math
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw
import os

def create_pwa_icon(size, filename, is_maskable=False):
    img = Image.new("RGBA", (size, size), (8, 11, 18, 255))
    draw = ImageDraw.Draw(img)
    
    center = size / 2
    # Radius scaling
    safe_margin = size * 0.8 if is_maskable else size * 0.9
    
    # Outer ambient glow ring
    for r in range(int(safe_margin * 0.42), int(safe_margin * 0.48), 2):
        alpha = int(40 * (1 - (r - safe_margin * 0.42) / (safe_margin * 0.06)))
        draw.ellipse([center - r, center - r, center + r, center + r], outline=(67, 136, 255, alpha), width=2)
    
    # Concentric audio rings
    radii = [safe_margin * 0.38, safe_margin * 0.30, safe_margin * 0.22, safe_margin * 0.14]
    colors = [
        (87, 216, 255, 230), # #57D8FF
        (67, 136, 255, 240), # #4388FF
        (155, 123, 255, 240), # #9B7BFF
        (87, 216, 255, 255)  # Cyan core
    ]
    
    for r, col in zip(radii, colors):
        draw.ellipse([center - r, center - r, center + r, center + r], outline=col, width=max(2, int(size * 0.015)))
    
    # Radial harmonic rays
    num_rays = 16
    for i in range(num_rays):
        angle = (2 * math.pi / num_rays) * i
        r_inner = safe_margin * 0.16
        ray_len = (safe_margin * 0.18) if (i % 2 == 0) else (safe_margin * 0.10)
        r_outer = r_inner + ray_len
        
        x1 = center + math.cos(angle) * r_inner
        y1 = center + math.sin(angle) * r_inner
        x2 = center + math.cos(angle) * r_outer
        y2 = center + math.sin(angle) * r_outer
        
        draw.line([(x1, y1), (x2, y2)], fill=(87, 216, 255, 200), width=max(2, int(size * 0.012)))
        
    # Center core pulse
    core_r = safe_margin * 0.08
    draw.ellipse([center - core_r, center - core_r, center + core_r, center + core_r], fill=(87, 216, 255, 255))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename, "PNG")
    print(f"Created {filename} ({size}x{size})")

def generate_sample_audio(filename, genre_type, duration=10.0, sr=22050):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = np.zeros_like(t)
    
    if genre_type == "rock":
        # Distorted guitar riff + kick/snare rhythm
        # Power chord: E2 (82.4 Hz), B2 (123.5 Hz), E3 (164.8 Hz)
        riff_notes = [82.41, 98.0, 110.0, 123.47]
        bar_len = sr * 0.5
        for i in range(int(duration * 2)):
            note_freq = riff_notes[i % len(riff_notes)]
            t_slice = t[int(i * bar_len):int((i + 1) * bar_len)]
            t_local = np.linspace(0, 0.5, len(t_slice), endpoint=False)
            
            # Harmonic sawtooth + soft clipping for distortion
            sig = (np.sin(2 * np.pi * note_freq * t_local) + 
                   0.6 * np.sin(2 * np.pi * note_freq * 2 * t_local) +
                   0.4 * np.sin(2 * np.pi * note_freq * 3 * t_local) +
                   0.2 * np.sin(2 * np.pi * note_freq * 4 * t_local))
            # Distortion
            sig = np.tanh(2.5 * sig) * np.exp(-1.5 * t_local)
            
            # Beat pulse (kick on 0, snare noise on 1)
            if i % 2 == 0:
                kick = np.sin(2 * np.pi * 55 * np.exp(-10 * t_local) * t_local) * np.exp(-8 * t_local)
                sig += kick * 0.7
            else:
                snare_noise = (np.random.rand(len(t_local)) * 2 - 1) * np.exp(-12 * t_local)
                sig += snare_noise * 0.5
                
            y[int(i * bar_len):int((i + 1) * bar_len)] += sig
            
    elif genre_type == "classical":
        # Polyphonic string ensemble: Strings triad (C maj, A min, F maj, G maj)
        chords = [
            [261.63, 329.63, 392.00, 523.25], # C maj
            [220.00, 261.63, 329.63, 440.00], # A min
            [174.61, 261.63, 349.23, 440.00], # F maj
            [196.00, 246.94, 293.66, 392.00]  # G maj
        ]
        chord_len = sr * 2.5
        for idx, chord in enumerate(chords):
            start = int(idx * chord_len)
            end = min(len(y), int((idx + 1) * chord_len))
            t_local = np.linspace(0, 2.5, end - start, endpoint=False)
            # Gentle string vibrato & envelope
            env = np.sin(np.pi * (t_local / 2.5)) ** 0.5
            vibrato = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t_local)
            
            sig = np.zeros_like(t_local)
            for f in chord:
                sig += 0.25 * np.sin(2 * np.pi * f * vibrato * t_local)
                sig += 0.12 * np.sin(2 * np.pi * f * 2 * vibrato * t_local)
                sig += 0.06 * np.sin(2 * np.pi * f * 3 * vibrato * t_local)
            y[start:end] += sig * env
            
    elif genre_type == "jazz":
        # Swing tempo walking bass + Rhodes 7th chord stabs
        bass_notes = [130.81, 146.83, 164.81, 174.61, 196.0, 174.61, 164.81, 146.83] # C-D-E-F-G-F-E-D
        step_len = sr * 0.6
        for step in range(int(duration / 0.6)):
            start = int(step * step_len)
            end = min(len(y), int((step + 1) * step_len))
            t_local = np.linspace(0, 0.6, end - start, endpoint=False)
            
            # Walking upright bass note
            f_bass = bass_notes[step % len(bass_notes)]
            bass = np.sin(2 * np.pi * f_bass * t_local) * np.exp(-4 * t_local)
            bass += 0.3 * np.sin(2 * np.pi * (f_bass * 2) * t_local) * np.exp(-6 * t_local)
            
            # Rhodes chord on offbeats
            chord_sig = np.zeros_like(t_local)
            if step % 2 == 1:
                # Dm7 / G7 chords
                rhodes_freqs = [293.66, 349.23, 440.0, 523.25]
                for rf in rhodes_freqs:
                    chord_sig += 0.15 * np.sin(2 * np.pi * rf * t_local) * np.exp(-5 * t_local)
            
            # Ride cymbal swing tick
            ride = (np.random.rand(len(t_local)) * 2 - 1) * np.exp(-25 * t_local) * 0.15
            
            y[start:end] += (bass * 0.6 + chord_sig * 0.5 + ride)
            
    # Normalize peak to 0.85
    peak = np.max(np.abs(y))
    if peak > 0:
        y = (y / peak) * 0.85
        
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    sf.write(filename, y.astype(np.float32), sr)
    print(f"Generated sample audio: {filename} ({duration}s, {sr}Hz)")

if __name__ == "__main__":
    # Icons
    create_pwa_icon(192, "frontend/public/pwa-192x192.png")
    create_pwa_icon(512, "frontend/public/pwa-512x512.png")
    create_pwa_icon(512, "frontend/public/maskable-icon-512x512.png", is_maskable=True)
    create_pwa_icon(64, "frontend/public/favicon.png")
    
    # Audio samples
    generate_sample_audio("frontend/public/samples/rock_sample.wav", "rock", 12.0)
    generate_sample_audio("frontend/public/samples/classical_sample.wav", "classical", 12.0)
    generate_sample_audio("frontend/public/samples/jazz_sample.wav", "jazz", 12.0)
