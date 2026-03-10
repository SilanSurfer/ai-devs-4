import csv
import io
import os

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["AIDEVS_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 1. Fetch people.csv ---
csv_url = f"https://hub.ag3nts.org/data/{AIDEVS_API_KEY}/people.csv"
response = requests.get(csv_url)
response.raise_for_status()
reader = csv.DictReader(io.StringIO(response.text))
people = list(reader)

# --- 2. Filter by criteria ---
# Males, born in Grudziądz, age between 20 and 40 in 2026
filtered = [
    p for p in people
    if p["gender"] == "M"
    and p["city"] == "Grudziądz"
    and 20 <= (2026 - int(p["born"])) <= 40
]

# --- 3. Tag jobs with LLM using Structured Output ---
TAG_DESCRIPTIONS = {
    "IT": "informatyka, programowanie, systemy, sieci, technologie",
    "transport": "kierowcy, logistyka, spedycja, przewóz towarów/osób, pojazdy ciężarowe",
    "edukacja": "nauczyciele, trenerzy, szkolenia, uczelnie",
    "medycyna": "lekarze, pielęgniarki, farmacja, opieka zdrowotna",
    "praca z ludźmi": "obsługa klienta, sprzedaż, HR, zarządzanie zespołem",
    "praca z pojazdami": "mechanicy, serwis pojazdów, operatorzy maszyn",
    "praca fizyczna": "budownictwo, magazynowanie, produkcja, prace manualne",
}

tag_descriptions_str = "\n".join(f"- {tag}: {desc}" for tag, desc in TAG_DESCRIPTIONS.items())
numbered_jobs = "\n".join(f"{i}. {p['job']}" for i, p in enumerate(filtered))

prompt = f"""Przypisz tagi do poniższych stanowisk pracy. Każde stanowisko może otrzymać wiele tagów.
Używaj wyłącznie tagów z poniższej listy:

{tag_descriptions_str}

Stanowiska:
{numbered_jobs}

Zwróć listę obiektów z polami "index" (numer stanowiska) i "tags" (lista przypisanych tagów)."""


class JobTags(BaseModel):
    index: int
    tags: list[str]


class TaggingResult(BaseModel):
    results: list[JobTags]


completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    response_format=TaggingResult,
)

tagging = completion.choices[0].message.parsed

# --- 4. Keep only people tagged with "transport" ---
transport_indices = {r.index for r in tagging.results if "transport" in r.tags}
tags_by_index = {r.index: r.tags for r in tagging.results}

answer = []
for i, p in enumerate(filtered):
    if i in transport_indices:
        answer.append({
            "name": p["name"],
            "surname": p["surname"],
            "gender": p["gender"],
            "born": int(p["born"]),
            "city": p["city"],
            "tags": tags_by_index[i],
        })

# --- 5. Submit answer ---
payload = {
    "apikey": AIDEVS_API_KEY,
    "task": "people",
    "answer": answer,
}

verify_response = requests.post("https://hub.ag3nts.org/verify", json=payload)
print(verify_response.json())
