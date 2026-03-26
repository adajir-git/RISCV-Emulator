# RISC-V Emulator (RV32I)

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A RISC-V (RV32I) processor emulator implemented in Python. This project simulates the base RISC-V instruction set architecture including arithmetic operations, logical operations, memory access, and conditional branching.

## Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Supported Instructions](#-supported-instructions)
- [Installation](#-installation)
- [Usage](#-usage)
- [Examples](#-examples)
- [Testing](#-testing)
- [Technical Details](#-technical-details)
- [Author](#-author)

## Features

- **Complete CPU simulation**: Implementation of fetch-decode-execute cycle
- **Memory subsystem**: Byte-addressable memory with Little Endian support
- **32 general-purpose registers**: Full support for RISC-V register architecture
- **Interactive mode**: Calculator for quick operation testing
- **Demo programs**: Including Fibonacci sequence computation
- **Unit tests**: Automated implementation correctness testing
- **Debug output**: Detailed instruction execution trace

## Architecture

The emulator consists of three main components:

### 1. Memory
- Size: 1 MB (configurable)
- Addressing: Byte-addressable
- Endianness: Little Endian
- Operations: `read_8()`, `write_8()`, `read_32()`, `write_32()`

### 2. CPU (Central Processing Unit)
- Registers: 32 general-purpose (x0-x31)
- Program Counter (PC): 32-bit
- Word size: 32 bits
- Cycle: Fetch → Decode → Execute

### 3. Testing Framework
- Unit tests for memory, arithmetic, and branching
- Automated result validation

## Supported Instructions

### Arithmetic Operations
| Instruction | Type | Description |
|-----------|-----|-------|
| `ADDI` | I-Type | Add immediate to register |
| `ADD` | R-Type | Add two registers |
| `SUB` | R-Type | Subtract two registers |

### Logical Operations
| Instruction | Type | Description |
|-----------|-----|-------|
| `ANDI` | I-Type | Bitwise AND with immediate |
| `AND` | R-Type | Bitwise AND of two registers |
| `OR` | R-Type | Bitwise OR of two registers |
| `XOR` | R-Type | Bitwise XOR of two registers |

### Memory Operations
| Instruction | Type | Description |
|-----------|-----|-------|
| `LW` | I-Type | Load Word from memory |
| `SW` | S-Type | Store Word to memory |

### Conditional Branches
| Instruction | Type | Description |
|-----------|-----|-------|
| `BEQ` | B-Type | Branch if registers are equal |
| `BNE` | B-Type | Branch if registers are not equal |

## Installation

### Requirements
- Python 3.7 or higher
- No external dependencies (uses only the standard library)

### Setup

```bash
# Clone the repository
git clone https://github.com/adajir-git/RISCV-Emulator.git
cd RISCV-Emulator

# Run the emulator
python riscv_emulator.py
```

## Usage

### Interactive Mode

After running the program, a menu will appear with the following options:

```
RISC-V EMULATOR
========================================

Select operation:
1: Addition (ADD)
2: Subtraction (SUB)
3: AND
4: OR
5: Fibonacci
6: Tests
0: Exit
```

### Programmatic Usage

```python
from riscv_emulator import Memory, CPU

# Create memory and CPU
ram = Memory()
cpu = CPU(ram)

# Load program (machine code)
program = [
    0x00A00093,  # ADDI x1, x0, 10
    0x01400113,  # ADDI x2, x0, 20
    0x002081B3   # ADD x3, x1, x2
]
ram.load_program(program)

# Execute
cpu.run()

# Result
print(f"x3 = {cpu.get_reg(3)}")  # Output: x3 = 30
```

## Examples

### Example 1: Simple Calculation

```
Select operation:
1: Addition (ADD)
2: Subtraction (SUB)
3: AND
4: OR
5: Fibonacci
6: Tests
0: Exit

Your choice: 1
Enter first number (A): 15
Enter second number (B): 27

--- START COMPUTATION CYCLE ---
[FETCH]  Address: 0x0000 | Instruction: 0x002081B3
[EXEC]   ADD: x3 = x1(15) + x2(27)
[WRITE]  Storing value 42 to register x3
  --- END COMPUTATION CYCLE ---

Result: 15 + 27 = 42
```

### Example 2: Fibonacci Sequence

The program calculates the 7th Fibonacci number:

```
Your choice: 5

--- DEMO: FIBONACCI SEQUENCE ---
Loading machine code into memory
Starting CPU...

[FINAL] Result (7th number) in register x1: 13
[FINAL] Result stored in memory RAM[0]: 13
```

## Testing

The emulator includes a comprehensive unit test suite:

```bash
# Run all tests
python -m unittest riscv_emulator.TestEmulator

# Or interactively
python riscv_emulator.py
# Select option 6: Tests
```

### Test Coverage:
- ✅ Memory operations (endianness)
- ✅ Arithmetic instructions
- ✅ Conditional branches
- ✅ Register operations

## Technical Details

### Instruction Formats

The emulator supports the following RISC-V instruction types:

- **R-Type**: `funct7 | rs2 | rs1 | funct3 | rd | opcode`
- **I-Type**: `imm[11:0] | rs1 | funct3 | rd | opcode`
- **S-Type**: `imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode`
- **B-Type**: `imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode`

### Memory Organization

```
Address   Byte 0    Byte 1    Byte 2    Byte 3
0x0000    [  LSB  ] [       ] [       ] [  MSB  ]  <- Little Endian
0x0004    [       ] [       ] [       ] [       ]
...
```

### Register x0

Register `x0` is hardwired to zero per RISC-V specification:
- Reads always return 0
- Writes are ignored

## Repository Structure

```
RISCV-Emulator/
│
├── riscv_emulator.py    # Main emulator file
├── README.md            # This documentation
└── LICENSE              # Project license
```

## Academic Context

This project was created as part of the **Programming 1 (NPRG030)** course at the Faculty of Mathematics and Physics, Charles University.

- **Semester**: Winter 2025/2026
- **Year**: 1st year
- **Major**: Computer Science

## Author

**Adam Jiřík**
- GitHub: [@adajir-git](https://github.com/adajir-git)
- Project: [RISC-V Emulator](https://github.com/adajir-git/RISCV-Emulator)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- RISC-V Foundation for the open ISA specification
- Faculty of Mathematics and Physics, Charles University for educational support

## References

- [RISC-V Specification](https://riscv.org/technical/specifications/)
- [RISC-V ISA Reference](https://github.com/riscv/riscv-isa-manual)
- [Python Documentation](https://docs.python.org/3/)

---

<div align="center">
Made with ❤️  for learning computer architecture
</div>
