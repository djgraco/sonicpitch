# Global Sonic Pitch

Global Sonic Pitch umožňuje znížiť alebo zvýšiť výšku hlasu NVDA pomocou
zvukovej knižnice Sonic. Pridáva samostatné nastavenie **Sonic pitch**, nezávislé
od ovládania **Výška** v syntetizéri. Môžete tak upraviť znenie hlasu bez zmeny
nastavenej rýchlosti reči.

Doplnok spracúva reč vytvorenú podporovaným syntetizérom. Naďalej používate
svoj pôvodný syntetizér a hlas. Spracovanie je predvolene vypnuté.

## Požiadavky a kompatibilita

Aktuálne vyhlásenie o kompatibilite zahŕňa NVDA od verzie 2025.1, naposledy
testované s verziou 2026.1.1. Nepotvrdzuje kompatibilitu s budúcimi verziami
NVDA. Doplnok obsahuje knižnice Sonic pre 32-bitové aj 64-bitové NVDA.

Podporované sú napríklad eSpeak NG, OneCore, RHVoice a 64-bitové SAPI5, ak
reč prechádza podporovaným zvukovým výstupom NVDA. Podporované sú aj štandardné
32-bitové SAPI5 a SAPI4 v 64-bitovom NVDA. **SAPI4 vyžaduje zvukový výstup
WASAPI v NVDA; starší zvukový výstup SAPI4 sa nespracúva.**

Iné syntetizéry môžu fungovať, ak používajú kompatibilný výstup reči NVDA.

Ak používate hardvérový syntetizér reči, Sonic pitch jeho reč nespracúva,
pretože zvuk vzniká v samotnom zariadení.

Doplnok nemení zvuk iných aplikácií ani zvuky NVDA, ktoré nie sú rečou.
Neregistruje ďalšie hlasy SAPI.

## Inštalácia

