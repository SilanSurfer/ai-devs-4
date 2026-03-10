# Zadanie

Pobierz listę osób, które przeżyły 'Wielką Korektę' i które współpracują z systemem. Znajdziesz ją pod linkiem:
`https://hub.ag3nts.org/data/<twój-klucz>/people.csv`

Wiemy, że do organizacji transportów między elektrowniami angażowani są ludzie, którzy:

- są mężczyznami
- w 2026 roku mają między 20 a 40 lat
- urodzeni w Grudziądzu
- pracują w branży transportowej

Każdą z potencjalnych osób musisz odpowiednio otagować. Dostępne tagi:

- `IT`
- `transport`
- `edukacja`
- `medycyna`
- `praca z ludźmi`
- `praca z pojazdami`
- `praca fizyczna`

Jedna osoba może mieć wiele tagów. Nas interesują tylko ludzie pracujący w transporcie, którzy spełniają też poprzednie warunki.

## Odpowiedź

Prześlij listę osób na adres `https://hub.ag3nts.org/verify`. Nazwa zadania: `people`.

```json
{
  "apikey": "<twój-klucz-api>",
  "task": "people",
  "answer": [
    {
      "name": "Jan",
      "surname": "Kowalski",
      "gender": "M",
      "born": 1987,
      "city": "Warszawa",
      "tags": ["tag1", "tag2"]
    },
    {
      "name": "Anna",
      "surname": "Nowak",
      "gender": "F",
      "born": 1993,
      "city": "Grudziądz",
      "tags": ["tagA", "tagB", "tagC"]
    }
  ]
}
```

## Co należy zrobić?

1. **Pobierz dane z hubu** — plik `people.csv` dostępny pod linkiem z treści zadania (wstaw swój klucz API z https://hub.ag3nts.org/). Plik zawiera dane osobowe wraz z opisem stanowiska pracy (`job`).
2. **Przefiltruj dane** — zostaw wyłącznie osoby spełniające wszystkie kryteria: płeć, miejsce urodzenia, wiek.
3. **Otaguj zawody modelem językowym** — wyślij opisy stanowisk (`job`) do LLM i poproś o przypisanie tagów z listy. Użyj mechanizmu Structured Output, aby wymusić odpowiedź w określonym formacie JSON. Szczegóły w sekcji Wskazówki.
4. **Wybierz osoby z tagiem `transport`** — z otagowanych rekordów wybierz wyłącznie te z tagiem `transport`.
5. **Wyślij odpowiedź** — prześlij tablicę obiektów na `https://hub.ag3nts.org/verify` w formacie pokazanym powyżej.
6. **Zdobycie flagi** — jeśli dane będą poprawne, Hub odeśle flagę w formacie `{FLG:JAKIES_SLOWO}`. Wpisz ją na https://hub.ag3nts.org/ (zaloguj się kontem, którym zrobiłeś zakup kursu).

## Wskazówki

- **Structured Output** — Polega na wymuszeniu odpowiedzi modelu w ściśle określonym formacie JSON przez przekazanie schematu (JSON Schema) w polu `response_format` wywołania API. Eliminuje całą klasę błędów parsowania. Możesz też użyć bibliotek jak [Instructor](https://github.com/instructor-ai/instructor) (Python/JS/TypeScript).
- **Batch tagging** — Zamiast wywoływać LLM osobno dla każdej osoby, wyślij w jednym żądaniu ponumerowaną listę opisów stanowisk i poproś o zwrócenie listy obiektów z numerem rekordu i przypisanymi tagami. Znacznie redukuje liczbę wywołań API.
- **Opisy tagów pomagają modelowi** — Do każdej kategorii dołącz krótki opis zakresu, by model poprawnie klasyfikował niejednoznaczne stanowiska.
- **Format pól w odpowiedzi** — `born` to liczba całkowita (sam rok urodzenia). `tags` to tablica stringów, nie jeden string z przecinkami.
