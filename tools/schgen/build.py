"""Generate KiCad 7 schematic for the LM2596 based lab power supply."""
import math, uuid, sys, os, json
from sexp import *

PROJECT = 'buckbench'
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else '../../hardware'
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'buckbench_root'))
POWER_NETS = {'GND': 'GND', '+5V': '+5V', '+3V3': '+3V3'}
_u = [0]
def U():
    _u[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f'buckbench_{_u[0]}'))

def fnt(size=1.27, bold=False):
    f = [Sym('font'), [Sym('size'), size, size]]
    if bold: f.append(Sym('bold'))
    return f

# ---------------------------------------------------------------- custom symbols
def custom_box(name, left, right, width, title=None, top=None, bottom=None, ref='A'):
    """left/right: list of (number, name, etype) or None for a gap. Returns symbol def."""
    n = max(len(left), len(right))
    h = (n + 1) * 2.54
    y0 = (n - 1) * 2.54 / 2
    # snap y0 to 1.27 grid
    y0 = round(y0 / 1.27) * 1.27
    hw = width / 2
    top_y = y0 + 2.54
    bot_y = y0 - (n - 1) * 2.54 - 2.54
    gfx = [Sym('symbol'), f'{name}_0_1',
           [Sym('rectangle'), [Sym('start'), -hw, top_y], [Sym('end'), hw, bot_y],
            [Sym('stroke'), [Sym('width'), 0.254], [Sym('type'), Sym('default')]],
            [Sym('fill'), [Sym('type'), Sym('background')]]]]
    pins = [Sym('symbol'), f'{name}_1_1']
    def pin(num, pname, et, x, y, ang):
        pins.append([Sym('pin'), Sym(et), Sym('line'), [Sym('at'), x, y, ang], [Sym('length'), 2.54],
                     [Sym('name'), pname, [Sym('effects'), fnt()]],
                     [Sym('number'), num, [Sym('effects'), fnt()]]])
    for i, p in enumerate(left):
        if p: pin(p[0], p[1], p[2], -hw - 2.54, y0 - i * 2.54, 0)
    for i, p in enumerate(right):
        if p: pin(p[0], p[1], p[2], hw + 2.54, y0 - i * 2.54, 180)
    sym = [Sym('symbol'), f'Lab:{name}', [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
           [Sym('property'), 'Reference', ref, [Sym('at'), -hw, top_y + 1.27, 0], [Sym('effects'), fnt(), [Sym('justify'), Sym('left')]]],
           [Sym('property'), 'Value', name, [Sym('at'), -hw, bot_y - 1.27, 0], [Sym('effects'), fnt(), [Sym('justify'), Sym('left')]]],
           [Sym('property'), 'Footprint', '', [Sym('at'), 0, 0, 0], [Sym('effects'), fnt(), Sym('hide')]],
           [Sym('property'), 'Datasheet', '', [Sym('at'), 0, 0, 0], [Sym('effects'), fnt(), Sym('hide')]],
           gfx, pins]
    return sym

CUSTOM = {}
CUSTOM['LM2596_modul'] = custom_box('LM2596_modul',
    [('1', 'IN+', 'power_in'), ('2', 'IN-', 'power_in'), None, ('5', 'ON/OFF (pin5)', 'input')],
    [('3', 'OUT+', 'power_out'), ('4', 'OUT-', 'passive'), None, ('6', 'FB (pin4)', 'input')], 30.48)
CUSTOM['MP1584_modul'] = custom_box('MP1584_modul',
    [('1', 'IN+', 'power_in'), ('2', 'IN-', 'power_in')],
    [('3', 'OUT+', 'power_out'), ('4', 'OUT-', 'passive')], 20.32)
BP_L = ['B12', 'B13', 'B14', 'B15', 'A8', 'A9', 'A10', 'A11', 'A12', 'A15', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', '5V', 'G', '3.3']
BP_R = ['VB', 'C13', 'C14', 'C15', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'B0', 'B1', 'B10', 'B11', 'R', '3.3', 'G', 'G']
def bp_type(n):
    return {'5V': 'power_in', 'G': 'power_in', '3.3': 'power_out'}.get(n, 'bidirectional')
def bp_name(n):
    if n[0] in 'AB' and n[1:].isdigit(): return 'P' + n
    if n == 'C13' or n == 'C14' or n == 'C15': return 'P' + n
    return {'G': 'GND', '3.3': '3V3', 'R': 'RESET', 'VB': 'VBAT'}.get(n, n)
CUSTOM['BluePill_STM32F103C8'] = custom_box('BluePill_STM32F103C8',
    [(f'L{i+1}', bp_name(n), bp_type(n)) for i, n in enumerate(BP_L)],
    [(f'R{i+1}', bp_name(n), bp_type(n)) for i, n in enumerate(BP_R)], 20.32)
for k in CUSTOM:
    CUSTOM[k][1] = f'Lab:{k}'

def symdef(lib_id):
    lib, name = lib_id.split(':')
    if lib == 'Lab':
        return CUSTOM[name]
    return get_symbol(lib, name)

# ---------------------------------------------------------------- schematic builder
class Sch:
    def __init__(self):
        self.items = []
        self.libs = {}
        self.pwr_n = 0
        self.netpins = {}

    def _xf(self, x0, y0, rot, px, py):
        a = math.radians(rot)
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        return round(x0 + rx, 3), round(y0 - ry, 3)

    def place(self, lib_id, ref, value, x, y, rot=0, unit=1, nets=None, stub=None, hide_ref=False,
              props_at=None, mirror=None, connect=True):
        sd = symdef(lib_id)
        self.libs[lib_id] = sd
        sym = [Sym('symbol'), [Sym('lib_id'), lib_id], [Sym('at'), x, y, rot]]
        sym += [[Sym('unit'), unit], [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
                [Sym('dnp'), Sym('no')], [Sym('uuid'), U()]]
        for p in find(sd, 'property'):
            name = p[1]
            if name.startswith('ki_'):
                continue
            at = find1(p, 'at')
            px, py = self._xf(x, y, rot, float(at[1]), float(at[2]))
            pa = float(at[3]) if len(at) > 3 else 0
            eff = copy.deepcopy(find1(p, 'effects'))
            if props_at and name in props_at:
                pp = props_at[name]
                px, py = pp[0] + x, pp[1] + y
                pa = 90 if rot in (90, 270) else 0
                sw = {'left': 'right', 'right': 'left'} if rot in (90, 270) else {}
                j = [Sym('justify')] + [Sym(sw.get(t, t)) for t in (pp[2] if len(pp) > 2 else 'left').split() if t != 'center']
                eff = [Sym('effects'), fnt()] + ([j] if len(j) > 1 else [])
            elif rot in (90, 270) and pa in (90, 270):
                pa = 0
            elif rot in (90, 270):
                pa = 90 if pa == 0 else 0
            text = {'Reference': ref, 'Value': value}.get(name, p[2])
            if name == 'Reference' and hide_ref and Sym('hide') not in eff:
                eff.append(Sym('hide'))
            sym.append([Sym('property'), name, text, [Sym('at'), px, py, pa], eff])
        for pin in symbol_pins(sd, unit):
            sym.append([Sym('pin'), pin['number'], [Sym('uuid'), U()]])
        sym.append([Sym('instances'), [Sym('project'), PROJECT,
                    [Sym('path'), '/' + ROOT_UUID, [Sym('reference'), ref], [Sym('unit'), unit]]]])
        self.items.append(sym)
        if not connect:
            return sym
        stub = stub or 2.54
        # connections
        nets = nets or {}
        pins = symbol_pins(sd, unit)
        keys = {p['number'] for p in pins} | {p['name'] for p in pins}
        for k in nets:
            assert k in keys, (ref, k, keys)
        for pin in pins:
            net = nets.get(pin['number'], nets.get(pin['name'], '__missing__'))
            assert net != '__missing__', (ref, pin['number'], pin['name'])
            cx, cy = self._xf(x, y, rot, pin['x'], pin['y'])
            if net is None:
                self.items.append([Sym('no_connect'), [Sym('at'), cx, cy], [Sym('uuid'), U()]])
                continue
            direct = net.startswith('=')
            net = net.lstrip('=')
            self.netpins.setdefault(net, []).append(f'{ref}.{pin["number"]}')
            if direct:
                continue
            ang = math.radians(pin['angle'] + rot)
            ox, oy = -round(math.cos(ang)), round(math.sin(ang))  # outward, screen coords
            sx, sy = round(cx + ox * stub, 3), round(cy + oy * stub, 3)
            self.wire(cx, cy, sx, sy)
            self.netlabel(net, sx, sy, ox, oy)
        return sym

    def wire(self, x1, y1, x2, y2):
        self.items.append([Sym('wire'), [Sym('pts'), [Sym('xy'), x1, y1], [Sym('xy'), x2, y2]],
                           [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]], [Sym('uuid'), U()]])

    def netlabel(self, net, x, y, ox, oy):
        if net in POWER_NETS:
            self.pwr_n += 1
            gnd = net == 'GND'
            # body direction = outward
            if gnd:
                rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(ox, oy)]
            else:
                rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(ox, oy)]
            self.place('power:' + POWER_NETS[net], f'#PWR{self.pwr_n:03d}', net, x, y, rot, nets={}, connect=False)
            return
        ang = 180 if ox < 0 else 0
        just = [Sym('justify'), Sym('right' if ang == 180 else 'left'), Sym('bottom')]
        self.items.append([Sym('label'), net, [Sym('at'), x, y, ang], [Sym('fields_autoplaced')],
                           [Sym('effects'), fnt(), just], [Sym('uuid'), U()]])

    def text(self, s, x, y, size=1.5, bold=False):
        self.items.append([Sym('text'), s, [Sym('exclude_from_sim'), Sym('no')] if False else [Sym('at'), x, y, 0],
                           [Sym('effects'), fnt(size, bold), [Sym('justify'), Sym('left'), Sym('top')]], [Sym('uuid'), U()]])

    def frame(self, x1, y1, x2, y2, title):
        self.items.append([Sym('rectangle'), [Sym('start'), x1, y1], [Sym('end'), x2, y2],
                           [Sym('stroke'), [Sym('width'), 0.3], [Sym('type'), Sym('dash')]],
                           [Sym('fill'), [Sym('type'), Sym('none')]], [Sym('uuid'), U()]])
        self.items.append([Sym('text'), title, [Sym('at'), x1 + 2, y1 + 2, 0],
                           [Sym('effects'), fnt(2.0, True), [Sym('justify'), Sym('left'), Sym('top')]], [Sym('uuid'), U()]])

    def save(self, path, title_block):
        doc = [Sym('kicad_sch'), [Sym('version'), 20230121], [Sym('generator'), Sym('eeschema')],
               [Sym('uuid'), ROOT_UUID], [Sym('paper'), 'A3'], title_block,
               [Sym('lib_symbols')] + list(self.libs.values())]
        doc += self.items
        doc.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
        open(path, 'w').write(dump(doc) + '\n')

