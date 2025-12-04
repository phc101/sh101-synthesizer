"""
SH-101 Synthesizer with Computer Keyboard Support
Play with your QWERTY keyboard like a piano!

Keyboard Layout:
  A W S E D F T G Y H U J K  (White and black keys)
  Z = Octave Down
  X = Octave Up
  ESC = Quit
"""

import numpy as np
import sounddevice as sd
from scipy import signal
import pygame
import sys
import threading

# Audio configuration
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

class SH101Synth:
    """Roland SH-101 Synthesizer with real-time synthesis"""
    
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
        
        # Synth parameters
        self.waveform = 'sawtooth'
        self.cutoff = 2000
        self.resonance = 0.7
        self.attack = 0.01
        self.decay = 0.3
        self.sustain = 0.6
        self.release = 0.5
        self.volume = 0.25
        self.sub_osc_level = 0.3
        self.lfo_rate = 5
        self.lfo_depth = 0.3
        
    def generate_oscillator(self, frequency, length):
        """Generate oscillator waveform"""
        phase_increment = 2 * np.pi * frequency / self.sample_rate
        phases = self.phase + np.arange(length) * phase_increment
        
        if self.waveform == 'sawtooth':
            audio = signal.sawtooth(phases)
        elif self.waveform == 'square':
            audio = signal.square(phases)
        elif self.waveform == 'triangle':
            audio = signal.sawtooth(phases, width=0.5)
        else:  # sine
            audio = np.sin(phases)
        
        self.phase = phases[-1] % (2 * np.pi)
        return audio
    
    def apply_filter(self, audio, cutoff, resonance):
        """Apply resonant filter"""
        cutoff = np.clip(cutoff, 20, self.sample_rate / 2 - 100)
        f = 2 * np.sin(np.pi * cutoff / self.sample_rate)
        q = resonance
        
        output = np.zeros_like(audio)
        low = self.filter_state[0]
        band = self.filter_state[1]
        
        for i in range(len(audio)):
            low = low + f * band
            high = audio[i] - low - q * band
            band = f * high + band
            low = np.tanh(low)
            band = np.tanh(band)
            output[i] = low
        
        self.filter_state[0] = low
        self.filter_state[1] = band
        
        return output
    
    def apply_envelope(self, audio):
        """Apply ADSR envelope"""
        output = np.zeros_like(audio)
        
        for i in range(len(audio)):
            if self.is_playing:
                if self.env_stage == 'off' or self.env_stage == 'release':
                    self.env_stage = 'attack'
                    self.env_time = 0
                
                if self.env_stage == 'attack':
                    if self.attack > 0:
                        progress = self.env_time / (self.attack * self.sample_rate)
                        self.env_level = 1 - np.exp(-5 * progress)
                        if progress >= 1.0:
                            self.env_level = 1.0
                            self.env_stage = 'decay'
                            self.env_time = 0
                    else:
                        self.env_level = 1.0
                        self.env_stage = 'decay'
                
                elif self.env_stage == 'decay':
                    if self.decay > 0:
                        progress = self.env_time / (self.decay * self.sample_rate)
                        self.env_level = self.sustain + (1.0 - self.sustain) * np.exp(-5 * progress)
                        if progress >= 1.0:
                            self.env_level = self.sustain
                            self.env_stage = 'sustain'
                    else:
                        self.env_level = self.sustain
                        self.env_stage = 'sustain'
                
                elif self.env_stage == 'sustain':
                    self.env_level = self.sustain
            
            else:  # Release
                if self.env_stage != 'off':
                    if self.env_stage != 'release':
                        self.env_stage = 'release'
                        self.env_time = 0
                        self.release_start_level = self.env_level
                    
                    if self.release > 0:
                        progress = self.env_time / (self.release * self.sample_rate)
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
    
    def generate_lfo(self, length):
        """Generate LFO modulation"""
        phase_increment = 2 * np.pi * self.lfo_rate / self.sample_rate
        phases = self.lfo_phase + np.arange(length) * phase_increment
        lfo = np.sin(phases)
        self.lfo_phase = phases[-1] % (2 * np.pi)
        return lfo
    
    def synthesize(self, frequency, length):
        """Main synthesis function"""
        # Generate main oscillator
        audio = self.generate_oscillator(frequency, length)
        
        # Mix with sub oscillator
        if self.sub_osc_level > 0:
            self.phase_sub = getattr(self, 'phase_sub', 0)
            phase_increment = 2 * np.pi * (frequency / 2) / self.sample_rate
            phases = self.phase_sub + np.arange(length) * phase_increment
            sub = signal.square(phases)
            self.phase_sub = phases[-1] % (2 * np.pi)
            audio = audio * (1 - self.sub_osc_level) + sub * self.sub_osc_level
        
        # Apply LFO modulation to filter
        if self.lfo_rate > 0 and self.lfo_depth > 0:
            lfo = self.generate_lfo(length)
            modulated_cutoff = self.cutoff * (1 + lfo * self.lfo_depth)
        else:
            modulated_cutoff = self.cutoff
        
        # Apply filter with envelope modulation
        env_mod = self.env_level * 1.0  # Filter envelope amount
        final_cutoff = modulated_cutoff * (1 + env_mod)
        audio = self.apply_filter(audio, final_cutoff, self.resonance)
        
        # Apply amplitude envelope
        audio = self.apply_envelope(audio)
        
        # Soft clipping
        audio = np.tanh(audio * 1.5) * self.volume
        
        return audio

