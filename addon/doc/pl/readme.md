# Global Sonic Pitch

Global Sonic Pitch pozwala obniżać i podwyższać głos NVDA za pomocą biblioteki
dźwiękowej Sonic. Dodaje osobne ustawienie **Sonic pitch**, niezależne od
regulacji **Wysokość** w syntezatorze. Dzięki temu możesz dostosować brzmienie
głosu bez zmieniania ustawionej szybkości mowy.

Dodatek przetwarza mowę wytworzoną przez obsługiwany syntezator. Nadal
korzystasz ze swojego dotychczasowego syntezatora i głosu. Przetwarzanie jest
domyślnie wyłączone.

## Wymagania i zgodność

Obecna deklaracja zgodności obejmuje NVDA od wersji 2025.1, z ostatnią
przetestowaną wersją 2026.1.1. Nie stanowi to potwierdzenia zgodności z przyszłymi
wersjami NVDA. Dodatek zawiera biblioteki Sonic dla NVDA 32- i 64-bitowego.

Obsługiwane są m.in. eSpeak NG, OneCore, RHVoice i SAPI5 64-bit, gdy mowa
trafia do obsługiwanego wyjścia dźwięku NVDA. Dodatek obsługuje też standardowe
32-bitowe SAPI5 i SAPI4 w NVDA 64-bitowym. **SAPI4 wymaga wyjścia dźwięku
WASAPI w NVDA; starsze wyjście dźwięku SAPI4 nie jest przetwarzane.**

Inne syntezatory mogą działać, jeśli korzystają ze zgodnego wyjścia mowy NVDA.

Jeśli używasz syntezatora sprzętowego, Sonic pitch nie przetwarza jego mowy,
ponieważ dźwięk powstaje w samym urządzeniu.

Dodatek nie zmienia dźwięku innych aplikacji ani dźwięków NVDA innych niż mowa.
Nie rejestruje również dodatkowych głosów SAPI.

## Instalacja

