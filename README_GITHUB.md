# 🎹 SH-101 Synthesizer

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

A faithful emulation of the legendary **Roland SH-101** monophonic analog synthesizer, implemented in Python with multiple interfaces: web-based (Streamlit), browser-based (React), and desktop with computer keyboard control (Pygame).

## ✨ Features

### Synthesis Engine
- 🎵 **Multiple Waveforms**: Sawtooth, Square, Pulse, Triangle, Sine
- 🎚️ **Resonant Filter**: State-variable filter with lowpass, bandpass, and highpass modes
- 📊 **ADSR Envelope**: Full Attack, Decay, Sustain, Release controls
- 〰️ **LFO Modulation**: Sine, Triangle, Square, and Sample & Hold waveforms
- 🔊 **Sub Oscillator**: One octave below main oscillator for massive bass
- 🎛️ **Real-time Synthesis**: Low-latency audio generation at 44.1kHz

### User Interfaces
1. **Streamlit Web Interface** - Adjustable parameters with visual controls
2. **React Browser Version** - Works directly in browser, optimized for mobile
3. **Pygame Keyboard Version** - Play with your computer keyboard like a piano!

### Built-in Presets
- 🎸 **Bass** - Deep, powerful bass sounds
- 🎺 **Lead** - Cutting synth leads
- 🧪 **Acid** - Classic TB-303 style acid bassline
- 🌊 **Pad** - Smooth atmospheric sounds
- 🎺 **Brass** - Brassy, punchy tones

## 🚀 Quick Start

### Option 1: Streamlit Web Version (Recommended for Beginners)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the enhanced version
streamlit run sh101_synth_enhanced.py
```

Then open your browser to `http://localhost:8501`

### Option 2: React Browser Version (Mobile-Friendly)

The React version (`.jsx` file) runs directly in the browser as a Claude Artifact. Perfect for mobile devices!

### Option 3: Desktop with Keyboard Control

```bash
# Install dependencies
pip install -r requirements_keyboard.txt

# Run the keyboard version
python sh101_keyboard.py
```

**Keyboard Controls:**
```
Piano Keys:  A W S E D F T G Y H U J K
             │ │ │ │ │ │ │ │ │ │ │ │ │
             C C# D D# E F F# G G# A A# B C

Z = Octave Down    X = Octave Up
1-5 = Load Presets (Bass, Lead, Acid, Pad, Brass)
ESC = Quit
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Audio output device (speakers/headphones)
- (Optional) Git for version control

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sh101-synthesizer.git
cd sh101-synthesizer

# Install Streamlit version dependencies
pip install -r requirements.txt

# Or install keyboard version dependencies
pip install -r requirements_keyboard.txt
```

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎛️ Synth Parameters

| Parameter | Description | Range |
|-----------|-------------|-------|
| **Oscillator** | Waveform selection | Sawtooth, Square, Pulse, Triangle, Sine |
| **Sub Oscillator** | One octave below main | 0.0 - 1.0 |
| **Cutoff** | Filter cutoff frequency | 100 - 8000 Hz |
| **Resonance** | Filter resonance/Q | 0.0 - 4.0 |
| **Attack** | Envelope attack time | 0.001 - 2.0 s |
| **Decay** | Envelope decay time | 0.001 - 2.0 s |
| **Sustain** | Envelope sustain level | 0.0 - 1.0 |
| **Release** | Envelope release time | 0.001 - 3.0 s |
| **LFO Rate** | Modulation speed | 0 - 20 Hz |
| **LFO Depth** | Modulation amount | 0.0 - 1.0 |

## 🎨 Sound Design Tips

### Creating Classic Sounds

**Fat Bass:**
1. Waveform: Sawtooth
2. Sub Oscillator: 0.6-0.8
3. Cutoff: 500-800 Hz
4. Resonance: 1.0-1.5
5. Short Attack (0.01s), Medium Decay (0.4s)
6. Low Sustain (0.3)

**Acid Bassline:**
1. Waveform: Square
2. Cutoff: 300-600 Hz
3. Resonance: 2.0-3.0 (high!)
4. Attack: 0.01s
5. Decay: 0.1-0.2s
6. Sustain: 0.0
7. Short Release (0.1s)

**Synth Pad:**
1. Waveform: Sawtooth
2. Cutoff: 1500-2500 Hz
3. Long Attack (0.8s) and Release (1.5s)
4. High Sustain (0.8)
5. Slow LFO (2-4 Hz) with low depth

**Lead Sound:**
1. Waveform: Square or Pulse
2. Cutoff: 2500-4000 Hz
3. Medium Attack (0.05-0.1s)
4. Add slight LFO for vibrato

## 🏗️ Project Structure

```
sh101-synthesizer/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
├── GITHUB_GUIDE.md             # How to publish to GitHub
├── requirements.txt             # Streamlit dependencies
├── requirements_keyboard.txt    # Pygame dependencies
├── sh101_synth.py              # Basic Streamlit version
├── sh101_synth_enhanced.py     # Enhanced Streamlit version
├── sh101_keyboard.py           # Pygame keyboard version
├── sh101-synth-online.jsx      # React browser version
└── run_synth.sh                # Quick start script
```

## 🔧 Technical Details

### Audio Engine
- **Sample Rate**: 44,100 Hz
- **Block Size**: 1024-2048 samples
- **Bit Depth**: 32-bit float
- **Synthesis**: Real-time subtractive synthesis
- **Filter**: State-variable filter with resonance feedback

### Architecture
```
Oscillator → Sub Oscillator Mix → 
LFO Modulation → Resonant Filter (with Envelope Mod) → 
Amplitude Envelope → Output
```

## 🐛 Troubleshooting

### No Sound Output
1. Check system audio is working
2. Verify audio device isn't muted
3. Try adjusting Master Volume slider
4. On mobile: tap the "Enable Audio" button first

### High CPU Usage
- Real-time synthesis is CPU-intensive
- Close other applications
- Try increasing block size in code

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Pygame Version Won't Run
```bash
pip install pygame numpy scipy sounddevice
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Ideas for Contributions
- Additional waveforms or filter types
- Preset save/load functionality
- MIDI input support
- Recording/export to WAV
- Arpeggiator
- Step sequencer
- More accurate analog modeling
- Performance optimizations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the legendary **Roland SH-101** synthesizer (1982-1986)
- Inspired by the analog synthesis techniques of the 1980s
- Built with modern Python audio libraries

## 📚 Resources

- [Web Audio API Documentation](https://developer.mozilla.org/en-US/Web_Audio_API)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Digital Signal Processing Tutorial](https://jackschaedler.github.io/circles-sines-signals/)
- [Sound On Sound: Synth Secrets](https://www.soundonsound.com/series/synth-secrets)

## 🎵 Made With

- [Python](https://www.python.org/) - Core language
- [NumPy](https://numpy.org/) - Numerical computing
- [SciPy](https://scipy.org/) - Signal processing
- [Streamlit](https://streamlit.io/) - Web interface
- [Pygame](https://www.pygame.org/) - Keyboard control
- [React](https://react.dev/) - Browser interface
- [SoundDevice](https://python-sounddevice.readthedocs.io/) - Audio I/O

## 📧 Contact

Have questions or feedback? Open an issue or reach out!

---

**Note**: Roland and SH-101 are trademarks of Roland Corporation. This is an educational project and not affiliated with or endorsed by Roland Corporation.

⭐ If you like this project, please give it a star on GitHub!
