import streamlit as st
import numpy as np
import sounddevice as sd
from scipy import signal
import queue
import threading
import time

# Audio configuration
SAMPLE_RATE = 44100
BLOCK_SIZE = 2048

class SH101Synth:
    """Roland SH-101 Synthesizer Clone"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.is_playing = False
        self.current_note = None
        self.phase = 0
        self.filter_state = np.zeros(2)
        self.env_stage = 'off'
        self.env_level = 0
        self.env_time = 0
        self.lfo_phase = 0
        
    def generate_oscillator(self, frequency, waveform, length, pwm=0.5):
        """Generate oscillator waveform"""
        t = np.arange(length) / self.sample_rate
        phase_increment = 2 * np.pi * frequency / self.sample_rate
        phases = self.phase + np.arange(length) * phase_increment
        
        if waveform == 'Sawtooth':
            audio = signal.sawtooth(phases)
        elif waveform == 'Square':
            audio = signal.square(phases, duty=pwm)
        elif waveform == 'Pulse':
            audio = signal.square(phases, duty=0.25)
        elif waveform == 'Triangle':
            audio = signal.sawtooth(phases, width=0.5)
        elif waveform == 'Sub Osc':
            # Sub oscillator one octave down
            audio = signal.square(phases / 2)
        else:
            audio = np.sin(phases)
        
        self.phase = phases[-1] % (2 * np.pi)
        return audio
    
    def apply_filter(self, audio, cutoff, resonance, filter_type='lowpass'):
        """Apply resonant filter (simplified state-variable filter)"""
        cutoff = np.clip(cutoff, 20, self.sample_rate / 2 - 100)
        
        # Normalize cutoff frequency
        f = 2 * np.sin(np.pi * cutoff / self.sample_rate)
        q = resonance
        
        output = np.zeros_like(audio)
        low = self.filter_state[0]
        band = self.filter_state[1]
        
        for i in range(len(audio)):
            low = low + f * band
            high = audio[i] - low - q * band
            band = f * high + band
            
            if filter_type == 'lowpass':
                output[i] = low
            elif filter_type == 'bandpass':
                output[i] = band
            elif filter_type == 'highpass':
                output[i] = high
        
        self.filter_state[0] = low
        self.filter_state[1] = band
        
        return output
    
    def apply_envelope(self, audio, attack, decay, sustain, release, gate_on):
        """Apply ADSR envelope"""
        output = np.zeros_like(audio)
        
        for i in range(len(audio)):
            if gate_on:
                if self.env_stage == 'off' or self.env_stage == 'release':
                    self.env_stage = 'attack'
                    self.env_time = 0
                
                if self.env_stage == 'attack':
                    if attack > 0:
                        self.env_level = self.env_time / (attack * self.sample_rate)
                        if self.env_level >= 1.0:
                            self.env_level = 1.0
                            self.env_stage = 'decay'
                            self.env_time = 0
                    else:
                        self.env_level = 1.0
                        self.env_stage = 'decay'
                
                elif self.env_stage == 'decay':
                    if decay > 0:
                        self.env_level = 1.0 - (1.0 - sustain) * (self.env_time / (decay * self.sample_rate))
                        if self.env_level <= sustain:
                            self.env_level = sustain
                            self.env_stage = 'sustain'
                    else:
                        self.env_level = sustain
                        self.env_stage = 'sustain'
                
                elif self.env_stage == 'sustain':
                    self.env_level = sustain
            
            else:  # Gate off - release
                if self.env_stage != 'off':
                    if self.env_stage != 'release':
                        self.env_stage = 'release'
                        self.env_time = 0
                    
                    if release > 0:
                        decay_amount = self.env_level * (self.env_time / (release * self.sample_rate))
                        self.env_level = max(0, self.env_level - decay_amount / 10)
                        if self.env_level <= 0.001:
                            self.env_level = 0
                            self.env_stage = 'off'
                    else:
                        self.env_level = 0
                        self.env_stage = 'off'
            
            output[i] = audio[i] * self.env_level
            self.env_time += 1
        
        return output
    
    def generate_lfo(self, rate, length, waveform='sine'):
        """Generate LFO modulation"""
        phase_increment = 2 * np.pi * rate / self.sample_rate
        phases = self.lfo_phase + np.arange(length) * phase_increment
        
        if waveform == 'sine':
            lfo = np.sin(phases)
        elif waveform == 'triangle':
            lfo = signal.sawtooth(phases, width=0.5)
        elif waveform == 'square':
            lfo = signal.square(phases)
        else:
            lfo = np.random.uniform(-1, 1, length)  # Sample & Hold
        
        self.lfo_phase = phases[-1] % (2 * np.pi)
        return lfo
    
    def synthesize(self, frequency, length, params):
        """Main synthesis function"""
        # Generate oscillator
        audio = self.generate_oscillator(
            frequency, 
            params['waveform'], 
            length,
            params['pwm']
        )
        
        # Mix with sub oscillator if enabled
        if params['sub_osc_level'] > 0:
            sub = self.generate_oscillator(
                frequency / 2,
                'Sub Osc',
                length
            )
            audio = audio * (1 - params['sub_osc_level']) + sub * params['sub_osc_level']
        
        # Apply LFO modulation to filter cutoff
        if params['lfo_rate'] > 0 and params['lfo_depth'] > 0:
            lfo = self.generate_lfo(params['lfo_rate'], length, params['lfo_waveform'])
            modulated_cutoff = params['cutoff'] * (1 + lfo * params['lfo_depth'])
        else:
            modulated_cutoff = params['cutoff']
        
        # Apply filter with envelope modulation
        env_mod = self.env_level * params['filter_env']
        final_cutoff = modulated_cutoff * (1 + env_mod)
        audio = self.apply_filter(audio, final_cutoff, params['resonance'], params['filter_type'])
        
        # Apply amplitude envelope
        audio = self.apply_envelope(
            audio,
            params['attack'],
            params['decay'],
            params['sustain'],
            params['release'],
            self.is_playing
        )
        
        return audio * params['volume']

# Global synth instance
if 'synth' not in st.session_state:
    st.session_state.synth = SH101Synth(SAMPLE_RATE)
    st.session_state.audio_queue = queue.Queue()
    st.session_state.stream = None

def audio_callback(outdata, frames, time_info, status):
    """Audio callback for real-time synthesis"""
    if status:
        print(status)
    
    synth = st.session_state.synth
    params = st.session_state.get('synth_params', {})
    
    if synth.is_playing and synth.current_note:
        audio = synth.synthesize(synth.current_note, frames, params)
        outdata[:, 0] = audio
    else:
        # Generate release tail if needed
        if synth.env_level > 0:
            audio = synth.synthesize(synth.current_note or 440, frames, params)
            outdata[:, 0] = audio
        else:
            outdata.fill(0)

def note_to_freq(note):
    """Convert MIDI note number to frequency"""
    return 440 * (2 ** ((note - 69) / 12))

# Streamlit UI
st.set_page_config(page_title="SH-101 Synthesizer", layout="wide")

st.title("🎹 Roland SH-101 Synthesizer Clone")
st.markdown("*Classic monophonic analog synth emulation*")

# Create three columns for controls
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎵 Oscillator")
    waveform = st.selectbox(
        "Waveform",
        ['Sawtooth', 'Square', 'Pulse', 'Triangle', 'Sine'],
        index=0
    )
    
    pwm = st.slider("Pulse Width", 0.1, 0.9, 0.5, 0.05)
    
    sub_osc_level = st.slider("Sub Oscillator", 0.0, 1.0, 0.3, 0.05)
    
    st.subheader("🎚️ Filter")
    cutoff = st.slider("Cutoff", 100.0, 8000.0, 2000.0, 10.0)
    resonance = st.slider("Resonance", 0.0, 2.0, 0.7, 0.1)
    filter_type = st.selectbox("Filter Type", ['lowpass', 'bandpass', 'highpass'], index=0)
    filter_env = st.slider("Envelope Amount", 0.0, 2.0, 0.5, 0.1)

with col2:
    st.subheader("📊 Envelope (ADSR)")
    attack = st.slider("Attack", 0.001, 2.0, 0.01, 0.01)
    decay = st.slider("Decay", 0.001, 2.0, 0.3, 0.01)
    sustain = st.slider("Sustain", 0.0, 1.0, 0.6, 0.05)
    release = st.slider("Release", 0.001, 3.0, 0.5, 0.01)
    
    st.subheader("🔊 Output")
    volume = st.slider("Master Volume", 0.0, 0.5, 0.2, 0.01)

with col3:
    st.subheader("〰️ LFO")
    lfo_rate = st.slider("LFO Rate (Hz)", 0.0, 20.0, 5.0, 0.1)
    lfo_depth = st.slider("LFO Depth", 0.0, 1.0, 0.3, 0.05)
    lfo_waveform = st.selectbox("LFO Waveform", ['sine', 'triangle', 'square', 'random'], index=0)
    
    st.subheader("🎹 Keyboard")
    octave = st.slider("Octave", 2, 6, 4, 1)
    
# Store parameters
st.session_state.synth_params = {
    'waveform': waveform,
    'pwm': pwm,
    'sub_osc_level': sub_osc_level,
    'cutoff': cutoff,
    'resonance': resonance,
    'filter_type': filter_type,
    'filter_env': filter_env,
    'attack': attack,
    'decay': decay,
    'sustain': sustain,
    'release': release,
    'volume': volume,
    'lfo_rate': lfo_rate,
    'lfo_depth': lfo_depth,
    'lfo_waveform': lfo_waveform,
}

# Virtual keyboard
st.markdown("---")
st.subheader("Virtual Keyboard")

# Create keyboard layout
keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
note_cols = st.columns(12)

# Start audio stream if not already running
if st.session_state.stream is None:
    try:
        st.session_state.stream = sd.OutputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=audio_callback
        )
        st.session_state.stream.start()
    except Exception as e:
        st.error(f"Could not start audio stream: {e}")

# Keyboard buttons
for i, (col, key) in enumerate(zip(note_cols, keys)):
    with col:
        midi_note = (octave * 12) + i
        is_black = '#' in key
        
        button_type = "secondary" if is_black else "primary"
        
        if st.button(f"{key}{octave}", key=f"note_{midi_note}", use_container_width=True):
            freq = note_to_freq(midi_note)
            st.session_state.synth.current_note = freq
            st.session_state.synth.is_playing = True
            
            # Auto-release after a short time (simulating key release)
            time.sleep(0.1)

# Control buttons
st.markdown("---")
col_a, col_b, col_c = st.columns([1, 1, 3])

with col_a:
    if st.button("🎵 Test Note (A4)", use_container_width=True):
        st.session_state.synth.current_note = 440
        st.session_state.synth.is_playing = True
        time.sleep(0.5)
        st.session_state.synth.is_playing = False

with col_b:
    if st.button("🔇 Stop", use_container_width=True):
        st.session_state.synth.is_playing = False

# Info section
st.markdown("---")
st.markdown("""
### SH-101 Features
- **Oscillator**: Classic analog waveforms with pulse width control
- **Sub Oscillator**: One octave below main oscillator
- **Filter**: Resonant state-variable filter with envelope modulation
- **Envelope**: Full ADSR control for both VCA and VCF
- **LFO**: Modulation source for filter and pitch
- **Monophonic**: Single note playback, true to the original

*Click keyboard keys or use the test note button to play. Adjust controls in real-time!*
""")

# Cleanup on app termination
if st.session_state.stream is not None:
    # Note: Streamlit doesn't have a built-in cleanup hook
    # In production, you'd want to handle this more elegantly
    pass
