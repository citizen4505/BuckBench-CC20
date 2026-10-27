# Buckbench-CC20

Mini kompaktní laboratorní zdroj postavený na levném modulu **LM2596S** (step-down), doplněný o omezení proudu (CC), měření napětí a proudu a řízení mikrokontrolérem **STM32F103** (Blue Pill).

📄 [Schéma zapojení (PDF)](hardware/buckbench-cc20.pdf) · [BOM](hardware/bom.csv)

## Specifikace

| Parametr | Hodnota |
|---|---|
| Vstup | 24 V DC (adaptér) |
| Výstupní napětí | 1,25 – 20 V (potenciometry hrubě + jemně) |
| Výstupní proud | 0 – 2 A, nastavitelné omezení (CC) |
| Měření | výstupní napětí a proud, 4místný 7seg. displej, 2 desetinná místa (`12.34` V / `1.23` A), přepínání U/I tlačítkem |
| Ochrany | zkrat na výstupu, zkrat a přepólování na vstupu, přepětí na vstupu, přehřátí, zpětné napětí na výstupu |

## Jak to funguje

- **CV (napětí):** regulaci dělá přímo LM2596S. Původní trimr na modulu je nahrazen panelovými potenciometry RV1 (10k, hrubě) a RV2 (500R, jemně) a spodní rezistor děliče novým R17 680R 1 %:
  `U = 1,23 V × (1 + R_RV / 680 Ω)` → 1,23 V až ~20,2 V.
- **CC (proud):** bočník 0,1 Ω v mínusové větvi → LM358 (U1A, zesílení 11) → integrátor U1B porovná proud s žádanou hodnotou. Při překročení „přetlačí“ přes D2 pin FB LM2596S a výstupní napětí klesne.
- **Žádaná hodnota proudu:** potenciometr RV3 čte STM32 (ADC), ten generuje PWM (PA8), které RC filtr převede na napětí `I_SET`. Firmware omezí rozsah na 0–2 A.
- **Zapnutí výstupu:** pin 5 (ON/OFF) LM2596S ovládá STM32 přes Q5. Výchozí stav (reset, zamrzlý MCU) = **výstup vypnut**.

## Ochrany

| Porucha | Řešení |
|---|---|
| Zkrat na výstupu | CC smyčka omezí proud na nastavenou hodnotu; vnitřní limit LM2596 (~3 A) jako záloha; firmware při trvalém zkratu výstup vypne |
| Zkrat / přetížení na vstupu | pojistka F1 (T 3 A) |
| Přepólování vstupu | sériová Schottky dioda D8 (SS54) |
| Přepětí na vstupu | TVS dioda D7 (SMBJ24CA) |
| Přehřátí | NTC na chladiči LM2596 → ADC, firmware vypne výstup nad ~85 °C; záloha: tepelná ochrana uvnitř LM2596 |
| Zpětné / opačné napětí na výstupu | dioda D9 (SS54) přes výstupní svorky |

## Struktura repozitáře

```
hardware/   KiCad 7 projekt (schéma, knihovna Lab symbolů), PDF schématu, BOM
firmware/   firmware pro STM32F103 (připravuje se)
docs/       postup úpravy modulu, oživení, kalibrace
tools/      generátor schématu (Python), kontrola zapojení proti netlistu
```

## Postup stavby

Viz [docs/uprava-modulu.md](docs/uprava-modulu.md) – úpravy modulu LM2596S a oživení krok za krokem.

## Stav projektu

- [x] Schéma zapojení (rev. 1)
- [ ] Ověření CC smyčky na nepájivém poli (stabilita integrátoru)
- [ ] Firmware: měření, displej, PWM limitu, ochrany
- [ ] Deska plošných spojů / rozložení v krabičce
- [ ] Kalibrace a měření parametrů
