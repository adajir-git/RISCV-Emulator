# Emulátor procesoru RISC-V (RV32I)
# Autor: Adam Jiřík, I. ročník, obor Informatika
# Zimní semestr 2025/2026, Programování 1 (NPRG030)

import unittest
from sys import stdin

# ==========================================
# CAST 1: PAMET (MEMORY)
# ==========================================

# --- KONSTANTY PRO PAMET ---
DEFAULT_MEM_SIZE = 1024 * 1024  # Vychozi velikost 1 MB
WORD_BYTES = 4                  # 32-bitove slovo ma 4 bajty
BYTE_MASK = 0xFF                # Maska pro ziskani 8 bitu (1 bajtu)
SHIFT_8 = 8                     # Posun o 1 bajt
SHIFT_16 = 16                   # Posun o 2 bajty
SHIFT_24 = 24                   # Posun o 3 bajty
# ---------------------------

class Memory:
    """
    Trida simulujici operacni pamet (RAM).
    
    Implementuje byte-addressable pamet v Little Endian zapisu/cteni
    pro 32-bitova slova, coz je vyzadovano architekturou RISC-V.
    """
    def __init__(self, size=DEFAULT_MEM_SIZE):
        """
        Inicializace pameti.
        :parametr size: Velikost pameti v bajtech (default: 1 MB)
        """
        self.memory = [0] * size
        self.size = size

    def load_program(self, data, start_address=0):
        """
        Nahraje strojovy kod (seznam 32-bitovych integeru) do pameti.
        
        Protoze pamet je adresovatelna po bajtech, kazde 32-bitove slovo
        musi byt rozdeleno na 4 bajty a ulozeno v poradi Little Endian
        (nejmene vyznamny bajt na nejnizsi adrese)
        """
        # reset pameti pred kazdym programem (vycistime bordel)
        for i in range(len(data) * WORD_BYTES): 
            if start_address + i < self.size:
                self.memory[start_address + i] = 0

        for i, instruction in enumerate(data):
            # rozklad 32-bit instrukce na 4 bajty pomoci bitovych posunu a maskovani
            # priklad: 0x12345678 -> byte_0=0x78, byte_1=0x56, byte_2=0x34, byte_3=0x12
            byte_0 = instruction & BYTE_MASK          # LSB (Least Significant Byte)
            byte_1 = (instruction >> SHIFT_8) & BYTE_MASK
            byte_2 = (instruction >> SHIFT_16) & BYTE_MASK
            byte_3 = (instruction >> SHIFT_24) & BYTE_MASK  # MSB (Most Significant Byte)
            
            # vypocet fyzicke adresy (kazda instrukce zabere 4 bajty)
            address = start_address + (i * WORD_BYTES)
            
            # pokud se program vejde do pameti, zapisujeme, jinak vypiseme chybu
            if address + (WORD_BYTES - 1) < self.size:
                self.memory[address]     = byte_0
                self.memory[address + 1] = byte_1
                self.memory[address + 2] = byte_2
                self.memory[address + 3] = byte_3
            else:
                print("Chyba: Program se nevejde do pameti!")
                break

    def read_8(self, address):
        """Precte jeden bajt z dane adresy (simulace LOAD BYTE)"""
        if address < 0 or address >= self.size: # pojistka spravne adresy (v rozmezi memory)
           return 0
        return self.memory[address]

    def write_8(self, address, value):
        """Zapise jeden bajt na danou adresu (simulace STORE BYTE)"""
        if address < 0 or address >= self.size: 
            return
        self.memory[address] = value & BYTE_MASK # zajisti ze zapiseme opravdu jen jeden byte

    def read_32(self, address):
        """
        Precte 32-bitove slovo (4 bajty) z pameti.
        Sklada bajty zpet do slova v Little Endian poradi
        """
        byte_0 = self.read_8(address)
        byte_1 = self.read_8(address + 1)
        byte_2 = self.read_8(address + 2)
        byte_3 = self.read_8(address + 3)
        # skladani: byte_0 je spodnich 8 bitu, byte_1 dalsich 8, atd.
        return byte_0 | (byte_1 << SHIFT_8) | (byte_2 << SHIFT_16) | (byte_3 << SHIFT_24)

    def write_32(self, address, value):
        """
        Zapise 32-bitove slovo do pameti.
        Rozklada slovo na 4 bajty (Little Endian)
        """
        byte_0 = value & BYTE_MASK
        byte_1 = (value >> SHIFT_8) & BYTE_MASK
        byte_2 = (value >> SHIFT_16) & BYTE_MASK
        byte_3 = (value >> SHIFT_24) & BYTE_MASK
        self.write_8(address, byte_0)
        self.write_8(address + 1, byte_1)
        self.write_8(address + 2, byte_2)
        self.write_8(address + 3, byte_3)