# Global synth instance
synth = SH101Synth(SAMPLE_RATE)
current_octave = 4

def audio_callback(outdata, frames, time_info, status):
    """Audio callback for real-time synthesis"""
    if status:
        print(status)
    
    if synth.is_playing and synth.current_note:
        audio = synth.synthesize(synth.current_note, frames)
        outdata[:, 0] = audio
    else:
        # Generate release tail
        if synth.env_level > 0:
            audio = synth.synthesize(synth.current_note or 440, frames)
            outdata[:, 0] = audio
        else:
            outdata.fill(0)

def note_to_freq(note):
    """Convert MIDI note number to frequency"""
    return 440 * (2 ** ((note - 69) / 12))

# Keyboard mapping (QWERTY keyboard to piano keys)
KEY_MAP = {
    pygame.K_a: 0,   # C
    pygame.K_w: 1,   # C#
    pygame.K_s: 2,   # D
    pygame.K_e: 3,   # D#
    pygame.K_d: 4,   # E
    pygame.K_f: 5,   # F
    pygame.K_t: 6,   # F#
    pygame.K_g: 7,   # G
    pygame.K_y: 8,   # G#
    pygame.K_h: 9,   # A
    pygame.K_u: 10,  # A#
    pygame.K_j: 11,  # B
    pygame.K_k: 12,  # C (next octave)
}

PRESET_KEYS = {
    pygame.K_1: 'bass',
    pygame.K_2: 'lead',
    pygame.K_3: 'acid',
    pygame.K_4: 'pad',
    pygame.K_5: 'brass',
}

PRESETS = {
    'bass': {
        'waveform': 'sawtooth',
        'cutoff': 800,
        'resonance': 1.2,
        'attack': 0.01,
        'decay': 0.4,
        'sustain': 0.3,
        'release': 0.2,
        'sub_osc_level': 0.5,
    },
    'lead': {
        'waveform': 'square',
        'cutoff': 3000,
        'resonance': 0.5,
        'attack': 0.05,
        'decay': 0.3,
        'sustain': 0.7,
        'release': 0.3,
        'sub_osc_level': 0.0,
    },
    'acid': {
        'waveform': 'square',
        'cutoff': 500,
        'resonance': 2.0,
        'attack': 0.01,
        'decay': 0.2,
        'sustain': 0.0,
        'release': 0.1,
        'sub_osc_level': 0.0,
    },
    'pad': {
        'waveform': 'sawtooth',
        'cutoff': 1500,
        'resonance': 0.3,
        'attack': 0.8,
        'decay': 0.5,
        'sustain': 0.8,
        'release': 1.5,
        'sub_osc_level': 0.3,
    },
    'brass': {
        'waveform': 'sawtooth',
        'cutoff': 2500,
        'resonance': 0.8,
        'attack': 0.1,
        'decay': 0.4,
        'sustain': 0.6,
        'release': 0.3,
        'sub_osc_level': 0.2,
    }
}

def load_preset(preset_name):
    """Load a preset"""
    if preset_name in PRESETS:
        p = PRESETS[preset_name]
        synth.waveform = p['waveform']
        synth.cutoff = p['cutoff']
        synth.resonance = p['resonance']
        synth.attack = p['attack']
        synth.decay = p['decay']
        synth.sustain = p['sustain']
        synth.release = p['release']
        synth.sub_osc_level = p['sub_osc_level']
        return True
    return False