# ---------------------------------------------------------------- the design
S = Sch()
R, C, CP = 'Device:R', 'Device:C', 'Device:C_Polarized'
H = 90  # horizontal two-pin part (pin1 left)
V = 0   # vertical (pin1 top)
PH = {'Reference': (-0.4, -1.8, 'right'), 'Value': (0.4, -1.8, 'left')}
PV = {'Reference': (2.0, -0.8, 'left'), 'Value': (2.0, 1.9, 'left')}
def r(ref, val, x, y, n1, n2, rot=V):
    S.place(R, ref, val, x, y, rot, nets={'1': n1, '2': n2}, props_at=PH if rot == H else PV)
def c(ref, val, x, y, n1, n2, rot=V, lib=C):
    S.place(lib, ref, val, x, y, rot, nets={'1': n1, '2': n2}, props_at=PH if rot == H else {'Reference': (2.5, -0.8, 'left'), 'Value': (2.5, 1.9, 'left')})


# ===== A: power path
S.frame(15, 16, 200, 98, 'A  Výkonová část – modul LM2596')
S.place('Connector:Screw_Terminal_01x02', 'J1', 'VSTUP 24 V DC', 28, 45, 180,
        nets={'1': 'VIN_RAW', '2': 'GND'}, props_at={'Reference': (-2, -6), 'Value': (-4, 5)})
