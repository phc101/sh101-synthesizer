import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Volume2, VolumeX, Settings, Play, Square } from 'lucide-react';

const SH101Synth = () => {
  const [audioContext, setAudioContext] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentNote, setCurrentNote] = useState(null);
  const [activeKey, setActiveKey] = useState(null);
  const [audioReady, setAudioReady] = useState(false);
  
  // Synth parameters
  const [waveform, setWaveform] = useState('sawtooth');
  const [cutoff, setCutoff] = useState(2000);
  const [resonance, setResonance] = useState(5);
  const [attack, setAttack] = useState(0.01);
  const [decay, setDecay] = useState(0.3);
  const [sustain, setSustain] = useState(0.6);
  const [release, setRelease] = useState(0.5);
  const [volume, setVolume] = useState(0.3);
  const [subOsc, setSubOsc] = useState(0.3);
  const [lfoRate, setLfoRate] = useState(5);
  const [lfoDepth, setLfoDepth] = useState(0.3);
  const [octave, setOctave] = useState(4);
  const [preset, setPreset] = useState('custom');
  
  // Audio nodes refs
  const oscillatorRef = useRef(null);
  const subOscRef = useRef(null);
  const gainNodeRef = useRef(null);
  const filterNodeRef = useRef(null);
  const lfoRef = useRef(null);
  const lfoGainRef = useRef(null);
  
  // Initialize audio on user interaction
  const initAudio = useCallback(() => {
    if (!audioContext) {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      setAudioContext(ctx);
      setAudioReady(true);
      
      // Play silent sound to unlock audio on iOS
      const silentGain = ctx.createGain();
      silentGain.gain.value = 0;
      silentGain.connect(ctx.destination);
      
      const silentOsc = ctx.createOscillator();
      silentOsc.connect(silentGain);
      silentOsc.start(ctx.currentTime);
      silentOsc.stop(ctx.currentTime + 0.1);
    } else if (audioContext.state === 'suspended') {
      audioContext.resume().then(() => {
        setAudioReady(true);
      });
    } else {
      setAudioReady(true);
    }
  }, [audioContext]);
  
  // Initialize Audio Context - don't auto-create, wait for user interaction
  useEffect(() => {
    return () => {
      if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
      }
    };
  }, [audioContext]);
  
  // Presets
  const presets = {
    bass: {
      waveform: 'sawtooth',
      cutoff: 800,
      resonance: 12,
      attack: 0.01,
      decay: 0.4,
      sustain: 0.3,
      release: 0.2,
      subOsc: 0.5,
      lfoRate: 0,
      lfoDepth: 0
    },
    lead: {
      waveform: 'square',
      cutoff: 3000,
      resonance: 5,
      attack: 0.05,
      decay: 0.3,
      sustain: 0.7,
      release: 0.3,
      subOsc: 0,
      lfoRate: 6,
      lfoDepth: 0.2
    },
    acid: {
      waveform: 'square',
      cutoff: 500,
      resonance: 20,
      attack: 0.01,
      decay: 0.2,
      sustain: 0,
      release: 0.1,
      subOsc: 0,
      lfoRate: 0,
      lfoDepth: 0
    },
    pad: {
      waveform: 'sawtooth',
      cutoff: 1500,
      resonance: 3,
      attack: 0.8,
      decay: 0.5,
      sustain: 0.8,
      release: 1.5,
      subOsc: 0.3,
      lfoRate: 3,
      lfoDepth: 0.15
    },
    brass: {
      waveform: 'sawtooth',
      cutoff: 2500,
      resonance: 8,
      attack: 0.1,
      decay: 0.4,
      sustain: 0.6,
      release: 0.3,
      subOsc: 0.2,
      lfoRate: 4,
      lfoDepth: 0.1
    }
  };
  
  const loadPreset = (presetName) => {
    if (presets[presetName]) {
      const p = presets[presetName];
      setWaveform(p.waveform);
      setCutoff(p.cutoff);
      setResonance(p.resonance);
      setAttack(p.attack);
      setDecay(p.decay);
      setSustain(p.sustain);
      setRelease(p.release);
      setSubOsc(p.subOsc);
      setLfoRate(p.lfoRate);
      setLfoDepth(p.lfoDepth);
      setPreset(presetName);
    }
  };
  
  const noteToFreq = (note) => {
    return 440 * Math.pow(2, (note - 69) / 12);
  };
  
  const playNote = useCallback((frequency) => {
    if (!audioContext || !audioReady) {
      initAudio();
      // Retry after initialization
      setTimeout(() => {
        if (audioContext) playNote(frequency);
      }, 100);
      return;
    }
    
    // Resume context if suspended
    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }
    
    // Stop existing note
    stopNote();
    
    const now = audioContext.currentTime;
    
    // Create oscillator
    const osc = audioContext.createOscillator();
    osc.type = waveform;
    osc.frequency.setValueAtTime(frequency, now);
    
    // Create sub oscillator
    const subOsc = audioContext.createOscillator();
    subOsc.type = 'square';
    subOsc.frequency.setValueAtTime(frequency / 2, now);
    
    // Create filter
    const filter = audioContext.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(cutoff, now);
    filter.Q.setValueAtTime(resonance, now);
    
    // Create LFO
    const lfo = audioContext.createOscillator();
    lfo.frequency.setValueAtTime(lfoRate, now);
    const lfoGain = audioContext.createGain();
    lfoGain.gain.setValueAtTime(cutoff * lfoDepth, now);
    
    // Create gain nodes
    const mainGain = audioContext.createGain();
    const subGain = audioContext.createGain();
    const masterGain = audioContext.createGain();
    
    mainGain.gain.setValueAtTime(1 - subOsc, now);
    subGain.gain.setValueAtTime(subOsc, now);
    
    // Connect LFO
    if (lfoRate > 0 && lfoDepth > 0) {
      lfo.connect(lfoGain);
      lfoGain.connect(filter.frequency);
      lfo.start(now);
      lfoRef.current = lfo;
      lfoGainRef.current = lfoGain;
    }
    
    // Connect main oscillator
    osc.connect(mainGain);
    mainGain.connect(filter);
    
    // Connect sub oscillator
    subOsc.connect(subGain);
    subGain.connect(filter);
    
    // Connect filter to master gain
    filter.connect(masterGain);
    masterGain.connect(audioContext.destination);
    
    // Apply envelope
    masterGain.gain.setValueAtTime(0, now);
    masterGain.gain.linearRampToValueAtTime(volume, now + attack);
    masterGain.gain.linearRampToValueAtTime(volume * sustain, now + attack + decay);
    
    // Apply filter envelope
    const filterEnvAmount = cutoff * 2;
    filter.frequency.setValueAtTime(cutoff, now);
    filter.frequency.linearRampToValueAtTime(cutoff + filterEnvAmount, now + attack);
    filter.frequency.linearRampToValueAtTime(cutoff + filterEnvAmount * sustain, now + attack + decay);
    
    // Start oscillators
    osc.start(now);
    subOsc.start(now);
    
    // Store references
    oscillatorRef.current = osc;
    subOscRef.current = subOsc;
    gainNodeRef.current = masterGain;
    filterNodeRef.current = filter;
    
    setIsPlaying(true);
  }, [audioContext, audioReady, initAudio, waveform, cutoff, resonance, attack, decay, sustain, volume, subOsc, lfoRate, lfoDepth]);
  
  const stopNote = useCallback(() => {
    if (!audioContext || !oscillatorRef.current) return;
    
    const now = audioContext.currentTime;
    
    // Apply release
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.cancelScheduledValues(now);
      gainNodeRef.current.gain.setValueAtTime(gainNodeRef.current.gain.value, now);
      gainNodeRef.current.gain.linearRampToValueAtTime(0, now + release);
    }
    
    if (filterNodeRef.current) {
      filterNodeRef.current.frequency.cancelScheduledValues(now);
      filterNodeRef.current.frequency.setValueAtTime(filterNodeRef.current.frequency.value, now);
      filterNodeRef.current.frequency.linearRampToValueAtTime(100, now + release);
    }
    
    // Stop oscillators after release
    setTimeout(() => {
      if (oscillatorRef.current) {
        oscillatorRef.current.stop();
        oscillatorRef.current = null;
      }
      if (subOscRef.current) {
        subOscRef.current.stop();
        subOscRef.current = null;
      }
      if (lfoRef.current) {
        lfoRef.current.stop();
        lfoRef.current = null;
      }
    }, release * 1000);
    
    setIsPlaying(false);
    setActiveKey(null);
  }, [audioContext, release]);
  
  const handleKeyPress = (note, keyName) => {
    const frequency = noteToFreq((octave * 12) + note);
    setCurrentNote(frequency);
    setActiveKey(keyName);
    playNote(frequency);
  };
  
  const handleKeyRelease = () => {
    stopNote();
  };
  
  // Keyboard layout
  const keys = [
    { note: 0, name: 'C', black: false },
    { note: 1, name: 'C#', black: true },
    { note: 2, name: 'D', black: false },
    { note: 3, name: 'D#', black: true },
    { note: 4, name: 'E', black: false },
    { note: 5, name: 'F', black: false },
    { note: 6, name: 'F#', black: true },
    { note: 7, name: 'G', black: false },
    { note: 8, name: 'G#', black: true },
    { note: 9, name: 'A', black: false },
    { note: 10, name: 'A#', black: true },
    { note: 11, name: 'B', black: false },
  ];
  
  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 p-2 md:p-4 overflow-auto">
      <div className="max-w-7xl mx-auto">
        {/* Audio Enable Button */}
        {!audioReady && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl p-8 max-w-md text-center">
              <div className="text-6xl mb-4">🎹</div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Ready to Play?
              </h2>
              <p className="text-gray-300 mb-6">
                Tap the button below to enable audio and start making music!
              </p>
              <button
                onClick={initAudio}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white text-xl font-bold px-12 py-6 rounded-xl shadow-lg transform transition-all hover:scale-105 active:scale-95"
              >
                🔊 Enable Audio & Start
              </button>
            </div>
          </div>
        )}
        
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-2xl p-4 md:p-6 mb-4 md:mb-6">
          <h1 className="text-2xl md:text-4xl font-bold text-white text-center mb-2">
            🎹 SH-101 Synthesizer
          </h1>
          <p className="text-white text-center text-sm md:text-base opacity-90">
            Classic Monophonic Analog Synth
          </p>
          {audioReady && (
            <div className="text-center mt-2">
              <span className="inline-block bg-green-500 text-white text-xs px-3 py-1 rounded-full">
                ✓ Audio Ready
              </span>
            </div>
          )}
        </div>
        
        {/* Presets */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-3 md:p-4 mb-4 md:mb-6">
          <div className="flex items-center gap-2 md:gap-4 flex-wrap justify-center">
            <span className="text-white font-semibold text-sm md:text-base w-full md:w-auto text-center md:text-left mb-2 md:mb-0">Presets:</span>
            {Object.keys(presets).map((p) => (
              <button
                key={p}
                onClick={() => loadPreset(p)}
                className={`px-3 md:px-4 py-2 md:py-2 rounded-lg font-medium transition-all text-sm md:text-base ${
                  preset === p
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
            <button
              onClick={() => setPreset('custom')}
              className={`px-3 md:px-4 py-2 md:py-2 rounded-lg font-medium transition-all text-sm md:text-base ${
                preset === 'custom'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Custom
            </button>
          </div>
        </div>
        
        {/* Controls */}
        <div className="grid grid-cols-1 gap-4 md:gap-6 mb-4 md:mb-6">
          {/* Oscillator & Filter - Combined for mobile */}
          <div className="bg-gray-800 rounded-lg shadow-xl p-4 md:p-6">
            <h2 className="text-lg md:text-xl font-bold text-white mb-3 flex items-center gap-2">
              <Square className="w-4 h-4 md:w-5 md:h-5" />
              Oscillator & Filter
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <label className="text-white text-xs md:text-sm mb-1 block font-medium">Waveform</label>
                  <select
                    value={waveform}
                    onChange={(e) => setWaveform(e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 text-sm md:text-base"
                  >
                    <option value="sawtooth">Sawtooth</option>
                    <option value="square">Square</option>
                    <option value="triangle">Triangle</option>
                    <option value="sine">Sine</option>
                  </select>
                </div>
                
                <div>
                  <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                    Sub Osc: {subOsc.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={subOsc}
                    onChange={(e) => setSubOsc(parseFloat(e.target.value))}
                    className="w-full h-8"
                  />
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                    Cutoff: {cutoff.toFixed(0)} Hz
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="8000"
                    step="10"
                    value={cutoff}
                    onChange={(e) => setCutoff(parseFloat(e.target.value))}
                    className="w-full h-8"
                  />
                </div>
                
                <div>
                  <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                    Resonance: {resonance.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    step="0.5"
                    value={resonance}
                    onChange={(e) => setResonance(parseFloat(e.target.value))}
                    className="w-full h-8"
                  />
                </div>
              </div>
            </div>
          </div>
          
          {/* Envelope */}
          <div className="bg-gray-800 rounded-lg shadow-xl p-4 md:p-6">
            <h2 className="text-lg md:text-xl font-bold text-white mb-3">📊 Envelope (ADSR)</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                  Attack: {attack.toFixed(2)}s
                </label>
                <input
                  type="range"
                  min="0.001"
                  max="2"
                  step="0.01"
                  value={attack}
                  onChange={(e) => setAttack(parseFloat(e.target.value))}
                  className="w-full h-8"
                />
              </div>
              
              <div>
                <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                  Decay: {decay.toFixed(2)}s
                </label>
                <input
                  type="range"
                  min="0.001"
                  max="2"
                  step="0.01"
                  value={decay}
                  onChange={(e) => setDecay(parseFloat(e.target.value))}
                  className="w-full h-8"
                />
              </div>
              
              <div>
                <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                  Sustain: {sustain.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={sustain}
                  onChange={(e) => setSustain(parseFloat(e.target.value))}
                  className="w-full h-8"
                />
              </div>
              
              <div>
                <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                  Release: {release.toFixed(2)}s
                </label>
                <input
                  type="range"
                  min="0.001"
                  max="3"
                  step="0.01"
                  value={release}
                  onChange={(e) => setRelease(parseFloat(e.target.value))}
                  className="w-full h-8"
                />
              </div>
            </div>
          </div>
          
          {/* LFO and Output */}
          <div className="bg-gray-800 rounded-lg shadow-xl p-4 md:p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h2 className="text-lg md:text-xl font-bold text-white mb-3">〰️ LFO</h2>
                <div className="space-y-3">
                  <div>
                    <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                      Rate: {lfoRate.toFixed(1)} Hz
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      step="0.1"
                      value={lfoRate}
                      onChange={(e) => setLfoRate(parseFloat(e.target.value))}
                      className="w-full h-8"
                    />
                  </div>
                  
                  <div>
                    <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                      Depth: {lfoDepth.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={lfoDepth}
                      onChange={(e) => setLfoDepth(parseFloat(e.target.value))}
                      className="w-full h-8"
                    />
                  </div>
                </div>
              </div>
              
              <div>
                <h2 className="text-lg md:text-xl font-bold text-white mb-3 flex items-center gap-2">
                  <Volume2 className="w-4 h-4 md:w-5 md:h-5" />
                  Output
                </h2>
                <div className="space-y-3">
                  <div>
                    <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                      Volume: {(volume * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="0.5"
                      step="0.01"
                      value={volume}
                      onChange={(e) => setVolume(parseFloat(e.target.value))}
                      className="w-full h-8"
                    />
                  </div>
                  
                  <div>
                    <label className="text-white text-xs md:text-sm mb-1 block font-medium">
                      Octave: {octave}
                    </label>
                    <input
                      type="range"
                      min="2"
                      max="6"
                      step="1"
                      value={octave}
                      onChange={(e) => setOctave(parseInt(e.target.value))}
                      className="w-full h-8"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Virtual Keyboard */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-3 md:p-6">
          <h2 className="text-lg md:text-xl font-bold text-white mb-4 text-center">🎹 Tap Keys to Play</h2>
          
          <div className="flex justify-center gap-0.5 md:gap-1 mb-4 overflow-x-auto pb-2">
            {keys.map((key) => (
              <button
                key={key.name}
                onTouchStart={(e) => {
                  e.preventDefault();
                  handleKeyPress(key.note, key.name);
                }}
                onTouchEnd={(e) => {
                  e.preventDefault();
                  handleKeyRelease();
                }}
                onMouseDown={() => handleKeyPress(key.note, key.name)}
                onMouseUp={handleKeyRelease}
                onMouseLeave={handleKeyRelease}
                className={`
                  ${key.black 
                    ? 'bg-gray-900 hover:bg-gray-700 text-white h-20 md:h-24 w-10 md:w-12 -mx-2 md:-mx-3 z-10' 
                    : 'bg-white hover:bg-gray-100 text-gray-900 h-28 md:h-32 w-12 md:w-16'
                  }
                  ${activeKey === key.name ? 'ring-4 ring-purple-500 brightness-75' : ''}
                  rounded-b-lg font-bold text-xs md:text-sm shadow-lg transition-all active:brightness-75
                  flex flex-col items-center justify-end pb-1 md:pb-2 touch-none select-none
                `}
                style={{ touchAction: 'none' }}
              >
                {key.name}
                {!key.black && <span className="text-xs mt-1">{octave}</span>}
              </button>
            ))}
          </div>
          
          <div className="flex flex-col md:flex-row gap-2 justify-center">
            <button
              onTouchStart={(e) => {
                e.preventDefault();
                handleKeyPress(0, 'Test');
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                handleKeyRelease();
              }}
              onMouseDown={() => handleKeyPress(0, 'Test')}
              onMouseUp={handleKeyRelease}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-4 md:py-3 rounded-lg font-bold text-base md:text-base transition-all active:scale-95"
              style={{ touchAction: 'none' }}
            >
              🎵 Test Note (C{octave})
            </button>
            <button
              onClick={stopNote}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-4 md:py-3 rounded-lg font-bold text-base md:text-base transition-all active:scale-95"
            >
              🔇 Stop All
            </button>
          </div>
        </div>
        
        {/* Info */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-4 md:p-6 mt-4 md:mt-6">
          <h3 className="text-base md:text-lg font-bold text-white mb-2">💡 Quick Tips</h3>
          <div className="text-gray-300 space-y-1 text-xs md:text-sm">
            <p>• <strong>Bass:</strong> Try the Bass preset, it's huge!</p>
            <p>• <strong>Acid:</strong> Square wave + high resonance + short envelope</p>
            <p>• <strong>Lead:</strong> Add some LFO for vibrato effect</p>
            <p className="mt-3 text-green-400 font-medium">✓ Optimized for mobile - tap and play!</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SH101Synth;