Zainstaluj **Global Sonic Pitch** ze sklepu dodatków NVDA. Możesz też pobrać
plik `.nvda-addon` z numerem wersji w nazwie ze strony
[wydań projektu](https://github.com/djgraco/sonicpitch/releases) i skorzystać
z opcji instalowania dodatku z pliku w NVDA. Uruchom ponownie NVDA, gdy
pojawi się odpowiedni komunikat.

## Pierwsze uruchomienie

1. Otwórz ustawienia NVDA i wybierz kategorię **Global Sonic Pitch**.
2. Zaznacz **Włącz globalny Sonic pitch**.
3. Wybierz **OK** lub **Zastosuj**, aby zapisać zmianę.
4. Otwórz ustawienia **Głos** i znajdź **Sonic pitch**. Możesz też wybrać
   tę pozycję w pierścieniu ustawień syntezatora.
5. Zmniejsz wartość, aby obniżyć głos, lub zwiększ ją, aby go podwyższyć.

**50 to wartość neutralna:** dodatek nie zmienia wtedy wysokości głosu.
Regulacja obejmuje wartości od 0 do 100. Liczby te nie oznaczają półtonów
ani procentowej zmiany częstotliwości. Zacznij od niewielkiej korekty
i posłuchaj efektu.

Po wyłączeniu przetwarzania pozycja **Sonic pitch** znika z ustawień głosu
i pierścienia ustawień syntezatora. Zapisane wartości zostają zachowane.

## Sonic pitch a wysokość syntezatora

Zwykłe ustawienie **Wysokość** steruje parametrem samego syntezatora.
**Sonic pitch** zmienia dźwięk, który syntezator już wytworzył. Słyszany
efekt zależy więc od obu ustawień. Możesz pozostawić wysokość syntezatora
na preferowanej wartości i użyć Sonic pitch do dodatkowej korekty.

Opisana tutaj wartość neutralna 50 dotyczy **Sonic pitch**. Nie oznacza
uniwersalnego ustawienia domyślnego wysokości we wszystkich syntezatorach.

## Ustawienia dodatku

W kategorii **Global Sonic Pitch** w ustawieniach NVDA znajdziesz:

- **Włącz globalny Sonic pitch** — włącza lub wyłącza przetwarzanie mowy.
- **Zwiększ zakres Sonic pitch do 20 półtonów** — zmienia zakres regulacji
  z zakresu −6 do +6 półtonów na zakres −20 do +20 półtonów. Domyślnie opcja jest wyłączona.
- **Użyj lepszej jakości przetwarzania Sonic** — wybiera tryb lepszej jakości.
  Może poprawić brzmienie niektórych głosów, ale zwiększyć obciążenie procesora.
  Domyślny jest tryb szybki. Opcja nie zmienia zakresu regulacji wysokości.
- **Włącz logowanie debugowania** — zapisuje informacje diagnostyczne w logu NVDA.
- **Wesprzyj autora** — otwiera stronę dobrowolnego wsparcia autora.

Samą wartość wysokości zmieniasz w ustawieniach głosu, pierścieniu ustawień
syntezatora lub przypisanym gestem, a nie w panelu dodatku. Zmiany w panelu
dodatku zapisz przyciskiem **OK** lub **Zastosuj**.

### Zakresy wysokości

| Sonic pitch | Zakres standardowy | Zakres rozszerzony |
| --- | --- | --- |
| 0 | −6 półtonów | −20 półtonów |
| 50 | Bez zmiany wysokości | Bez zmiany wysokości |
| 100 | +6 półtonów | +20 półtonów |

**Zmiana zakresu zmienia efekt zapisanych wartości innych niż 50.** Dodatek
nie przelicza dotychczasowych wartości tak, aby zachować poprzednią wysokość.
Na przykład 75 oznacza +3 półtony w zakresie standardowym i +10 półtonów
w rozszerzonym. Przy większych zmianach mogą być słyszalne zniekształcenia
wynikające z przetwarzania.

## Zapamiętywanie wartości i odsłuch zmian

Wartości są zapisywane osobno dla każdego syntezatora i głosu. Jeżeli
syntezator obsługuje warianty głosu, wariant również może mieć własną wartość.
Powrót do głosu lub wariantu przywraca jego zapisane ustawienie. Nowe głosy
zwykle zaczynają od 50; w starszej konfiguracji mogą odziedziczyć wcześniejszą wartość.

Zmiany w ustawieniach głosu można odsłuchiwać. **OK** lub **Zastosuj** zapisuje
je, a **Anuluj** lub **Escape** odrzuca zmiany wprowadzone od ostatniego zapisu
w tym oknie. Zmiany w pierścieniu ustawień syntezatora i za pomocą przypisanych
gestów są zapisywane od razu. Podczas wypowiedzi zmiana wysokości lub jakości
może zacząć działać dopiero przy najbliższej bezpiecznej granicy przetwarzania mowy.

## Zdarzenia wejścia

W oknie **Zdarzenia wejścia** w NVDA otwórz kategorię **Global Sonic Pitch**.
Możesz przypisać gesty do poleceń, które:

- przełączają przetwarzanie;
- odczytują stan przetwarzania i bieżącą wysokość;
- zwiększają lub zmniejszają Sonic pitch bieżącego głosu o 5;
- przywracają Sonic pitch bieżącego głosu do 50;
- otwierają stronę wsparcia autora.

Domyślnie żaden gest nie jest przypisany. Efekt zmiany o 5 zależy od wybranego
zakresu wysokości.

## Rozwiązywanie problemów

### Brakuje ustawienia Sonic pitch

Zaznacz **Włącz globalny Sonic pitch**, zapisz ustawienia i ponownie otwórz
ustawienia głosu. W razie potrzeby przełącz syntezator na inny i wróć do
poprzedniego albo uruchom ponownie NVDA.

### Zmiana wartości nie daje efektu

Sprawdź, czy przetwarzanie jest włączone, a wartość różni się od 50. Syntezator
musi korzystać z obsługiwanego wyjścia dźwięku. W przypadku SAPI4 starsze wyjście
omija dodatek. Samo włączenie lepszej jakości nie zmienia wysokości, gdy
Sonic pitch ma wartość neutralną.

### Wartość zmienia się po wybraniu innego głosu

Każdy głos lub obsługiwany wariant może mieć inne zapisane ustawienie.
W razie potrzeby dostosuj Sonic pitch dla nowo wybranego głosu.

### Głosu SAPI nie ma na liście NVDA

Zainstaluj i skonfiguruj głos za pomocą jego własnych narzędzi, a następnie
uruchom ponownie NVDA. Global Sonic Pitch nie dodaje ani nie naprawia wpisów
na liście głosów SAPI.

### Zgłaszanie problemu

Włącz logowanie debugowania, odtwórz problem i zbierz odpowiednie wpisy
za pomocą podglądu logu NVDA. Podaj wersję i architekturę NVDA, wersję dodatku,
syntezator i głos, wartość wysokości, zakres, tryb jakości oraz czynności
pozwalające odtworzyć problem. Przed udostępnieniem sprawdź log pod kątem prywatnych
treści. Problemy zgłaszaj w [systemie zgłoszeń](https://github.com/djgraco/sonicpitch/issues).

## Wsparcie autora

Przycisk **Wesprzyj autora** i odpowiadające mu polecenie otwierają stronę
[buycoffee.to/kazimierz-parzych](https://buycoffee.to/kazimierz-parzych).
Podczas instalacji lub aktualizacji może też pojawić się opcjonalne pytanie
o wsparcie. **Tak** otwiera tę stronę, a **Nie** kontynuuje instalację.
Wsparcie jest dobrowolne i nie jest wymagane do korzystania z żadnej funkcji.

## Licencja

Kod dodatku jest dostępny na licencji GNU GPL w wersji 2 lub nowszej.
Pakiet zawiera jej tekst w pliku `COPYING.txt`. Dołączone biblioteki DLL Sonic
są objęte licencją Apache 2.0, której tekst znajduje się w pliku
`globalPlugins/sonicPitchNative/LICENSE-Sonic.txt`. Zobacz również
`THIRD_PARTY_NOTICES.txt` w pakiecie.
