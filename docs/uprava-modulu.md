# Úprava modulu LM2596S a oživení

## 1. Úpravy modulu

1. **Odpájej trimr W103** (modrý, 10k) a **spodní rezistor děliče** (rezistor mezi FB a GND vedle trimru). Hodnotu si předtím změř multimetrem a poznamenej.
2. Na pájecí bod FB (pin 4 LM2596S) připoj:
   - R17 680R 1 % na GND,
   - drát k potenciometrům RV1 + RV2 (reostaty v sérii, druhý konec na OUT+),
   - katodu D2 (výstup obvodu CC).
   Dráty k potenciometrům drž krátké a zkroucené – FB je citlivý uzel.
3. **Pin 5 (ON/OFF)** LM2596S bývá spojen s GND. Spoj přeruš (nařízni cestu nebo nadzvedni vývod) a připoj na síť `EN`.
4. Výstupní svorku **OUT-** modulu nepoužívej jako výstup – slouží jako GND, na kterou je připojen bočník R1. Výstupní zdířka „−“ jde až za bočník.
5. Původní voltmetr a tlačítko modulu můžeš ponechat (měří před bočníkem) nebo odpojit.
6. Na LM2596S připevni malý chladič a na něj NTC (RT1) s teplovodivou pastou.

## 2. Oživení (postupně, s omezeným zdrojem nebo žárovkou v sérii)

1. Bez Blue Pillu: přiveď 24 V, ověř 5 V na výstupu MP1584 a 3,3 V na Blue Pillu po jeho zapojení.
2. Výstup je po zapnutí vypnutý (EN = 5 V). Dočasně spoj bázi Q5 přes 10k na 3,3 V → výstup se zapne. Ověř rozsah napětí 1,23–20 V potenciometry.
3. Bez zátěže změř `I_AMP` (≈ 0 V) a `U_SENSE` (= VOUT × 0,0909).
4. Na `I_SET` dočasně přiveď napětí z děliče (např. 0,55 V = 0,5 A). Zatěž výstup výkonovým rezistorem (např. 4,7 Ω) a ověř, že proud nepřekročí 0,5 A.
5. Osciloskopem zkontroluj výstup v režimu CC. Když kmitá, zvětši C5 (220 nF – 1 µF) nebo R11.
6. Teprve potom firmware a kalibrace.

## 3. Kalibrace (ve firmwaru)

Dvoubodová kalibrace proti multimetru zvlášť pro napětí a proud (např. 2 V a 15 V; 0,2 A a 1,8 A). Konstanty uložit do flash.