# ==========================================
# CAST 2: PROCESOR (CPU)
# ==========================================

# --- KONSTANTY PRO CPU ---
WORD_SIZE = 4                  # Velikost instrukce v bajtech (posun PC)
MASK_32_BIT = 0xFFFFFFFF       # Omezeni na 32 bitu pro registry

# Masky pro dekodovani instrukce
MASK_OPCODE = 0x7F
MASK_REG = 0x1F
MASK_FUNCT3 = 0x07
MASK_FUNCT7 = 0x7F

# Operacni kody (Opcodes - spodnich 7 bitu)
OPCODE_ALU_I = 0x13            # Aritmetika s konstantou (ADDI, ANDI)
OPCODE_ALU_R = 0x33            # Aritmetika se dvema registry (ADD, SUB, AND, OR, XOR)
OPCODE_LOAD  = 0x03            # Cteni z pameti (LW)
OPCODE_STORE = 0x23            # Zapis do pameti (SW)
OPCODE_BRANCH = 0x63           # Podminene skoky (BEQ, BNE)

# Funkce (Funct3)
F3_ADD_SUB_BEQ = 0x0           # Sdileny kod 0x0 pro ADD, SUB, ADDI, BEQ
F3_BNE = 0x1
F3_MEM = 0x2                   # Sdileny kod 0x2 pro LW, SW
F3_XOR = 0x4
F3_OR = 0x6
F3_AND = 0x7                   # Sdileny kod 0x7 pro AND, ANDI

# Rozsireni (Funct7)
F7_DEFAULT = 0x00              # Standardni operace (ADD, logicke op.)
F7_SUB = 0x20                  # Priznak pro odecitani (SUB)

# Znamenkove rozsireni (Sign Extension)
SIGN_BIT_12 = 0x800            # Kontrola 12. bitu
SIGN_EXT_12 = 0x1000           # Odecteni 2^12
SIGN_BIT_13 = 0x1000           # Kontrola 13. bitu
SIGN_EXT_13 = 0x2000           # Odecteni 2^13

MAX_INT_32 = 0x7FFFFFFF        # Maximalni kladne 32-bitove cislo
SIGN_EXT_32 = 0x100000000      # Odecteni 2^32 pro zaporna cisla
# -------------------------