Nainštalujte **Global Sonic Pitch** z obchodu s doplnkami NVDA. Prípadne
stiahnite súbor `.nvda-addon` s číslom verzie v názve zo stránky
[vydaní projektu](https://github.com/djgraco/sonicpitch/releases) a použite
možnosť inštalácie doplnku zo súboru v NVDA. Po výzve reštartujte NVDA.

## Prvé použitie

1. Otvorte nastavenia NVDA a vyberte kategóriu **Global Sonic Pitch**.
2. Začiarknite **Povoliť globálny Sonic pitch**.
3. Zvoľte **OK** alebo **Použiť**, aby sa zmena uložila.
4. Otvorte nastavenia **Hlas** a nájdite **Sonic pitch**. Môžete ho vybrať
   aj v kruhu nastavení syntetizéra.
5. Znížte hodnotu, ak chcete hlas znížiť, alebo ju zvýšte, ak ho chcete zvýšiť.

**50 je neutrálna hodnota:** doplnok vtedy výšku hlasu nemení. Ovládanie
používa hodnoty od 0 do 100. Tieto čísla neoznačujú poltóny ani percentuálnu
zmenu frekvencie. Začnite malou úpravou a vypočujte si výsledok.

Po vypnutí spracovania položka **Sonic pitch** zmizne z nastavení hlasu
a z kruhu nastavení syntetizéra. Uložené hodnoty zostanú zachované.

## Sonic pitch a výška syntetizéra

Bežné nastavenie **Výška** ovláda parameter samotného syntetizéra.
**Sonic pitch** mení zvuk, ktorý syntetizér už vytvoril. Výsledok preto závisí
od oboch nastavení. Výšku syntetizéra môžete ponechať na obľúbenej hodnote
a pomocou Sonic pitch vykonať ďalšiu úpravu.

Neutrálna hodnota 50 opísaná v tejto príručke platí pre **Sonic pitch**.
Neurčuje všeobecnú predvolenú výšku pre všetky syntetizéry.

## Nastavenia doplnku

V kategórii **Global Sonic Pitch** v nastaveniach NVDA nájdete:

- **Povoliť globálny Sonic pitch** — zapne alebo vypne spracovanie reči.
- **Zvýšiť rozsah Sonic pitch na 20 poltónov** — zmení rozsah z −6 až +6
  poltónov na −20 až +20 poltónov. Predvolene je táto možnosť vypnutá.
- **Použiť kvalitnejšie spracovanie Sonic** — zvolí kvalitnejší režim.
  Môže zlepšiť znenie niektorých hlasov, ale zvýšiť zaťaženie procesora.
  Predvolený je rýchly režim. Táto možnosť nemení rozsah výšky.
- **Povoliť ladiace záznamy** — zapisuje diagnostické informácie do logu NVDA.
- **Podporiť autora** — otvorí stránku dobrovoľnej podpory autora.

Samotnú výšku meníte v nastaveniach hlasu, v kruhu nastavení syntetizéra
alebo priradeným gestom, nie v paneli doplnku. Zmeny v paneli doplnku uložte
tlačidlom **OK** alebo **Použiť**.

### Rozsahy výšky

| Sonic pitch | Bežný rozsah | Rozšírený rozsah |
| --- | --- | --- |
| 0 | −6 poltónov | −20 poltónov |
| 50 | Bez zmeny výšky | Bez zmeny výšky |
| 100 | +6 poltónov | +20 poltónov |

**Zmena rozsahu zmení účinok uložených hodnôt odlišných od 50.** Doplnok
neprepočíta existujúce hodnoty tak, aby zachoval pôvodnú výšku. Napríklad
75 znamená +3 poltóny v bežnom rozsahu a +10 poltónov v rozšírenom rozsahu.
Pri väčších zmenách môžu byť počuteľné skreslenia spôsobené spracovaním.

## Uložené hodnoty a počúvanie zmien

Hodnoty sa ukladajú samostatne pre každý syntetizér a hlas. Ak syntetizér
podporuje varianty hlasu, aj variant môže mať vlastnú hodnotu. Návrat k hlasu
alebo variantu obnoví jeho uložené nastavenie. Nové hlasy zvyčajne začínajú
na 50; staršie konfigurácie môžu poskytnúť predtým uloženú hodnotu.

Zmeny v nastaveniach hlasu si môžete vypočuť. **OK** alebo **Použiť** ich
uloží, **Zrušiť** alebo **Escape** zahodí zmeny od posledného uloženia v tomto
okne. Zmeny v kruhu nastavení syntetizéra a pomocou priradených gest sa
ukladajú okamžite. Počas reči sa zmena výšky alebo kvality môže prejaviť až
pri najbližšej bezpečnej hranici spracovania reči.

## Vstupné gestá

V okne **Vstupné gestá** v NVDA otvorte kategóriu **Global Sonic Pitch**.
Môžete priradiť gestá k príkazom, ktoré:

- prepínajú spracovanie;
- oznámia stav spracovania a aktuálnu výšku;
- zvýšia alebo znížia Sonic pitch aktuálneho hlasu o 5;
- obnovia Sonic pitch aktuálneho hlasu na 50;
- otvoria stránku podpory autora.

Predvolene nie sú priradené žiadne gestá. Účinok zmeny o 5 závisí od zvoleného
rozsahu výšky.

## Riešenie problémov

### Chýba nastavenie Sonic pitch

Začiarknite **Povoliť globálny Sonic pitch**, uložte nastavenia a znova otvorte
nastavenia hlasu. V prípade potreby prepnite na iný syntetizér a späť alebo
reštartujte NVDA.

### Zmena hodnoty nemá účinok

Overte, či je spracovanie zapnuté a hodnota sa líši od 50. Syntetizér musí
používať podporovaný zvukový výstup. Pri SAPI4 starší výstup doplnok obchádza.
Samotné zapnutie kvalitnejšieho režimu nemení výšku, keď je Sonic pitch neutrálny.

### Hodnota sa zmení po výbere iného hlasu

Každý hlas alebo podporovaný variant môže mať inú uloženú hodnotu. V prípade
potreby upravte Sonic pitch pre novozvolený hlas.

### Hlas SAPI chýba v zozname NVDA

Nainštalujte a nastavte hlas pomocou jeho vlastných nástrojov a reštartujte
NVDA. Global Sonic Pitch nepridáva ani neopravuje položky v zozname hlasov SAPI.

### Nahlásenie problému

Zapnite ladiace záznamy, zopakujte problém a zozbierajte príslušné záznamy
pomocou prehliadača logu NVDA. Uveďte verziu a architektúru NVDA, verziu doplnku,
syntetizér a hlas, hodnotu výšky, rozsah, režim kvality a kroky na zopakovanie
problému. Pred zdieľaním skontrolujte, či log neobsahuje súkromný text.
Problémy hláste v [systéme hlásení](https://github.com/djgraco/sonicpitch/issues).

## Podpora autora

Tlačidlo **Podporiť autora** a príslušný príkaz otvoria stránku
[buycoffee.to/kazimierz-parzych](https://buycoffee.to/kazimierz-parzych).
Počas inštalácie alebo aktualizácie sa môže zobraziť aj voliteľná otázka
o podpore. **Áno** otvorí túto stránku, **Nie** pokračuje v inštalácii.
Podpora je dobrovoľná a nie je potrebná na používanie žiadnej funkcie.

## Licencia

Zdrojový kód doplnku je dostupný pod licenciou GNU GPL verzie 2 alebo novšej.
Balík obsahuje jej text v súbore `COPYING.txt`. Pribalené knižnice DLL Sonic
sú pod licenciou Apache 2.0, ktorej text je v súbore
`globalPlugins/sonicPitchNative/LICENSE-Sonic.txt`. Pozrite si aj
`THIRD_PARTY_NOTICES.txt` v balíku.
