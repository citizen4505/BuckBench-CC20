# Firmware (STM32F103C8 – Blue Pill)

Zatím připravuje se. Plánované funkce:

- ADC (DMA, průměrování): PA0 napětí, PA1 proud, PA2 režim CC, PB0 potenciometr limitu, PB1 NTC
- PWM PA8 (TIM1_CH1, ~70 kHz) – žádaná hodnota proudu 0–2 A
- Multiplex displeje: segmenty PB8–PB15, číslice PA4–PA7, obnova ~1 kHz (timer přerušení)
- Tlačítka: PB5 přepínání U/I, PB6 zapnutí/vypnutí výstupu (PA3)
- LED: PA11 U, PB7 I, PA10 CC, PA9 výstup zapnut
- Ochrany: trvalý zkrat (CC + U < 0,3 V po dobu > 2 s) → vypnout výstup; teplota > 85 °C → vypnout výstup
- Při startu: výstup vypnutý, limit proudu nastaven na minimum

## Převody

| Veličina | Vzorec |
|---|---|
| U na výstupu (před bočníkem) | `U_ADC × 11` |
| Proud | `I_ADC / 1,1` [A] |
| U na zátěži | `U − I × 0,1 Ω` |
| Žádaná hodnota | `střída = I × 1,1 / 3,3` |