class CPU:
    """
    Emulator procesoru architektury RISC-V
    Implementuje cyklus Fetch-Decode-Execute
    """
    def __init__(self, memory):
        self.memory = memory
        self.pc = 0           # program Counter (aktualni adresa instrukce)
        self.regs = [0] * 32  # 32 univerzalnich registru (x0 - x31)

    def dump_registers(self):
        """Vypis obsahu registru pro ladici ucely"""
        print("-" * 20 + " REGISTERS " + "-" * 20)
        for i in range(0, 32, 4):
            line = ""
            for j in range(4):
                reg_idx = i + j
                value = self.regs[reg_idx]
                # Zobrazeni jako signed integer pro lepsi citelnost
                if value > MAX_INT_32: 
                    value -= SIGN_EXT_32
                line += f"x{reg_idx:02d}={value:<6} " 
            print(line)
        print("-" * 51)
        print(f"PC = 0x{self.pc:08X}")
        print("-" * 51)

    def update_pc(self, value):
        """Aktualizace program counteru (posun na dalsi instrukci)"""
        self.pc = value

    def get_reg(self, index):
        """
        Cteni z registru.
        Registr x0 je v RISC-V vzdy 'hardwired' na nulu (pro lehci kopirovani hodnot napr)
        """
        if index == 0: 
            return 0
        return self.regs[index]

    def set_reg(self, index, value):
        """
        Zapis do registru.
        Zapis do x0 je ignorovan. Hodnota je orezana na 32 bitu.
        """
        if index == 0: 
            return
        self.regs[index] = value & MASK_32_BIT

    def fetch(self):
        """FETCH: Nacteni 32-bitove instrukce z pameti na adrese PC"""
        if self.pc >= self.memory.size:
            return None
        return self.memory.read_32(self.pc)

    def decode_and_execute(self, instruction):
        """
        DECODE & EXECUTE: Rozkodovani instrukce a provedeni operace.
        """
        if instruction is None or instruction == 0: 
            return False

        # dekodovani
        opcode = instruction & MASK_OPCODE        
        rd     = (instruction >> 7) & MASK_REG
        funct3 = (instruction >> 12) & MASK_FUNCT3
        rs1    = (instruction >> 15) & MASK_REG
        rs2    = (instruction >> 20) & MASK_REG
        funct7 = (instruction >> 25) & MASK_FUNCT7
        
        print(f"\n[FETCH]  Adresa: 0x{self.pc:04X} | Instrukce: 0x{instruction:08X}")

        # dekodovani konstant - immediates
        # 1. I-Type Immediate (12 bitu - 20-31) pro aritmetiku
        imm_i = (instruction >> 20)
        if imm_i & SIGN_BIT_12: 
            imm_i -= SIGN_EXT_12 

        # 2. S-Type Immediate (12 bitu - hornich 7 a spodnich 5, spojime je) pro ukladani do pameti
        imm_s = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
        if imm_s & SIGN_BIT_12: 
            imm_s -= SIGN_EXT_12

        # 3. B-Type Immediate (13 bitu) pro podminene skoky
        imm_b = ((instruction >> 31) << 12) | (((instruction >> 7) & 0x01) << 11) | (((instruction >> 25) & 0x3F) << 5) | (((instruction >> 8) & 0x0F) << 1)
        if imm_b & SIGN_BIT_13: 
            imm_b -= SIGN_EXT_13

        # vykonani - execution

        # instrukce ADDI - pricti konstantu k registru
        if opcode == OPCODE_ALU_I and funct3 == F3_ADD_SUB_BEQ:
            value_1 = self.get_reg(rs1)
            result = value_1 + imm_i
            print(f"[EXEC]   ADDI: x{rd} = x{rs1}({value_1}) + imm({imm_i})")
            print(f"[WRITE]  Ukladani hodnoty {result} do registru x{rd}")
            self.set_reg(rd, result)
            self.update_pc(self.pc + WORD_SIZE)
            return True
        
        # instrukce ANDI - bitovy and s konstantou
        if opcode == OPCODE_ALU_I and funct3 == F3_AND:
             value_1 = self.get_reg(rs1)
             result = value_1 & imm_i
             print(f"[EXEC]   ANDI: x{rd} = x{rs1}({value_1}) & imm({imm_i})")
             print(f"[WRITE]  Ukladani hodnoty {result} do registru x{rd}")
             self.set_reg(rd, result)
             self.update_pc(self.pc + WORD_SIZE)
             return True

        # instrukce ADD - secte dva registy
        if opcode == OPCODE_ALU_R and funct3 == F3_ADD_SUB_BEQ and funct7 == F7_DEFAULT:
             value_1 = self.get_reg(rs1)
             value_2 = self.get_reg(rs2)
             result = value_1 + value_2
             print(f"[EXEC]   ADD: x{rd} = x{rs1}({value_1}) + x{rs2}({value_2})")
             print(f"[WRITE]  Ukladani hodnoty {result} do registru x{rd}")
             self.set_reg(rd, result)
             self.update_pc(self.pc + WORD_SIZE)
             return True

        # instrukce SUB - odecte dva registry
        if opcode == OPCODE_ALU_R and funct3 == F3_ADD_SUB_BEQ and funct7 == F7_SUB:
             value_1 = self.get_reg(rs1)
             value_2 = self.get_reg(rs2)
             result = value_1 - value_2
             print(f"[EXEC]   SUB: x{rd} = x{rs1}({value_1}) - x{rs2}({value_2})")
             print(f"[WRITE]  Ukladani hodnoty {result} do registru x{rd}")
             self.set_reg(rd, result)
             self.update_pc(self.pc + WORD_SIZE)
             return True

        # logicke operace (AND, OR, XOR)
        if opcode == OPCODE_ALU_R:
            value_1 = self.get_reg(rs1)
            value_2 = self.get_reg(rs2)
            if funct3 == F3_AND and funct7 == F7_DEFAULT: # AND
                result = value_1 & value_2
                print(f"[EXEC]   AND: x{rd} = x{rs1}({value_1}) & x{rs2}({value_2})")
                self.set_reg(rd, result)
            elif funct3 == F3_OR and funct7 == F7_DEFAULT: # OR
                result = value_1 | value_2
                print(f"[EXEC]   OR: x{rd} = x{rs1}({value_1}) | x{rs2}({value_2})")
                self.set_reg(rd, result)
            elif funct3 == F3_XOR and funct7 == F7_DEFAULT: # XOR
                result = value_1 ^ value_2
                print(f"[EXEC]   XOR: x{rd} = x{rs1}({value_1}) ^ x{rs2}({value_2})")
                self.set_reg(rd, result)
            else:
                 pass # neznama instrukce
            
            if opcode == OPCODE_ALU_R: # spolecny zapis pro logiku
                print(f"[WRITE]  Ukladani hodnoty {result} do registru x{rd}")
                self.update_pc(self.pc + WORD_SIZE)
                return True

        # instrukce LW - nacte cislo z pameti
        if opcode == OPCODE_LOAD and funct3 == F3_MEM:
            base = self.get_reg(rs1)
            addr = base + imm_i
            value = self.memory.read_32(addr)
            print(f"[EXEC]   LW: x{rd} = Pamet[x{rs1}({base}) + {imm_i}] (Adresa: 0x{addr:X})")
            print(f"[READ]   Nactena hodnota {value} z pameti do x{rd}")
            self.set_reg(rd, value)
            self.update_pc(self.pc + WORD_SIZE)
            return True

        # instrukce SW - uloz cislo z registru do pameti
        if opcode == OPCODE_STORE and funct3 == F3_MEM:
            base = self.get_reg(rs1)
            value_to_store = self.get_reg(rs2)
            addr = base + imm_s
            print(f"[EXEC]   SW: Pamet[x{rs1}({base}) + {imm_s}] (Adresa: 0x{addr:X}) = x{rs2}({value_to_store})")
            print(f"[WRITE]  Zapisovani hodnoty {value_to_store} do pameti")
            self.memory.write_32(addr, value_to_store)
            self.update_pc(self.pc + WORD_SIZE)
            return True

        # instrukce BEQ - pokud jsou dva registry stejne, skocime na jinou adresu, jinak pokracujeme
        if opcode == OPCODE_BRANCH and funct3 == F3_ADD_SUB_BEQ:
             value_1 = self.get_reg(rs1)
             value_2 = self.get_reg(rs2)
             print(f"[EXEC]   BEQ: Porovnavani x{rs1}({value_1}) == x{rs2}({value_2})")
             if value_1 == value_2:
                 print(f"[JUMP]   Podminka splnena. Skacu na relativni offset {imm_b}")
                 self.update_pc(self.pc + imm_b)
             else:
                 print(f"[NEXT]   Podminka nesplnena. Pokracuji na dalsi instrukci.")
                 self.update_pc(self.pc + WORD_SIZE)
             return True

        # instrukce BNE - opak BEQ, skoci kdyz jsou registry ruzne
        if opcode == OPCODE_BRANCH and funct3 == F3_BNE:
             value_1 = self.get_reg(rs1)
             value_2 = self.get_reg(rs2)
             print(f"[EXEC]   BNE: Porovnavani x{rs1}({value_1}) != x{rs2}({value_2})")
             if value_1 != value_2:
                 print(f"[JUMP]   Podminka splnena. Skacu na relativni offset {imm_b}")
                 self.update_pc(self.pc + imm_b)
             else:
                 print(f"[NEXT]   Podminka nesplnena. Pokracuji na dalsi instrukci.")
                 self.update_pc(self.pc + WORD_SIZE)
             return True

        print(f"Neznama instrukce: 0x{instruction:X} na adrese {self.pc}")
        return False

    def step(self):
        """Provedeni jednoho taktu procesoru (Fetch -> Decode -> Execute)"""
        inst = self.fetch()
        return self.decode_and_execute(inst)

    def run(self):
        """Spusteni programu s limitem cyklu (ochrana proti nekonecne smycce)"""
        limit = 500
        while self.step() and limit > 0:
            limit -= 1

