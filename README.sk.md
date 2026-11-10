# Global Sonic Pitch

Global Sonic Pitch umožňuje znížiť alebo zvýšiť výšku hlasu NVDA pomocou
zvukovej knižnice Sonic. Pridáva samostatné nastavenie **Sonic pitch**, nezávislé
od nastavenia **Výška** v syntetizéri. Môžete tak upraviť znenie hlasu bez
zmeny nastavenej rýchlosti reči.

[English](README.md) | [Polski](README.pl.md) | Slovenčina

## Možnosti

- Úprava výšky v nastaveniach hlasu alebo v kruhu nastavení syntetizéra.
- Samostatné hodnoty pre syntetizéry, hlasy a podporované varianty hlasu.
- Bežný rozsah od −6 do +6 poltónov a voliteľný rozsah od −20 do +20
  poltónov. Neutrálna hodnota je v oboch rozsahoch 50.
- Voliteľný režim kvalitnejšieho spracovania Sonic.
- Možnosť priradiť vlastné gestá na prepínanie spracovania, zmenu výšky
  a obnovenie neutrálnej hodnoty.

Doplnok podporuje napríklad eSpeak NG, OneCore, RHVoice a podporované
konfigurácie SAPI. Kompatibilita závisí od spôsobu, akým syntetizér odovzdáva
zvuk NVDA; podrobnosti nájdete v [používateľskej príručke](addon/doc/sk/readme.md).

## Inštalácia a prvé použitie

Nainštalujte **Global Sonic Pitch** z obchodu s doplnkami NVDA alebo stiahnite
súbor `globalSonicPitch-<verzia>.nvda-addon` zo stránky
[vydaní projektu](https://github.com/djgraco/sonicpitch/releases).
Stiahnutý súbor nainštalujte pomocou možnosti inštalácie doplnku zo súboru v NVDA.
Po výzve reštartujte NVDA.

1. Otvorte nastavenia NVDA a vyberte kategóriu **Global Sonic Pitch**.
2. Začiarknite **Povoliť globálny Sonic pitch** a zvoľte **OK** alebo **Použiť**.
3. Otvorte nastavenia **Hlas** a upravte **Sonic pitch**. Hodnoty nižšie ako
   50 hlas znižujú, hodnoty vyššie ako 50 ho zvyšujú.

Spracovanie je predvolene vypnuté. Naďalej používate svoj pôvodný syntetizér;
nemusíte vyberať ďalší syntetizér.

## Dokumentácia a vývoj

- [Používateľská príručka](addon/doc/sk/readme.md)
- [História vydaní](CHANGELOG.md)
- [Zostavenie a štruktúra repozitára](docs/building.md) — v angličtine
- [Pokyny pre prekladateľov](docs/translating.md) — v angličtine
- [Technické poznámky](docs/technical-notes.md) — v angličtine
- [Kontrolný zoznam testov](TESTING.md) — v angličtine
- [Prispievanie do projektu](CONTRIBUTING.md) — v angličtine

Po príprave nástrojov podľa návodu na zostavenie spustite `uv sync --locked`
a potom `uv run scons`. Zostavenie vygeneruje pomoc vo formáte HTML,
skompilované preklady a manifesty a vytvorí balík doplnku s číslom verzie v názve.
Nástroje sú založené na [NVDA Add-on Template](https://github.com/nvaccess/AddonTemplate).

## Licencia

Zdrojový kód doplnku je dostupný pod licenciou GNU GPL verzie 2 alebo novšej.
Pozrite si [LICENSE.md](LICENSE.md) a [COPYING.txt](COPYING.txt).
Pribalené knižnice DLL Sonic sú pod licenciou Apache 2.0;
podrobnosti sú v [oznámeniach o súčastiach tretích strán](THIRD_PARTY_NOTICES.md).
