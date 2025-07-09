# Pyo Signal Generators Complete Documentation

A comprehensive reference for signal generators available in Pyo for audio synthesis.

## Table of Contents

1. [Basic Oscillators](#basic-oscillators)
2. [Noise Generators](#noise-generators)
3. [Complex Waveform Generators](#complex-waveform-generators)
4. [Chaotic Generators](#chaotic-generators)
5. [FM Synthesis](#fm-synthesis)
6. [Special Oscillators](#special-oscillators)
7. [Input & Control](#input--control)

---

## Basic Oscillators

### Sine
```python
Sine(freq=1000, phase=0, mul=1, add=0)
```

**Description**: A simple sine wave oscillator

**Parameters**:
- `freq`: Frequency in cycles per second, default: 1000
- `phase`: Phase of sampling, expressed as a fraction of a cycle (0 to 1), default: 0
- `mul`: Amplitude multiplier, default: 1
- `add`: Addition value, default: 0

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setPhase(x)`: Replace the phase attribute
- `reset()`: Resets current phase to 0

**Example**:
```python
# 440Hz sine wave
sine = Sine(freq=440, mul=0.5)
sine.out()
```

---

### Phasor
```python
Phasor(freq=100, phase=0, mul=1, add=0)
```

**Description**: A simple phase incrementor. Output is a periodic ramp from 0 to 1.

**Parameters**:
- `freq`: Frequency in cycles per second, default: 100
- `phase`: Phase of sampling, expressed as a fraction of a cycle (0 to 1), default: 0

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setPhase(x)`: Replace the phase attribute
- `reset()`: Resets current phase to 0

**Example**:
```python
# 100Hz ramp wave
ramp = Phasor(freq=100)
ramp.out()
```

---

### RCOsc
```python
RCOsc(freq=100, sharp=0.25, mul=1, add=0)
```

**Description**: Waveform approximation of a RC circuit (logarithmic growth followed by exponential decay)

**Parameters**:
- `freq`: Frequency in cycles per second, default: 100
- `sharp`: Slope of the attack and decay of the waveform, between 0 and 1, default: 0.25
  - 0: Triangular waveform
  - 1: Almost square wave

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setSharp(x)`: Replace the sharp attribute
- `reset()`: Resets current phase to 0

**Example**:
```python
# RC circuit-like waveform
rc = RCOsc(freq=220, sharp=0.5)
rc.out()
```

---

### SuperSaw
```python
SuperSaw(freq=100, detune=0.5, bal=0.7, mul=1, add=0)
```

**Description**: Roland JP-8000 Supersaw emulator. Uses 7 sawtooth oscillators detuned against each other.

**Parameters**:
- `freq`: Frequency in cycles per second, default: 100
- `detune`: Depth of the detuning, between 0 and 1, default: 0.5
  - 0: All oscillators tuned to the same frequency
  - 1: Maximum detuning
- `bal`: Balance between central oscillator and sideband oscillators, default: 0.7
  - 0: Only central oscillator
  - 1: Mix of all oscillators with central one lower

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setDetune(x)`: Replace the detune attribute
- `setBal(x)`: Replace the bal attribute

**Example**:
```python
# Supersaw with moderate detuning
supersaw = SuperSaw(freq=110, detune=0.7, bal=0.8)
supersaw.out()
```

---

## Noise Generators

### Noise
```python
Noise(mul=1, add=0)
```

**Description**: A white noise generator

**Parameters**:
- `type`: Generation algorithm (0 or 1)
  - 0: Uses system rand() method (default)
  - 1: Simple linear congruential generator (cheaper)

**Methods**:
- `setType(x)`: Sets the generation algorithm

**Example**:
```python
# White noise
noise = Noise(mul=0.1)
noise.out()
```

---

### PinkNoise
```python
PinkNoise(mul=1, add=0)
```

**Description**: A pink noise generator. Paul Kellet's implementation with -10dB/decade filter.

**Features**: Accurate to within ±0.05dB above 9.2Hz (44100Hz sampling rate)

**Example**:
```python
# Pink noise
pink = PinkNoise(mul=0.1)
pink.out()
```

---

### BrownNoise
```python
BrownNoise(mul=1, add=0)
```

**Description**: A brown noise generator. Power density decreases 6dB per octave (density proportional to 1/f²).

**Example**:
```python
# Brown noise
brown = BrownNoise(mul=0.1)
brown.out()
```

---

## Complex Waveform Generators

### LFO
```python
LFO(freq=100, sharp=0.5, type=0, mul=1, add=0)
```

**Description**: Band-limited Low Frequency Oscillator with different wave shapes

**Parameters**:
- `freq`: Oscillator frequency in cycles per second, default: 100
- `sharp`: Sharpness factor between 0 and 1, default: 0.5
- `type`: Waveform type (0-7), default: 0
  - 0: Saw up
  - 1: Saw down
  - 2: Square
  - 3: Triangle
  - 4: Pulse
  - 5: Bipolar pulse
  - 6: Sample and hold
  - 7: Modulated Sine

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setSharp(x)`: Replace the sharp attribute
- `setType(x)`: Replace the type attribute
- `reset()`: Resets current phase to 0

**Example**:
```python
# Triangle wave LFO
lfo = LFO(freq=2, type=3, mul=0.5)
lfo.out()
```

---

### Blit
```python
Blit(freq=100, harms=40, mul=1, add=0)
```

**Description**: Band limited impulse train synthesis. Low aliasing oscillator with harmonic control.

**Parameters**:
- `freq`: Frequency in cycles per second, default: 100
- `harms`: Number of harmonics in the generated spectrum, default: 40

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setHarms(x)`: Replace the harms attribute

**Example**:
```python
# Band-limited impulse train
blit = Blit(freq=220, harms=20)
blit.out()
```

---

### SumOsc
```python
SumOsc(freq=100, ratio=0.5, index=0.5, mul=1, add=0)
```

**Description**: Discrete summation formulae to produce complex spectra. Based on James A. Moorer's paper.

**Formula**: `(sin(theta) - a * sin(theta - beta)) / (1 + a**2 - 2 * a * cos(beta))`

**Parameters**:
- `freq`: Base frequency in cycles per second, default: 100
- `ratio`: Factor to stretch/compress partial series, default: 0.5
- `index`: Damping of successive partials (0-1), default: 0.5
  - 0.5: Each partial is 6dB lower than previous

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setRatio(x)`: Replace the ratio attribute
- `setIndex(x)`: Replace the index attribute

**Example**:
```python
# Complex spectrum oscillator
sum_osc = SumOsc(freq=220, ratio=0.75, index=0.3)
sum_osc.out()
```

---

## Chaotic Generators

### Lorenz
```python
Lorenz(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)
```

**Description**: Chaotic attractor for the Lorenz system. Three non-linear differential equations.

**Parameters**:
- `pitch`: Speed of variations (0-1), default: 0.25
  - Below 0.2: LFO usage
  - Above 0.2: Broad spectrum noise
- `chaos`: Chaotic behavior (0-1), default: 0.5
  - 0: Nearly periodic
  - 1: Totally chaotic
- `stereo`: If True, generates X and Y variables (180° out of phase), default: False

**Methods**:
- `setPitch(x)`: Replace the pitch attribute
- `setChaos(x)`: Replace the chaos attribute

**Example**:
```python
# Chaotic LFO
lorenz = Lorenz(pitch=0.1, chaos=0.8, stereo=True)
lorenz.out()
```

---

### Rossler
```python
Rossler(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)
```

**Description**: Chaotic attractor for the Rossler system. Similar to Lorenz but different characteristics.

**Parameters**: Same as Lorenz

**Example**:
```python
# Rossler chaotic oscillator
rossler = Rossler(pitch=0.3, chaos=0.6)
rossler.out()
```

---

### ChenLee
```python
ChenLee(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)
```

**Description**: Chaotic attractor for the Chen-Lee system. Another chaotic system with unique properties.

**Parameters**: Same as Lorenz

**Example**:
```python
# Chen-Lee chaotic oscillator
chenlee = ChenLee(pitch=0.2, chaos=0.7)
chenlee.out()
```

---

## FM Synthesis

### FM
```python
FM(carrier=100, ratio=0.5, index=5, mul=1, add=0)
```

**Description**: Simple frequency modulation generator based on Chowning's algorithm.

**Parameters**:
- `carrier`: Carrier frequency in cycles per second, default: 100
- `ratio`: Modulator/carrier frequency ratio, default: 0.5
- `index`: Modulation index (modulator amplitude), default: 5

**Methods**:
- `setCarrier(x)`: Replace the carrier attribute
- `setRatio(x)`: Replace the ratio attribute
- `setIndex(x)`: Replace the index attribute

**Example**:
```python
# Classic FM synthesis
fm = FM(carrier=440, ratio=1.5, index=3)
fm.out()
```

---

### CrossFM
```python
CrossFM(carrier=100, ratio=0.5, ind1=2, ind2=2, mul=1, add=0)
```

**Description**: Cross frequency modulation where both oscillators modulate each other.

**Parameters**:
- `carrier`: Carrier frequency in cycles per second, default: 100
- `ratio`: Modulator/carrier frequency ratio, default: 0.5
- `ind1`: Carrier index (carrier amplitude for modulating modulator), default: 2
- `ind2`: Modulation index (modulator amplitude for modulating carrier), default: 2

**Methods**:
- `setCarrier(x)`: Replace the carrier attribute
- `setRatio(x)`: Replace the ratio attribute
- `setInd1(x)`: Replace the ind1 attribute
- `setInd2(x)`: Replace the ind2 attribute

**Example**:
```python
# Cross FM synthesis
cross_fm = CrossFM(carrier=220, ratio=0.75, ind1=1.5, ind2=2.5)
cross_fm.out()
```

---

## Special Oscillators

### FastSine
```python
FastSine(freq=1000, initphase=0.0, quality=1, mul=1, add=0)
```

**Description**: Fast sine wave approximation using parabola formula. Faster than table lookup.

**Parameters**:
- `freq`: Frequency in cycles per second, default: 1000
- `initphase`: Initial phase (0-1), default: 0.0
- `quality`: Approximation quality (0 or 1), default: 1
  - 1: More accurate but more CPU intensive
  - 0: Less accurate but very fast (good for LFO)

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setQuality(x)`: Replace the quality attribute
- `reset()`: Resets current phase to 0

**Example**:
```python
# Fast sine for LFO
fast_sine = FastSine(freq=2, quality=0, mul=0.5)
```

---

### SineLoop
```python
SineLoop(freq=1000, feedback=0, mul=1, add=0)
```

**Description**: Sine wave oscillator with feedback for brightness control.

**Parameters**:
- `freq`: Frequency in cycles per second, default: 1000
- `feedback`: Feedback amount (0-1), controls brightness, default: 0

**Methods**:
- `setFreq(x)`: Replace the freq attribute
- `setFeedback(x)`: Replace the feedback attribute

**Example**:
```python
# Sine with feedback
sine_loop = SineLoop(freq=440, feedback=0.3)
sine_loop.out()
```

---

## Input & Control

### Input
```python
Input(chnl=0, mul=1, add=0)
```

**Description**: Read from a numbered channel in an external audio signal.

**Parameters**:
- `chnl`: Input channel to read from, default: 0

**Note**: Requires Server's duplex mode set to 1

**Example**:
```python
# Read from input channel 0
input_signal = Input(chnl=0, mul=0.5)
input_signal.out()
```

---

## Common Methods

All generators inherit from `PyoObject` and have these common methods:

### Audio Methods
- `out(chnl=0, inc=1, dur=0, delay=0)`: Send to audio output
- `play(dur=0, delay=0)`: Start processing without output
- `stop(wait=0)`: Stop processing

### Control Methods
- `setMul(x)`: Set amplitude multiplier
- `setAdd(x)`: Set addition value
- `setSub(x)`: Set subtraction value
- `setDiv(x)`: Set division value
- `set(attr, value, port=0.03, callback=None)`: Set any attribute with portamento

### Utility Methods
- `get(all=False)`: Get current sample value
- `mix(voices=1)`: Mix streams into fewer voices
- `range(min, max)`: Adjust mul/add for given range
- `ctrl()`: Open GUI control window

---

## Usage Examples

### Basic Oscillator Setup
```python
from pyo import *

# Initialize server
s = Server().boot()
s.start()

# Create oscillators
sine = Sine(freq=440, mul=0.3)
phasor = Phasor(freq=110, mul=0.2)

# Send to output
sine.out(chnl=0)
phasor.out(chnl=1)
```

### FM Synthesis Example
```python
# FM synthesis with LFO modulation
lfo = LFO(freq=0.5, type=0, mul=2)
fm = FM(carrier=220, ratio=1.414, index=3 + lfo)
fm.out()
```

### Noise Filtering Example
```python
# Pink noise through resonant filter
pink = PinkNoise(mul=0.1)
filtered = Biquad(pink, freq=1000, q=5, type=0)
filtered.out()
```

### Chaotic Modulation Example
```python
# Chaotic modulation of SuperSaw
chaos = Lorenz(pitch=0.1, chaos=0.8, mul=50)
supersaw = SuperSaw(freq=110 + chaos, detune=0.6)
supersaw.out()
```

This documentation covers all signal generators available in Pyo. Each generator provides unique sonic characteristics suitable for different synthesis techniques and musical applications.