# ==========================================
# CAST 3: UNIT TESTY
# ==========================================

# --- KONSTANTY PRO TESTY ---
TEST_MEM_VALUE = 0x12345678
TEST_ADD_REG = 3
TEST_ADD_EXPECTED = 30
TEST_BEQ_REG = 4
TEST_BEQ_EXPECTED = 1
# ---------------------------

class TestEmulator(unittest.TestCase):
    """Sada testu overujici spravnost emulace"""
    
    def test_memory(self):
        """Test zapisu a cteni z pameti (Endianita)"""
        ram = Memory()
        ram.write_32(0, TEST_MEM_VALUE)
        self.assertEqual(ram.read_32(0), TEST_MEM_VALUE)

    def test_cpu_ops(self):
        """Test zakladnich aritmetickych operaci (ADD, ADDI)"""
        ram = Memory()
        cpu = CPU(ram)
        # program: ADDI x1, x0, 10; ADDI x2, x0, 20; ADD x3, x1, x2
        program = [0x00A00093, 0x01400113, 0x002081B3]
        ram.load_program(program)
        cpu.run()
        self.assertEqual(cpu.get_reg(TEST_ADD_REG), TEST_ADD_EXPECTED)

    def test_branching(self):
        """Test podminenych skoku (BEQ)"""
        ram = Memory()
        cpu = CPU(ram)
        # program testuje preskoceni instrukce pomoci BEQ
        program = [
            0x00500093, 0x00500113, 0x00208463, 0x06300193, 0x00100213 # (x1 = 5, x2 = 5, if x1 == x2 skocime o 8 bytu dopredu, preskoci se, x4 = 1)
        ]
        ram.load_program(program)
        cpu.run()
        self.assertEqual(cpu.get_reg(TEST_BEQ_REG), TEST_BEQ_EXPECTED)