S.place('Device:Fuse', 'F1', 'T 3 A', 50, 40, H, nets={'1': 'VIN_RAW', '2': 'VIN_F'}, props_at=PH)
S.place('Device:D_TVS', 'D7', 'SMBJ24CA', 62, 60, 90, nets={'A1': 'VIN_F', 'A2': 'GND'},
        props_at={'Reference': (2.5, -0.8), 'Value': (2.5, 1.9)})
S.place('Device:D_Schottky', 'D8', 'SS54 (přepólování)', 78, 40, 180, nets={'A': 'VIN_F', 'K': 'VIN_P'},
        props_at={'Reference': (0, -2.5), 'Value': (0, 3.5, 'top')})
S.place('Switch:SW_SPST', 'SW1', 'SÍŤOVÝ VYPÍNAČ', 106, 40, 0, nets={'1': 'VIN_P', '2': 'VIN'})
S.place('Lab:LM2596_modul', 'A1', 'LM2596S_modul (W103 a spodní R odstranit)', 148, 54, 0,
        nets={'1': 'VIN', '2': 'GND', '3': 'VOUT', '4': 'GND', '5': 'EN', '6': 'FB'})
c('C1', '470µF/35V', 110, 80, 'VIN', 'GND', lib=CP)
PP = {'Reference': (-0.4, 3.0, 'right top'), 'Value': (0.4, 3.0, 'left top')}
S.place('Device:R_Potentiometer', 'RV1', '10k lin – U hrubě', 152, 26, H,
        nets={'1': 'VOUT', '2': 'RV_MID', '3': 'RV_MID'}, props_at=PP)
