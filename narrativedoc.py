import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
narrative_file = os.path.join(SCRIPT_DIR, "narrativedoc.json")
checkbox_file = os.path.join(SCRIPT_DIR, "checkbox_values.txt")

base_url = "https://www.bodc.ac.uk/data/documents/series/"

# ✅ Réutilisation de session pour accélérer les requêtes
session = requests.Session()

def load_checkbox_values():
    """Charge les 100 premières valeurs numériques du fichier checkbox_values.txt"""
    try:
        with open(checkbox_file, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip().isdigit()][:]
    except FileNotFoundError:
        print(f"Fichier {checkbox_file} introuvable.")
        return []

def load_existing_narratives():
    """Charge les documents narratifs existants sous forme de set"""
    if not os.path.exists(narrative_file):
        return set()
    try:
        with open(narrative_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
            return set(existing_data)  # Charger comme un ensemble pour éviter les doublons
    except (json.JSONDecodeError, FileNotFoundError):
        return set()

def fetch_narrative_document(url):
    """Récupère le texte narratif depuis l'URL avec session"""
    try:
        response = session.get(url, timeout=7, verify=False)  # ✅ Désactive SSL pour gagner du temps
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'lxml')
        narrative_section = soup.find("h1", string="Narrative Documents")
        if not narrative_section:
            return None

        narrative_text = []
        for sibling in narrative_section.find_next_siblings():
            if sibling.name == "h1" and sibling.text.strip() == "Project Information":
                break
            narrative_text.append(sibling.get_text(strip=True))

        return " ".join(narrative_text).strip()
    except Exception:
        return None

def fetch_all_narratives():
    """Récupère et met à jour le JSON avec de nouveaux documents narratifs uniques"""
    checkbox_values = load_checkbox_values()
    existing_narratives = load_existing_narratives()
    new_narratives = set()

    with ThreadPoolExecutor(max_workers=50) as executor:  # ✅ Augmentation des threads
        futures = {executor.submit(fetch_narrative_document, f"{base_url}{value}/"): value for value in checkbox_values}

        with tqdm(total=len(checkbox_values), desc="Extraction des documents narratifs", unit="page") as progress:
            for future in as_completed(futures):  # ✅ Traite les résultats dès qu'ils arrivent
                narrative_text = future.result()
                if narrative_text and narrative_text not in existing_narratives:
                    new_narratives.add(narrative_text)
                progress.update(1)

    # ✅ Mise à jour JSON optimisée
    if new_narratives:
        with open(narrative_file, "w", encoding="utf-8") as json_file:
            json.dump(list(existing_narratives.union(new_narratives)), json_file, indent=4, ensure_ascii=False)

    print(f"Extraction terminée. Résultats enregistrés dans '{narrative_file}'.")

# Exécution
fetch_all_narratives()
