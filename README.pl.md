# Global Sonic Pitch

Global Sonic Pitch pozwala obniżać i podwyższać głos NVDA za pomocą biblioteki
dźwiękowej Sonic. Dodaje osobną regulację **Sonic pitch**, niezależną od
ustawienia **Wysokość** w syntezatorze. Dzięki temu możesz dostosować brzmienie
głosu bez zmieniania ustawionej szybkości mowy.

[English](README.md) | Polski | [Slovenčina](README.sk.md)

## Możliwości

- Regulacja wysokości w ustawieniach głosu lub pierścieniu ustawień syntezatora.
- Osobne ustawienia dla syntezatorów, głosów i obsługiwanych wariantów głosu.
- Standardowy zakres od −6 do +6 półtonów oraz opcjonalny zakres od −20 do
  +20 półtonów. W obu zakresach wartość neutralna wynosi 50.
- Opcjonalny tryb lepszej jakości przetwarzania Sonic.
- Możliwość przypisania własnych gestów do przełączania przetwarzania,
  zmiany wysokości i przywracania wartości neutralnej.

Dodatek obsługuje m.in. eSpeak NG, OneCore, RHVoice oraz obsługiwane
konfiguracje SAPI. Zgodność zależy od sposobu przekazywania dźwięku przez
syntezator; szczegóły znajdziesz w [instrukcji](addon/doc/pl/readme.md).

## Instalacja i pierwsze uruchomienie

Zainstaluj **Global Sonic Pitch** ze sklepu dodatków NVDA albo pobierz plik
`globalSonicPitch-<wersja>.nvda-addon` z [wydań projektu](https://github.com/djgraco/sonicpitch/releases).
Pobrany plik zainstaluj za pomocą opcji instalowania dodatku z pliku w NVDA.
Uruchom ponownie NVDA, gdy pojawi się odpowiedni komunikat.

1. Otwórz ustawienia NVDA i wybierz kategorię **Global Sonic Pitch**.
2. Zaznacz **Włącz globalny Sonic pitch**, a następnie wybierz **OK** lub **Zastosuj**.
3. Otwórz ustawienia **Głos** i zmień **Sonic pitch**. Wartości poniżej 50
   obniżają głos, a wartości powyżej 50 go podwyższają.

Przetwarzanie jest domyślnie wyłączone. Nadal korzystasz ze swojego
dotychczasowego syntezatora; nie musisz wybierać dodatkowego syntezatora.

## Dokumentacja i rozwój

- [Instrukcja obsługi](addon/doc/pl/readme.md)
- [Historia wydań](CHANGELOG.md)
- [Budowanie i struktura repozytorium](docs/building.md) — po angielsku
- [Wskazówki dla tłumaczy](docs/translating.md) — po angielsku
- [Informacje techniczne](docs/technical-notes.md) — po angielsku
- [Lista testów](TESTING.md) — po angielsku
- [Współpraca przy projekcie](CONTRIBUTING.md) — po angielsku

Po przygotowaniu narzędzi opisanych w instrukcji budowania wykonaj
`uv sync --locked`, a następnie `uv run scons`. Budowanie generuje pomoc HTML,
skompilowane tłumaczenia i manifesty, po czym tworzy pakiet dodatku z numerem
wersji w nazwie. Narzędzia są oparte na [NVDA Add-on Template](https://github.com/nvaccess/AddonTemplate).

## Licencja

Kod dodatku jest dostępny na licencji GNU GPL w wersji 2 lub nowszej.
Zobacz [LICENSE.md](LICENSE.md) i [COPYING.txt](COPYING.txt).
Dołączone biblioteki DLL Sonic są objęte licencją Apache 2.0;
szczegóły opisano w [informacjach o komponentach zewnętrznych](THIRD_PARTY_NOTICES.md).
