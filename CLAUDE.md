# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based modular synthesizer sound installation that generates constrained random audio compositions using virtual synth modules. The project creates a 4-channel audio output system using the `pyo` library for real-time audio synthesis.

## Development Setup

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Run main application
python main.py
```

## Key Architecture Components

### Module System
All synthesizer modules inherit from `BaseModule` in `src/modules/base_module.py`, providing:
- **Parameters**: Configuration values (frequency, gain, etc.)
- **Input/Output ports**: For audio and control voltage (CV) signals
- **Lifecycle**: `start()`, `stop()`, `process()` methods
- **Logging**: Uses Python's logging module instead of print statements

### Connection Management
The `ConnectionManager` in `src/connection.py` handles module interconnections:
- Registers modules by name
- Manages audio/CV signal routing between modules
- Supports different signal types (AUDIO, CV, GATE, TRIGGER)

### Core Modules (All Implemented)
- **VCO** (Voltage Controlled Oscillator): Generates basic waveforms (sine, saw, square, triangle, noise)
- **VCF** (Voltage Controlled Filter): Low-pass filter with cutoff frequency and Q control
- **VCA** (Voltage Controlled Amplifier): Volume control with support for CV and PyoObject inputs
- **LFO** (Low Frequency Oscillator): Generates control signals for modulation
- **ENV** (Envelope Generator): Creates ADSR envelopes with gate triggering

## Critical Development Notes

### Audio Output Pattern
When testing audio modules, follow this pattern for proper sound output:

```python
# 1. Setup pyo server
s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

# 2. Create and connect modules via ConnectionManager
cm = ConnectionManager()
vco = VCO(name="test_vco")
vca = VCA(name="test_vca")
cm.register_module("test_vco", vco)
cm.register_module("test_vca", vca)

# 3. Start modules
vco.start()
vca.start()

# 4. Connect modules
cm.connect("test_vco", "audio_out", "test_vca", "audio_in", SignalType.AUDIO)

# 5. Process VCA to apply connections
vca.process()

# 6. Output to audio channel
vca.out_to_channel(0)

# 7. IMPORTANT: Use continuous time.sleep() for audio playback
time.sleep(5)  # NOT fragmented loops with small sleeps

# 8. Cleanup
s.stop()
s.shutdown()
```

### Test Files
- `tests/manual/test_vco_vca_connection.py`: Tests basic VCO->VCA connections with detailed debugging
- `tests/manual/test_vcf_lfo_env.py`: Tests VCF, LFO, and ENV modules with audio output

### Logging Configuration
Always configure logging in main entry points:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### pyo Audio Engine
- Uses `pyo` library for real-time audio synthesis
- Requires proper server initialization before module creation
- Audio output must be continuous (use `time.sleep(5)` not `time.sleep(0.1)` loops)
- Supports 4-channel output via macOS Aggregate Device

## Important Development Practices

### 1. Always Call process() After Changes
```python
# After connecting modules
cm.connect("vco", "audio_out", "vca", "audio_in", SignalType.AUDIO)
vca.process()  # REQUIRED: Apply the connection

# After changing parameters
vcf.set_frequency(1000)
vcf.process()  # REQUIRED: Apply the parameter change
```

### 2. Process Modules in Signal Flow Order
```python
# Correct order: input → output
vcf.process()  # Process filter first
vca.process()  # Process amplifier second
```

### 3. VCA Supports Both CV Types
```python
# Numeric CV control
vca.set_gain(0.5)  # Direct numeric value

# PyoObject CV control (from ENV)
cm.connect("env", "cv_out", "vca", "gain_cv", SignalType.CV)  # Direct PyoObject
```

### 4. Proper Server Lifecycle
```python
try:
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()
    # ... your code ...
finally:
    s.stop()
    s.shutdown()
```

## Project Structure

```
modular_project/
├── src/
│   ├── connection.py              # Connection management system
│   ├── generator.py               # Constrained random generation (planned)
│   └── modules/
│       ├── base_module.py         # Base class for all modules
│       ├── vco.py                 # Voltage Controlled Oscillator
│       ├── vcf.py                 # Voltage Controlled Filter
│       ├── vca.py                 # Voltage Controlled Amplifier
│       ├── lfo.py                 # Low Frequency Oscillator
│       └── env.py                 # Envelope Generator (ADSR)
├── tests/
│   └── manual/
│       ├── test_vco_vca_connection.py   # Basic VCO->VCA connection test
│       └── test_vcf_lfo_env.py          # Advanced modules test
├── doc/
│   ├── MODULAR_GUIDE.md          # Usage guide and patching techniques
│   ├── MANUAL.md                 # Project setup and build instructions
│   └── [1-3].md                  # Development history and debug records
└── main.py                       # Main application entry point
```

## Additional Documentation

For more detailed information, refer to these documents:

- **Development Setup & Build Process**: See [`doc/MANUAL.md`](doc/MANUAL.md) for complete project setup instructions and development workflow
- **Modular Synthesizer Usage**: See [`doc/MODULAR_GUIDE.md`](doc/MODULAR_GUIDE.md) for detailed patching techniques, module usage patterns, and practical examples
- **Module Technical Details**: See [`src/modules/README.md`](src/modules/README.md) for comprehensive module specifications and API documentation

## Common Commands

```bash
# Run main application
python main.py

# Test basic connections
python tests/manual/test_vco_vca_connection.py

# Test advanced modules (VCF, LFO, ENV)
python tests/manual/test_vcf_lfo_env.py

# Code formatting
black --line-length 119 src/
```