def draw_ui(screen, font, small_font, active_keys, current_preset):
    """Draw the UI"""
    screen.fill((30, 30, 50))
    
    # Title
    title = font.render("🎹 SH-101 Synthesizer", True, (255, 255, 255))
    screen.blit(title, (20, 20))
    
    # Instructions
    y_offset = 80
    instructions = [
        "KEYBOARD CONTROLS:",
        "A W S E D F T G Y H U J K  = Piano keys (C to C)",
        "Z = Octave Down  |  X = Octave Up",
        "1-5 = Presets (Bass, Lead, Acid, Pad, Brass)",
        "ESC = Quit",
        "",
        f"Current Octave: {current_octave}",
        f"Current Preset: {current_preset}",
        "",
        "SYNTH PARAMETERS:",
        f"Waveform: {synth.waveform}",
        f"Cutoff: {synth.cutoff:.0f} Hz  |  Resonance: {synth.resonance:.2f}",
        f"Attack: {synth.attack:.2f}s  |  Decay: {synth.decay:.2f}s",
        f"Sustain: {synth.sustain:.2f}  |  Release: {synth.release:.2f}s",
        f"Sub Osc: {synth.sub_osc_level:.2f}  |  Volume: {synth.volume:.2f}",
    ]
    
    for i, text in enumerate(instructions):
        color = (100, 200, 255) if i == 0 or i == 9 else (200, 200, 200)
        rendered = small_font.render(text, True, color)
        screen.blit(rendered, (20, y_offset + i * 25))
    
    # Visual keyboard
    y_keyboard = 450
    key_width = 40
    key_height = 120
    black_key_height = 80
    
    white_keys = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K']
    black_keys = {'W': 1, 'E': 2, 'T': 4, 'Y': 5, 'U': 6}
    
    x_offset = 50
    
    # Draw white keys
    for i, key in enumerate(white_keys):
        x = x_offset + i * key_width
        color = (255, 100, 100) if key in active_keys else (255, 255, 255)
        pygame.draw.rect(screen, color, (x, y_keyboard, key_width - 2, key_height), border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), (x, y_keyboard, key_width - 2, key_height), 2, border_radius=5)
        
        key_text = small_font.render(key, True, (0, 0, 0))
        screen.blit(key_text, (x + 12, y_keyboard + key_height - 30))
    
    # Draw black keys
    for key, pos in black_keys.items():
        x = x_offset + pos * key_width - 15
        color = (255, 100, 100) if key in active_keys else (0, 0, 0)
        pygame.draw.rect(screen, color, (x, y_keyboard, 30, black_key_height), border_radius=5)
        
        key_text = small_font.render(key, True, (255, 255, 255))
        screen.blit(key_text, (x + 8, y_keyboard + black_key_height - 25))
    
    pygame.display.flip()

def main():
    """Main function"""
    global current_octave
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("SH-101 Synthesizer - Keyboard Control")
    
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    
    # Start audio stream
    stream = sd.OutputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    )
    stream.start()
    
    print("SH-101 Synthesizer Started!")
    print("Play with your keyboard: A W S E D F T G Y H U J K")
    print("Z/X = Change octave  |  1-5 = Load presets  |  ESC = Quit")
    
    clock = pygame.time.Clock()
    running = True
    active_keys = set()
    current_preset = "Custom"
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                # Quit
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                # Octave control
                elif event.key == pygame.K_z:
                    current_octave = max(2, current_octave - 1)
                    print(f"Octave: {current_octave}")
                
                elif event.key == pygame.K_x:
                    current_octave = min(6, current_octave + 1)
                    print(f"Octave: {current_octave}")
                
                # Preset loading
                elif event.key in PRESET_KEYS:
                    preset_name = PRESET_KEYS[event.key]
                    if load_preset(preset_name):
                        current_preset = preset_name.capitalize()
                        print(f"Loaded preset: {current_preset}")
                
                # Play note
                elif event.key in KEY_MAP:
                    note_offset = KEY_MAP[event.key]
                    midi_note = (current_octave * 12) + note_offset
                    freq = note_to_freq(midi_note)
                    synth.current_note = freq
                    synth.is_playing = True
                    
                    # Track active key for visual feedback
                    key_name = pygame.key.name(event.key).upper()
                    active_keys.add(key_name)
            
            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    synth.is_playing = False
                    key_name = pygame.key.name(event.key).upper()
                    active_keys.discard(key_name)
        
        # Draw UI
        draw_ui(screen, font, small_font, active_keys, current_preset)
        
        clock.tick(60)
    
    # Cleanup
    stream.stop()
    stream.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