# ==========================================
# CAST 4: HLAVNI PROGRAM (INTERAKTIVNI MENU)
# ==========================================

# --- KONSTANTY PRO KALKULACKU A FORMATOVANI ---
MAX_INT_32 = 0x7FFFFFFF          # Maximalni kladne 32-bitove cislo
SIGN_EXT_32 = 0x100000000        # Odecteni 2^32 pro zaporna cisla

INST_ADD_X3_X1_X2 = 0x002081B3   # Strojovy kod pro ADD x3, x1, x2
INST_SUB_X3_X1_X2 = 0x402081B3   # Strojovy kod pro SUB x3, x1, x2
INST_AND_X3_X1_X2 = 0x0020F1B3   # Strojovy kod pro AND x3, x1, x2
INST_OR_X3_X1_X2  = 0x0020E1B3   # Strojovy kod pro OR x3, x1, x2
# ----------------------------------------------

def run_fibonacci_demo():
    """
    Demonstracni program: Vypocet n-teho Fibonacciho cisla.
    Ukazuje pouziti cyklu, skoku a prace s pameti.
    """
    print("\n--- DEMO: FIBONACCIHO POSLOUPNOST ---")
    ram = Memory()
    cpu = CPU(ram)
    
    # program pocita 7. cislo (n=7).
    program = [
        0x00000093, 0x00100113, 0x00700193, 0x00000213, # 0x00000093 - 1001 0011 - opcode = ADDI, rd = 1, funct3 = 0, rs1 = 0, immediate = 0
        0x00418C63, 0x002082B3, 0x00010093, 0x00028113, 
        0x00120213, 0xFE0006E3, 0x00102023, 
    ]
    
    print("Nahrava se strojovy kod do pameti")
    ram.load_program(program)
    
    print("Spoustim CPU...")
    cpu.run()
    
    print(f"\n[FINAL] Vysledek (7. cislo) v registru x1: {cpu.get_reg(1)}")
    print(f"[FINAL] Vysledek ulozeny v pameti RAM[0]: {ram.read_32(0)}")
    print("-------------------------------------\n\n")

    print_operations()