S.place('Device:R_Potentiometer', 'RV2', '500R lin – U jemně', 182, 26, H,
        nets={'1': 'RV_MID', '2': 'FB', '3': 'FB'}, props_at=PP)
r('R1', '0R1 1W bočník', 158, 82, 'OUT_NEG', 'GND')
S.place('Connector:Screw_Terminal_01x02', 'J2', 'VÝSTUP', 192, 64, 0,
        nets={'1': 'VOUT', '2': 'OUT_NEG'}, props_at={'Reference': (-1, -3.5), 'Value': (-1, 4)})
r('R17', '680R 1%', 190, 44, 'FB', 'GND')
S.place('Device:D_Schottky', 'D9', 'SS54', 176, 82, 270, nets={'K': 'VOUT', 'A': 'OUT_NEG'},
        props_at={'Reference': (2.5, -0.8, 'right'), 'Value': (2.5, 1.9, 'right')})
r('R2', '100k 1%', 30, 78, 'VOUT', 'U_SENSE')
r('R3', '10k 1%', 52, 85, 'U_SENSE', 'GND')
c('C2', '100nF', 72, 85, 'U_SENSE', 'GND')

# ===== B: 5V supply + output enable
S.frame(205, 16, 300, 98, 'B  Napájení 5 V a vypínání výstupu')
S.place('Lab:MP1584_modul', 'A2', 'MP1584_modul (5 V)', 252, 38, 0,
        nets={'1': 'VIN', '2': 'GND', '3': '+5V', '4': 'GND'})
