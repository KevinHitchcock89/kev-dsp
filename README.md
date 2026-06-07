# Digital Communications Platform

## Overview
This project documents the design and implementation of a modular baseband digital communication system, beginning with a BPSK transmit/receive chain and progressing toward FPGA deployment.

The goal is to explore matched filtering, noise performance, synchronization sensitivity, and fixed-point implementation considerations.

## Folder Structure
    digital-comms-platform/
    │
    ├── python_model/
    │   ├── bpsk/
    │   │   └── main.py
    │   ├── channel/
    │   ├── filters/
    │   └── utils/
    │
    ├── docs/
    │   └── system_architecture.md
    │
    ├── results/
    │
    ├── requirements.txt
    ├── README.md
    └── .gitignore

## Phase 1 – BPSK System (Python Simulation)
- Bit generation
- Symbol mapping
- AWGN channel modeling
- Matched filtering
- BER vs Eb/N0 validation
- Timing and phase sensitivity analysis

## Future Phases
- QPSK and higher-order modulation
- Synchronization algorithms
- Fixed-point modeling
- FPGA implementation

## Tools
- Python
- NumPy
- SciPy
- Matplotlib

## Author
Kevin Hitchcock