import csv
import io
import logging
import os

import requests
from dotenv import load_dotenv
import openai
from openai import OpenAI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["AIDEVS_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 1. Fetch people.csv ---
csv_url = f"https://hub.ag3nts.org/data/{AIDEVS_API_KEY}/people.csv"
logger.info("Fetching people.csv from hub")
response = requests.get(csv_url)
response.raise_for_status()
reader = csv.DictReader(io.StringIO(response.text))
people = list(reader)
logger.info("Fetched %d people", len(people))

# --- 2. Filter by criteria ---
# Males, born in Grudziądz, age between 20 and 40 in 2026
filtered = [
    p for p in people
    if p["gender"] == "M"
    and p["birthPlace"] == "Grudziądz"
    # Extract birth year from date in format RRRR-MM-DD
    and 20 <= (2026 - int(p["birthDate"].split("-")[0])) <= 40
]
logger.info("Filtered to %d people (male, Grudziądz, age 20-40)", len(filtered))
logger.debug("Filtered people: %s", [f"{p['name']} {p['surname']}" for p in filtered])

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

logger.info("Sending %d jobs to LLM for tagging", len(filtered))
try:
    completion = client.responses.parse(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": prompt}],
        text_format=TaggingResult,
    )
except openai.APIStatusError as e:
    logger.error("OpenAI API error %s: %s", e.status_code, e.message)
    raise

if completion.output_parsed is None:
    logger.error("LLM returned no parsed output: %s", completion.output_text)
    raise ValueError("LLM tagging returned no structured output")

tagging = completion.output_parsed
logger.debug("LLM tagging result: %s", tagging)

# --- 4. Keep only people tagged with "transport" ---
transport_indices = {r.index for r in tagging.results if "transport" in r.tags}
tags_by_index = {r.index: r.tags for r in tagging.results}
logger.info("Transport-tagged indices: %s", transport_indices)

answer = []
for i, p in enumerate(filtered):
    if i in transport_indices:
        answer.append({
            "name": p["name"],
            "surname": p["surname"],
            "gender": p["gender"],
            "born": int(p["birthDate"].split("-")[0]),
            "city": p["birthPlace"],
            "tags": tags_by_index[i],
        })

logger.info("Answer contains %d people: %s", len(answer), [f"{a['name']} {a['surname']}" for a in answer])

# --- 5. Submit answer ---
payload = {
    "apikey": AIDEVS_API_KEY,
    "task": "people",
    "answer": answer,
}

logger.info("Submitting answer to hub")
verify_response = requests.post("https://hub.ag3nts.org/verify", json=payload)
result = verify_response.json()
logger.info("Verify response: %s", result)
print(result)