r('R4', '10k', 222, 72, '+5V', 'EN')
S.place('Transistor_BJT:BC547', 'Q5', 'BC547', 265, 76, 0, nets={'C': 'EN', 'B': 'Q5_B', 'E': 'GND'})
r('R5', '10k', 240, 86, 'OUT_EN', 'Q5_B', H)
r('R6', '100k', 288, 80, 'Q5_B', 'GND')

# ===== C: current sensing and limiting
S.frame(15, 102, 200, 198, 'C  Měření a omezení proudu (LM358)')
r('R7', '1k', 28, 125, 'OUT_NEG', 'ISH_F', H)
c('C3', '100nF', 42, 135, 'ISH_F', 'GND')
S.place('Amplifier_Operational:LM358', 'U1', 'LM358', 68, 128, 0, unit=1,
        nets={'+': 'ISH_F', '-': 'U1A_N', '1': 'I_AMP'})
r('R8', '10k', 70, 145, 'U1A_N', 'I_AMP', H)
r('R9', '1k', 50, 152, 'U1A_N', 'GND')
r('R10', '1k', 100, 120, 'I_AMP', 'I_MEAS', H)
c('C4', '100nF', 115, 132, 'I_MEAS', 'GND')
S.place('Device:D_Schottky', 'D1', 'BAT54', 135, 120, 0, nets={'A': 'I_MEAS', 'K': '+3V3'})
S.place('Amplifier_Operational:LM358', 'U1', 'LM358', 118, 160, 0, unit=2,
        nets={'+': 'I_AMP', '-': 'U1B_N', '7': 'CC_OUT'})
r('R11', '10k', 80, 162.54, 'I_SET', 'U1B_N', H)
c('C5', '100nF', 118, 176, 'U1B_N', 'CC_OUT', H)
r('R12', '470R', 150, 150, 'CC_OUT', 'CC_D', H)
S.place('Device:D_Schottky', 'D2', '1N5819', 175, 150, 0, nets={'A': 'CC_D', 'K': 'FB'})
r('R13', '10k', 150, 168, 'CC_OUT', 'CC_SENSE', H)
r('R14', '10k', 178, 176, 'CC_SENSE', 'GND')
r('R15', '10k', 30, 180, 'I_SET_PWM', 'ISF1', H)
c('C6', '1µF', 44, 184, 'ISF1', 'GND')
r('R16', '10k', 60, 180, 'ISF1', 'I_SET', H)
c('C7', '1µF', 74, 184, 'I_SET', 'GND')
S.place('Amplifier_Operational:LM358', 'U1', 'LM358', 192, 122, 0, unit=3, nets={'V+': '+5V', 'V-': 'GND'})
c('C8', '100nF', 178, 122, '+5V', 'GND')

# ===== D: Blue Pill
S.frame(205, 102, 300, 198, 'D  Řídicí jednotka – Blue Pill')
bp_nets = {
    'PB12': 'SEG_E', 'PB13': 'SEG_F', 'PB14': 'SEG_G', 'PB15': 'SEG_DP', 'PA8': 'I_SET_PWM',
    'PA9': 'LED_OUT', 'PA10': 'LED_CC', 'PA12': None, 'PA15': None, 'PB3': None, 'PB4': None,
    'PB5': 'BTN_MODE', 'PB6': 'BTN_OUT', 'PB7': 'LED_A', 'PB8': 'SEG_A', 'PB9': 'SEG_B',
    'VBAT': None, 'PC13': None, 'PC14': None, 'PC15': None, 'PA0': 'U_SENSE', 'PA1': 'I_MEAS',
    'PA2': 'CC_SENSE', 'PA3': 'OUT_EN', 'PA4': 'DIG1', 'PA5': 'DIG2', 'PA6': 'DIG3', 'PA7': 'DIG4',
    'PB0': 'ISET_POT', 'PB1': 'NTC', 'PA11': 'LED_V', 'PB10': 'SEG_C', 'PB11': 'SEG_D', 'RESET': None,
}
nets = {}
for side, lst in (('L', BP_L), ('R', BP_R)):
    for i, n in enumerate(lst):
        nets[f'{side}{i+1}'] = {'5V': '+5V', 'G': 'GND', '3.3': '+3V3'}.get(n, bp_nets.get(bp_name(n)))
