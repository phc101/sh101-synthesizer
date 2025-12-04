# 🎹 Roland SH-101 Synthesizer Clone

A faithful emulation of the classic Roland SH-101 monophonic analog synthesizer built with Streamlit and Python.

## Features

### Oscillator Section
- **Multiple Waveforms**: Sawtooth, Square, Pulse, Triangle, Sine
- **Pulse Width Modulation**: Adjustable duty cycle for square/pulse waves
- **Detune**: Fine-tuning control in cents
- **Sub Oscillator**: One octave below the main oscillator
- **Noise Generator**: White noise for percussive sounds

### Filter Section
- **Resonant Filter**: State-variable filter with multiple types
- **Filter Types**: Lowpass, Bandpass, Highpass
- **Resonance Control**: Self-oscillating at high settings
- **Envelope Modulation**: ADSR envelope amount for filter cutoff

### Envelope Generator
- **ADSR Envelope**: Full Attack, Decay, Sustain, Release controls
- **Exponential Curves**: Natural-sounding envelope shapes
- **Dual Application**: Controls both VCA (amplitude) and VCF (filter)

### LFO (Low-Frequency Oscillator)
- **Multiple Waveforms**: Sine, Triangle, Square, Sample & Hold
- **Rate Control**: 0-20 Hz modulation rate
- **Depth Control**: Amount of modulation applied to filter cutoff

### Virtual Keyboard
- **12-Note Keyboard**: One octave layout
- **Octave Selection**: 2-6 octave range
- **Visual Feedback**: Black and white key distinction

### Presets
- **Bass**: Deep, powerful bass sounds
- **Lead**: Cutting lead tones
- **Pad**: Smooth, atmospheric sounds
- **Acid**: Classic acid bassline sound
- **Brass**: Brassy, resonant tones

## Installation

### Prerequisites
- Python 3.8 or higher
- Audio output device (speakers/headphones)

### Quick Start

