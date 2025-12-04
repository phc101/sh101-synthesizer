import streamlit as st
import numpy as np
import sounddevice as sd
from scipy import signal
import queue
import threading

# Audio configuration
SAMPLE_RATE = 44100
BLOCK_SIZE = 2048

class SH101Synth:
    """Roland SH-101 Synthesizer Clone - Enhanced Version"""
    
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
        self.noise_phase = 0
        
    def generate_oscillator(self, frequency, waveform, length, pwm=0.5, detune=0):
        """Generate oscillator waveform with detune"""
        t = np.arange(length) / self.sample_rate
        freq_mod = frequency * (1 + detune * 0.01)  # Detune in cents
        phase_increment = 2 * np.pi * freq_mod / self.sample_rate
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
            audio = signal.square(phases / 2)
        elif waveform == 'Noise':
            # White noise
            audio = np.random.uniform(-1, 1, length)
        else:
            audio = np.sin(phases)
        
        self.phase = phases[-1] % (2 * np.pi)
        return audio
    
    def apply_filter(self, audio, cutoff, resonance, filter_type='lowpass'):
        """Apply resonant filter using state-variable filter"""
        cutoff = np.clip(cutoff, 20, self.sample_rate / 2 - 100)
        
        # Normalize cutoff frequency
        f = 2 * np.sin(np.pi * cutoff / self.sample_rate)
        q = np.clip(resonance, 0, 4)
        
        output = np.zeros_like(audio)
        low = self.filter_state[0]
        band = self.filter_state[1]
        
        for i in range(len(audio)):
            low = low + f * band
            high = audio[i] - low - q * band
            band = f * high + band
            
            # Soft clipping for resonance
            low = np.tanh(low)
            band = np.tanh(band)
            
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
        """Apply ADSR envelope with exponential curves"""
        output = np.zeros_like(audio)
        
        for i in range(len(audio)):
            if gate_on:
                if self.env_stage == 'off' or self.env_stage == 'release':
                    self.env_stage = 'attack'
                    self.env_time = 0
                
                if self.env_stage == 'attack':
                    if attack > 0:
                        # Exponential attack
                        progress = self.env_time / (attack * self.sample_rate)
                        self.env_level = 1 - np.exp(-5 * progress)
                        if progress >= 1.0:
                            self.env_level = 1.0
                            self.env_stage = 'decay'
                            self.env_time = 0
                    else:
                        self.env_level = 1.0
                        self.env_stage = 'decay'
                
                elif self.env_stage == 'decay':
                    if decay > 0:
                        progress = self.env_time / (decay * self.sample_rate)
                        self.env_level = sustain + (1.0 - sustain) * np.exp(-5 * progress)
                        if progress >= 1.0:
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
                        self.release_start_level = self.env_level
                    
                    if release > 0:
                        progress = self.env_time / (release * self.sample_rate)
                        self.env_level = self.release_start_level * np.exp(-5 * progress)
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
        else:  # Sample & Hold
            # Generate new random values at LFO rate
            samples_per_step = int(self.sample_rate / max(rate, 0.1))
            lfo = np.repeat(np.random.uniform(-1, 1, len(phases) // samples_per_step + 1), samples_per_step)[:len(phases)]
        
        self.lfo_phase = phases[-1] % (2 * np.pi)
        return lfo
    
    def synthesize(self, frequency, length, params):
        """Main synthesis function"""
        # Generate main oscillator
        audio = self.generate_oscillator(
            frequency, 
            params['waveform'], 
            length,
            params['pwm'],
            params.get('detune', 0)
        )
        
        # Mix with sub oscillator if enabled
        if params['sub_osc_level'] > 0:
            sub = self.generate_oscillator(
                frequency / 2,
                'Sub Osc',
                length
            )
            audio = audio * (1 - params['sub_osc_level']) + sub * params['sub_osc_level']
        
        # Add noise if enabled
        if params.get('noise_level', 0) > 0:
            noise = self.generate_oscillator(0, 'Noise', length)
            audio = audio * (1 - params['noise_level']) + noise * params['noise_level']
        
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
        
        # Soft clipping for output
        audio = np.tanh(audio * 1.5) * params['volume']
        
        return audio

# Initialize session state
if 'synth' not in st.session_state:
    st.session_state.synth = SH101Synth(SAMPLE_RATE)
    st.session_state.stream = None
    st.session_state.current_playing = None

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
st.set_page_config(page_title="SH-101 Synthesizer", layout="wide", page_icon="🎹")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .synth-section {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎹 Roland SH-101 Synthesizer</h1><p>Classic Monophonic Analog Synth Emulation</p></div>', unsafe_allow_html=True)

# Preset selector
st.sidebar.header("Presets")
preset = st.sidebar.selectbox(
    "Load Preset",
    ["Custom", "Bass", "Lead", "Pad", "Acid", "Brass"]
)

# Preset configurations
presets = {
    "Bass": {
        "waveform": "Sawtooth",
        "cutoff": 800,
        "resonance": 1.2,
        "attack": 0.01,
        "decay": 0.4,
        "sustain": 0.3,
        "release": 0.2,
        "filter_env": 1.5,
        "sub_osc_level": 0.5,
    },
    "Lead": {
        "waveform": "Square",
        "cutoff": 3000,
        "resonance": 0.5,
        "attack": 0.05,
        "decay": 0.3,
        "sustain": 0.7,
        "release": 0.3,
        "filter_env": 0.8,
        "sub_osc_level": 0.0,
    },
    "Pad": {
        "waveform": "Sawtooth",
        "cutoff": 1500,
        "resonance": 0.3,
        "attack": 0.8,
        "decay": 0.5,
        "sustain": 0.8,
        "release": 1.5,
        "filter_env": 0.3,
        "sub_osc_level": 0.3,
    },
    "Acid": {
        "waveform": "Square",
        "cutoff": 500,
        "resonance": 2.0,
        "attack": 0.01,
        "decay": 0.2,
        "sustain": 0.0,
        "release": 0.1,
        "filter_env": 2.0,
        "sub_osc_level": 0.0,
    },
    "Brass": {
        "waveform": "Sawtooth",
        "cutoff": 2500,
        "resonance": 0.8,
        "attack": 0.1,
        "decay": 0.4,
        "sustain": 0.6,
        "release": 0.3,
        "filter_env": 1.0,
        "sub_osc_level": 0.2,
    }
}

# Load preset defaults
if preset != "Custom" and preset in presets:
    defaults = presets[preset]
else:
    defaults = {}

# Create control columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("🎵 Oscillator")
    waveform = st.selectbox(
        "Waveform",
        ['Sawtooth', 'Square', 'Pulse', 'Triangle', 'Sine'],
        index=['Sawtooth', 'Square', 'Pulse', 'Triangle', 'Sine'].index(defaults.get('waveform', 'Sawtooth'))
    )
    
    pwm = st.slider("Pulse Width", 0.1, 0.9, 0.5, 0.05)
    detune = st.slider("Detune (cents)", -50, 50, 0, 1)
    sub_osc_level = st.slider("Sub Oscillator", 0.0, 1.0, defaults.get('sub_osc_level', 0.3), 0.05)
    noise_level = st.slider("Noise", 0.0, 0.3, 0.0, 0.01)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("🎚️ Filter")
    cutoff = st.slider("Cutoff (Hz)", 100.0, 8000.0, float(defaults.get('cutoff', 2000)), 10.0)
    resonance = st.slider("Resonance", 0.0, 4.0, float(defaults.get('resonance', 0.7)), 0.1)
    filter_type = st.selectbox("Type", ['lowpass', 'bandpass', 'highpass'], index=0)
    filter_env = st.slider("Envelope Mod", 0.0, 3.0, float(defaults.get('filter_env', 0.5)), 0.1)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("📊 Envelope (ADSR)")
    attack = st.slider("Attack (s)", 0.001, 2.0, float(defaults.get('attack', 0.01)), 0.01)
    decay = st.slider("Decay (s)", 0.001, 2.0, float(defaults.get('decay', 0.3)), 0.01)
    sustain = st.slider("Sustain", 0.0, 1.0, float(defaults.get('sustain', 0.6)), 0.05)
    release = st.slider("Release (s)", 0.001, 3.0, float(defaults.get('release', 0.5)), 0.01)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("🔊 Output")
    volume = st.slider("Master Volume", 0.0, 0.5, 0.2, 0.01)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("〰️ LFO")
    lfo_rate = st.slider("Rate (Hz)", 0.0, 20.0, 5.0, 0.1)
    lfo_depth = st.slider("Depth", 0.0, 1.0, 0.3, 0.05)
    lfo_waveform = st.selectbox("Waveform", ['sine', 'triangle', 'square', 'random'], index=0)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="synth-section">', unsafe_allow_html=True)
    st.subheader("🎹 Settings")
    octave = st.slider("Octave", 2, 6, 4, 1)
    st.markdown('</div>', unsafe_allow_html=True)

# Store parameters
st.session_state.synth_params = {
    'waveform': waveform,
    'pwm': pwm,
    'detune': detune,
    'sub_osc_level': sub_osc_level,
    'noise_level': noise_level,
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
        st.error(f"⚠️ Could not start audio stream: {e}")
        st.info("Make sure your audio device is properly configured.")

# Virtual keyboard
st.markdown("---")
st.subheader("🎹 Virtual Keyboard")

# Create keyboard layout with proper black/white key arrangement
keys_layout = [
    ('C', False), ('C#', True), ('D', False), ('D#', True), 
    ('E', False), ('F', False), ('F#', True), ('G', False), 
    ('G#', True), ('A', False), ('A#', True), ('B', False)
]

note_cols = st.columns(12)

# Keyboard buttons
for i, (col, (key, is_black)) in enumerate(zip(note_cols, keys_layout)):
    with col:
        midi_note = (octave * 12) + i
        freq = note_to_freq(midi_note)
        
        button_label = f"{key}{octave}"
        button_key = f"note_{midi_note}"
        
        if st.button(button_label, key=button_key, use_container_width=True, type="secondary" if is_black else "primary"):
            st.session_state.synth.current_note = freq
            st.session_state.synth.is_playing = True
            st.session_state.current_playing = button_label

# Control buttons
st.markdown("---")
col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    if st.button("🎵 Test A4 (440Hz)", use_container_width=True):
        st.session_state.synth.current_note = 440
        st.session_state.synth.is_playing = True

with col_b:
    if st.button("🔇 Stop All", use_container_width=True):
        st.session_state.synth.is_playing = False
        st.session_state.current_playing = None

with col_c:
    if st.button("🔄 Reset Synth", use_container_width=True):
        st.session_state.synth = SH101Synth(SAMPLE_RATE)

# Status display
if st.session_state.current_playing:
    st.info(f"Currently playing: {st.session_state.current_playing}")

# Info section
st.markdown("---")
with st.expander("ℹ️ About the SH-101"):
    st.markdown("""
    ### Roland SH-101 Features
    
    The Roland SH-101 was a monophonic analog synthesizer released in 1982. This emulation includes:
    
    - **Oscillator**: Multiple waveforms (sawtooth, square, pulse, triangle, sine) with pulse width modulation
    - **Sub Oscillator**: Classic one-octave-below sub for massive bass
    - **Noise Generator**: White noise source for percussive sounds
    - **VCF**: Resonant 12dB/octave lowpass filter (also bandpass and highpass modes)
    - **ADSR Envelope**: Full envelope control for both VCA and VCF
    - **LFO**: Low-frequency oscillator with multiple waveforms for modulation
    - **Monophonic**: True monophonic behavior, one note at a time
    
    ### Tips for Great Sounds
    
    - **Bass**: Use sawtooth with high sub oscillator, low cutoff, high resonance
    - **Lead**: Square wave with moderate cutoff and filter envelope modulation
    - **Acid**: Square wave, low cutoff, high resonance, short decay, zero sustain
    - **Pad**: Sawtooth, slow attack/release, moderate cutoff
    - **Brass**: Sawtooth, medium attack, filter envelope modulation
    
    *Try the presets in the sidebar to get started!*
    """)

with st.expander("⌨️ Computer Keyboard Control (Coming Soon)"):
    st.markdown("""
    Future updates will include:
    - Computer keyboard to MIDI mapping
    - Arpeggiator
    - Sequencer
    - More preset banks
    - MIDI input support
    """)