S.place('Lab:BluePill_STM32F103C8', 'A3', 'Blue Pill (STM32F103C8T6)', 252, 150, 0, nets=nets, stub=5.08)

# ===== E: display
S.frame(15, 202, 200, 280, 'E  Displej 4×7 seg. (společná katoda, multiplex)')
S.place('Display_Character:CC56-12EWA', 'DS1', '4 místa, spol. katoda (např. 5641AS)', 92, 240, 0,
        nets={'a': 'DS_A', 'b': 'DS_B', 'c': 'DS_C', 'd': 'DS_D', 'e': 'DS_E', 'f': 'DS_F', 'g': 'DS_G',
              'DPX': 'DS_DP', 'CC1': 'K1', 'CC2': 'K2', 'CC3': 'K3', 'CC4': 'K4'})
for i, sg in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'DP']):
    r(f'R{20+i}', '100R', 38, 218 + i * 6, f'SEG_{sg}', f'DS_{sg}', H)
for i in range(4):
    x = 150 + (i % 2) * 32
    y = 228 + (i // 2) * 30
    S.place('Transistor_BJT:BC337', f'Q{i+1}', 'BC337', x, y, 0, nets={'C': f'K{i+1}', 'B': f'=Q{i+1}_B', 'E': 'GND'})
    r(f'R{30+i}', '470R', x - 5.08 - 3.81, y, f'DIG{i+1}', f'=Q{i+1}_B', H)

# ===== F: user interface
S.frame(305, 16, 405, 152, 'F  Ovládání a indikace')
S.place('Device:R_Potentiometer', 'RV3', '10k lin – limit I', 325, 42, 0,
        nets={'1': '+3V3', '2': 'ISET_POT', '3': 'GND'},
        props_at={'Reference': (-2.5, -0.8, 'right'), 'Value': (-2.5, 1.9, 'right')})
c('C9', '100nF', 350, 50, 'ISET_POT', 'GND')
r('R18', '10k 1%', 384, 36, '+3V3', 'NTC')
S.place('Device:Thermistor_NTC', 'RT1', 'NTC 10k (chladič)', 384, 58, 0, nets={'1': 'NTC', '2': 'GND'},
        props_at={'Reference': (2.5, -0.8), 'Value': (2.5, 1.9)})
c('C10', '100nF', 368, 58, 'NTC', 'GND')
S.place('Switch:SW_Push', 'SW2', 'U/I (MODE)', 335, 72, 0, nets={'1': 'BTN_MODE', '2': 'GND'})
S.place('Switch:SW_Push', 'SW3', 'VÝSTUP ON/OFF', 335, 86, 0, nets={'1': 'BTN_OUT', '2': 'GND'})
leds = [('LED_V', 'zelená – zobrazeno U'), ('LED_A', 'žlutá – zobrazeno I'),
        ('LED_CC', 'červená – omezení proudu'), ('LED_OUT', 'modrá – výstup zapnut')]
for i, (n, v) in enumerate(leds):
    y = 104 + i * 12
    r(f'R{40+i}', '1k', 325, y, n, f'{n}_A', H)
    S.place('Device:LED', f'D{3+i}', v, 362, y, 180, nets={'A': f'{n}_A', 'K': 'GND'},
            props_at={'Reference': (0, -2.2, 'center'), 'Value': (0, 2.2, 'center top')})

# ===== notes
S.text(
    "ÚPRAVY MODULU LM2596S\n"
    "1) Vypájet trimr W103 a spodní rezistor děliče (FB–GND). Nově:\n"
    "   R17 680R (FB–GND), RV1+RV2 reostaty mezi OUT+ a FB:\n"
    "   U = 1,23 × (1 + R_RV/680) → 1,23 až ~20,2 V.\n"
    "   Běžec spojen s krajem – FB nikdy nezůstane ve vzduchu.\n"
    "2) Pin 5 (ON/OFF) odříznout od GND. > 1,3 V = výstup vypnut.\n"
    "   R4 drží výstup vypnutý, STM32 ho zapíná přes Q5 (PA3 = 1).\n"
    "3) OUT- modulu = GND. Bočník R1 je mezi GND a zdířkou '-',\n"
    "   zdířka '-' NENÍ zem (pozor na uzemněný osciloskop).\n"
    "4) D2 připájet přímo na pin 4 (FB) LM2596.\n"
    "\n"
    "OCHRANY\n"
    "Vstup: F1 pojistka, D8 přepólování, D7 TVS přepětí.\n"
    "Výstup zkrat: CC smyčka (U1B) + vnitřní limit LM2596 (~3 A);\n"
    "   FW při trvalém zkratu výstup vypne (Q5).\n"
    "D9: ochrana proti zpětnému/opačnému napětí na výstupu.\n"
    "Přehřátí: NTC RT1 na chladiči → PB1, FW vypne nad ~85 °C;\n"
    "   záloha: tepelná ochrana uvnitř LM2596.",
    207, 204, 1.27)
S.text(
    "MĚŘÍTKA PRO FIRMWARE\n"
    "U_SENSE = VOUT × 10/110 → PA0 (36 V = 3,27 V)\n"
    "I_AMP = I × 0,1 Ω × 11 = 1,1 V/A → PA1\n"
    "Limit I: PWM PA8 (TIM1_CH1, ~70 kHz) → RC filtr\n"
    "   I_SET = střída × 3,3 V = I × 1,1 V/A (FW max 2,0 A)\n"
    "U na zátěži = VOUT − I × 0,1 Ω\n"
    "CC_SENSE (PA2) > ~0,5 V → zdroj omezuje proud\n"
    "NTC (PB1): 10k/NTC dělič, 25 °C = 1,65 V\n"
    "\n"
    "PINY STM32 (Blue Pill)\n"
    "ADC: PA0 U, PA1 I, PA2 CC, PB0 limit I, PB1 NTC\n"
    "PA8 PWM limitu, PA3 zapnutí výstupu\n"
    "PB8–PB15 segmenty a–g, DP   PA4–PA7 číslice 1–4\n"
    "PB5 tlačítko U/I, PB6 tlačítko výstup\n"
    "LED: PA11 U, PB7 I, PA10 CC, PA9 výstup\n"
    "Displej: 2 des. místa: 12.34 V / 1.23 A",
    307, 156, 1.27)

tb = [Sym('title_block'), [Sym('title'), 'BuckBench – mini laboratorní zdroj (LM2596S + STM32)'],
      [Sym('date'), '2026-10-27'], [Sym('rev'), '1'],
      [Sym('comment'), 1, 'CV: modul LM2596S, CC: LM358 do FB, měření U/I a displej: STM32F103 (Blue Pill)'],
      [Sym('comment'), 2, 'Výstup 1,25–20 V / 0–2 A, vstup 24 V DC']]
os.makedirs(OUTDIR, exist_ok=True)
S.save(f'{OUTDIR}/{PROJECT}.kicad_sch', tb)
json.dump(S.netpins, open(f'{OUTDIR}/netpins.json', 'w'), indent=1)
print('ok', len(S.items))