1. **Clone or download the files**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install streamlit numpy scipy sounddevice
```

3. **Run the synthesizer**:

Basic version:
```bash
streamlit run sh101_synth.py
```

Enhanced version (recommended):
```bash
streamlit run sh101_synth_enhanced.py
```

Using the run script:
```bash
chmod +x run_synth.sh
./run_synth.sh
```

## Usage

### Basic Controls

1. **Select a Preset**: Choose from the sidebar preset menu to load pre-configured sounds
2. **Adjust Parameters**: 
   - Oscillator: Select waveform and adjust pulse width
   - Filter: Set cutoff frequency and resonance
   - Envelope: Control attack, decay, sustain, release times
   - LFO: Add modulation with rate and depth controls
3. **Play Notes**: Click the virtual keyboard buttons to play notes
4. **Test Sound**: Use the "Test A4" button to hear a reference tone

### Sound Design Tips

#### Creating a Fat Bass
1. Set waveform to **Sawtooth**
2. Increase **Sub Oscillator** to 0.5-0.7
3. Set **Cutoff** to 500-800 Hz
4. Increase **Resonance** to 1.0-1.5
5. Set **Filter Envelope** to 1.5-2.0
6. Use short **Attack** (0.01s) and **Decay** (0.3-0.5s)
7. Lower **Sustain** to 0.2-0.4

#### Creating an Acid Lead
1. Set waveform to **Square**
2. **Cutoff**: 300-600 Hz
3. **Resonance**: 2.0-3.0 (high!)
4. **Filter Envelope**: 2.0-3.0
5. **Attack**: 0.01s
6. **Decay**: 0.1-0.2s
7. **Sustain**: 0.0
8. **Release**: 0.1s
9. Add LFO modulation for movement

#### Creating a Synth Pad
1. Set waveform to **Sawtooth**
2. **Cutoff**: 1500-2500 Hz
3. **Resonance**: 0.3-0.5
4. **Attack**: 0.5-1.0s
5. **Release**: 1.0-2.0s
6. **Sustain**: 0.7-0.9
7. Add slow **LFO** (2-4 Hz) with low depth

#### Creating a Lead Sound
1. Set waveform to **Square** or **Pulse**
2. **Cutoff**: 2500-4000 Hz
3. **Resonance**: 0.5-1.0
4. **Filter Envelope**: 0.5-1.0
5. **Attack**: 0.05-0.1s
6. **Decay**: 0.2-0.4s
7. **Sustain**: 0.6-0.8
8. Add slight **LFO** modulation for vibrato

## Technical Details

### Audio Engine
- **Sample Rate**: 44,100 Hz
- **Block Size**: 2048 samples
- **Bit Depth**: 32-bit float
- **Latency**: ~46ms (depends on system)

### Synthesis Method
- **Oscillators**: Band-limited waveform generation
- **Filter**: State-variable filter implementation
- **Envelopes**: Exponential curves for natural sound
- **Real-time**: Streaming audio synthesis

### Architecture
```
Oscillator → Sub Osc Mix → Noise Mix → 
LFO Modulation → Filter (with Env Mod) → 
Amplitude Envelope → Output
```

## Files

- `sh101_synth.py` - Basic version with core functionality
- `sh101_synth_enhanced.py` - Enhanced version with presets and improved UI
- `requirements.txt` - Python dependencies
- `run_synth.sh` - Convenience script to run the synthesizer
- `README.md` - This file

## Troubleshooting

### No Sound
1. Check your system audio output is working
2. Verify audio permissions for Python/terminal
3. Try adjusting the **Master Volume** slider
4. Check that your audio device is not muted
5. Try running with: `python -m sounddevice` to test audio

### High CPU Usage
1. The real-time synthesis is CPU-intensive
2. Close other applications
3. Reduce the browser tab count
4. The audio callback runs continuously

### Crackling/Popping
1. Increase the block size in the code (BLOCK_SIZE = 4096)
2. Close other audio applications
3. Check CPU usage
4. Update audio drivers

### Import Errors
```bash
# Make sure all dependencies are installed
pip install --upgrade streamlit numpy scipy sounddevice
```

## Limitations

- **Monophonic**: Only one note at a time (true to the original)
- **No MIDI**: Currently no MIDI input support (planned)
- **No Recording**: No built-in audio recording (use system audio recorder)
- **Browser-based**: Runs in web browser via Streamlit

## Future Enhancements

- [ ] Computer keyboard to MIDI mapping
- [ ] MIDI input support
- [ ] Built-in arpeggiator
- [ ] Step sequencer
- [ ] Preset save/load
- [ ] Audio recording/export
- [ ] More filter types (Moog-style, etc.)
- [ ] Portamento/glide
- [ ] Effects (delay, chorus, distortion)

## Contributing

Feel free to fork and improve! Some areas for contribution:
- Better filter algorithms
- More accurate oscillator modeling
- Performance optimizations
- UI/UX improvements
- Additional presets

## Acknowledgments

Based on the legendary Roland SH-101 synthesizer (1982-1986), a monophonic analog synthesizer that became a staple in electronic music, particularly in acid house and techno.

## License

This is an educational project. Roland and SH-101 are trademarks of Roland Corporation.

## Technical Notes

### State-Variable Filter
The filter uses a digital state-variable filter implementation that provides simultaneous lowpass, bandpass, and highpass outputs. The resonance parameter adds feedback to create the classic resonant "peak" that can self-oscillate at high settings.

### Envelope Implementation
The ADSR envelope uses exponential curves rather than linear ramps, which sounds more natural and analog-like. The release stage maintains the envelope level at note-off to prevent clicks.

### Phase Continuity
The oscillator maintains phase continuity between buffer blocks to prevent discontinuities and clicks in the audio output.

---

**Enjoy making music with your SH-101 clone!** 🎵
