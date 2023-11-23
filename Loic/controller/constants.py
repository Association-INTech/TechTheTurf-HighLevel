EVENT_TYPES = 'UNKNOWN', 'DIGITAL', 'ANALOG', 'PAD'
OTHER_TYPE, DIGITAL, ANALOG, PAD = range(4)

DIGITAL_BUTTONS = (
    'x', 'o', 'Δ', '□', 'L1', 'R1', 'L2', 'R2', 'Share', 'Options', 'Playstation', 'L3', 'R3'
)
CROSS, CIRCLE, TRIANGLE, SQUARE, L1, R1, L2_D, R2_D, SHARE, OPTIONS, PS, L3, R3 = range(13)

ANALOG_BUTTONS = (
    'Lx', 'Ly', 'L2', 'Rx', 'Ry', 'R2', 'H_arrows', 'V_arrows'
)
LX, LY, L2_A, RX, RY, R2_A, H_ARROWS, V_ARROWS = range(8)


PAD_STATES = (
    'UP', 'DOWN'
)
PAD_UP, PAD_DOWN = range(2)

BUTTON_NAMES = DIGITAL_BUTTONS, ANALOG_BUTTONS, PAD_STATES

# Used to display Events
EVENT_FORMAT = "Event<type={}, button={}, value={}>"
BUTTONS = {
    (ty, bu): name for ty, buttons in enumerate(BUTTON_NAMES, 1) for bu, name in enumerate(buttons)
}