def to_signed(value):
    if value > MAX_INT_32:
        return value - SIGN_EXT_32

    return value

def get_num():
    line = stdin.readline()
    if not line:
        return -1
    
    num = 0
    ascii_zero = ord('0')
    found_digit = False
    
    for symbol in line:
        if '0' <= symbol <= '9':
            found_digit = True
            num = num * 10 + (ord(symbol) - ascii_zero)
        elif found_digit:
            break
    
    if found_digit:
        return num

    return -1

def print_operations():
    print("\nVyberte operaci:")
    print(f"1: Scitani (ADD)\n2: Odcitani (SUB)\n3: AND\n4: OR\n5: Fibonacci\n6: Testy\n0: Konec\n")

def interactive_emulator():
    """Hlavni smycka programu - textove uzivatelske rozhrani"""
    print("\n" + "="*40)
    print("RISC-V EMULATOR")
    print("="*40)

    print_operations()

    while True:
        print("Vase volba: ", end = "", flush = True)
        choice = get_num()
        
        if choice == 0:
            print("Ukoncuji emulator.")
            break
            
        if choice == 6:
            print("\nSpoustim testy...")
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestEmulator)
            unittest.TextTestRunner(verbosity=2).run(suite)
            continue

        if choice == 5:
            run_fibonacci_demo()
            continue

        if choice in [1, 2, 3, 4]:
            value_a = -1
            while value_a == -1:
                print("Zadejte prvni cislo (A): ", end = "", flush = True)
                value_a = get_num()

            value_b = -1
            while value_b == -1:
                print("Zadejte prvni cislo (B): ", end = "", flush = True)
                value_b = get_num()

            ram = Memory()
            cpu = CPU(ram)
            cpu.regs[1] = value_a
            cpu.regs[2] = value_b
            
            instruction = 0
            op_sym = ""
            if choice == 1: 
                instruction = INST_ADD_X3_X1_X2
                op_sym = "+"
            elif choice == 2: 
                instruction = INST_SUB_X3_X1_X2
                op_sym = "-"
            elif choice == 3: 
                instruction = INST_AND_X3_X1_X2
                op_sym = "&"
            elif choice == 4: 
                instruction = INST_OR_X3_X1_X2
                op_sym = "|"


            print(f"\n\n\n--- START VYPOCETNIHO CYKLU ---")
            ram.write_32(0, instruction)
            cpu.step()
            result = cpu.get_reg(3)
            print(f"\n  --- KONEC VYPOCETNIHO CYKLU ---\n")
            
            print(f"Vysledek: {value_a} {op_sym} {value_b} = {to_signed(result)}")

            print("\n")
            print_operations()
                
            #cpu.dump_registers()

if __name__ == '__main__':
    interactive_emulator()