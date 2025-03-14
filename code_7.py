'''Ce code commence par lire l'ensemble des 33309 ligne du tableau des avec les liens vers les différentes
data. Une foix tous les liens récupérer un parcour tous les liens et on récupère les data intéressantes'''


import os
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm 


# Déterminer le répertoire du script actuel
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKBOX_FILE = os.path.join(SCRIPT_DIR, "checkbox_values.txt")

# Fonction pour vérifier si le fichier existe et charger les valeurs
def load_or_generate_checkbox_values():
    if os.path.exists(CHECKBOX_FILE):
        reponse=input("Un fichier 'checkbox_values.txt' à été trouvé, voulez vous l'utiliser (Y/N) : ")
        if reponse=="Y":
            print(f"Fichier {CHECKBOX_FILE} trouvé. Chargement des valeurs...")
            with open(CHECKBOX_FILE, "r") as file:
                checkbox_values = [line.strip() for line in file if line.strip().isdigit()]
            print(f"Nombre de valeurs chargées depuis le fichier : {len(checkbox_values)}")
            return checkbox_values
        else:
            print("fichier pas utiliser. Génération d'un nouveau")
            return generate_checkbox_values()
    else:
        print(f"Fichier {CHECKBOX_FILE} introuvable. Génération des valeurs...")
        return generate_checkbox_values()

# Fonction pour générer les valeurs des checkboxes et les stocker dans un fichier
def generate_checkbox_values():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = "https://www.bodc.ac.uk/data/bodc_database/samples/"
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'tabofres'))
    )

    checkbox_values = []
    page_number = 1


    with open(CHECKBOX_FILE, "w") as file:
        while True:
            print(f"Traitement de la page {page_number}...")
            table = driver.find_element(By.ID, 'tabofres')
            checkboxes = table.find_elements(By.XPATH, './/input[@type="checkbox"]')

            for checkbox in checkboxes:
                value = checkbox.get_attribute('value')
                if value.isdigit():
                    checkbox_values.append(value)
                    file.write(value + "\n")
            try:
                next_button = driver.find_element(By.XPATH, '//*[@id="pageinforesults"]//span[@id="xxxnext"]')
                next_button.click()
                WebDriverWait(driver, 5).until(EC.staleness_of(checkboxes[0]))
                page_number += 1
            except:
                print("Aucune autre page trouvée. Extraction terminée.")
                break

    driver.quit()
    print(f"Nombre total de valeurs numériques enregistrées : {len(checkbox_values)}")
    return checkbox_values

checkbox_values = load_or_generate_checkbox_values()

base_url = "https://www.bodc.ac.uk/data/documents/series/"

def fetch_parameters_table(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Erreur HTTP pour {url}: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        # Extraction de la section Parameters
        parameters_section = soup.find("h2", string="Parameters")
        if not parameters_section:
            print(f"Aucune section 'Parameters' trouvée pour {url}")
            return None

        table = parameters_section.find_next("table")
        if not table:
            print(f"Aucun tableau trouvé pour {url} dans la section 'Parameters'")
            return None

        headers = [header.text.strip() for header in table.find_all("th")]
        rows = [[cell.text.strip() for cell in row.find_all("td")] for row in table.find_all("tr")]
        rows = [row for row in rows if row]

        # Extraction de la section Time Co-ordinates(UT)
        time_section = soup.find("h2", string="Time Co-ordinates(UT)")
        if not time_section:
            print(f"Aucune section 'Time Co-ordinates(UT)' trouvée pour {url}")
            return None

        table = time_section.find_next("table")
        if not table:
            print(f"Aucun tableau trouvé pour {url} dans la section 'Time Co-ordinates(UT)'")
            return None

        time_rows = [[cell.text.strip() for cell in row.find_all("td")] for row in table.find_all("tr")]
        time_rows = [row for row in time_rows if row]

        # Extraction de la section Spatial Co-ordinates(UT)
        spatial_section = soup.find("h2", string="Spatial Co-ordinates")
        if not time_section:
            print(f"Aucune section 'Spatial Co-ordinates' trouvée pour {url}")
            return None

        table = spatial_section.find_next("table")
        if not table:
            print(f"Aucun tableau trouvé pour {url} dans la section 'Spatial Co-ordinates'")
            return None

        spatial_rows = [[cell.text.strip() for cell in row.find_all("td")] for row in table.find_all("tr")]
        spatial_rows = [row for row in spatial_rows if row]

        # Extraction de la section narrative documents
        # Stroker tout le texte contenu entre le h1 'Narrative Documents' et le <a name="data_activity">Data Activity or Cruise Information</a>

        narrative_section = soup.find("h1", string="Narrative Documents")
        if not narrative_section:
            print(f"Aucune section 'Narrative Documents' trouvée pour {url}")
            return None

        # Trouver l'élément <a name="data_activity">
        next_section = soup.find("h1", string="Project Information")
        narrative_text = ""

        if next_section:
            # Extraire tout le texte entre ces deux sections
            for element in narrative_section.find_all_next(text=True):
                if element == next_section:
                    break
                narrative_text += element.strip() + " "

        # Retourner le texte extrait dans le dictionnaire des résultats
        return {
            "parameters": {"headers": headers, "rows": rows},
            "time_coordinates": {"rows": time_rows},
            "spatial_coordinates": {"rows": spatial_rows},
            "narrative_documents": narrative_text.strip()  # Ajouter le texte de la section narrative
        }
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données pour {url}: {e}")
        return None


def fetch_page_data(value):
    url = f"{base_url}{value}/"
    return fetch_parameters_table(url)

def fetch_multiple_pages():
    all_data = []

    # Utilisation de ThreadPoolExecutor avec mise à jour de la progression
    with ThreadPoolExecutor(max_workers=20) as executor:
        with tqdm(total=len(checkbox_values), desc="Recherche des paramètres", unit="page") as progress:
            # Soumettre les tâches pour chaque valeur de checkbox
            results = {executor.submit(fetch_page_data, value): value for value in checkbox_values}
            for idx, future in enumerate(results):
                value = results[future]
                try:
                    result = future.result()
                    if result:
                        # On récupère les données des deux sections
                        parameters_data = result.get("parameters", {})
                        time_coordinates_data = result.get("time_coordinates", {})
                        spatial_coordinates_data = result.get("spatial_coordinates", {})
                        narrative_data = result.get("narrative_documents", {})
                        
                        # Ajout des données dans la liste all_data
                        all_data.append({
                            "html_number": idx + 1,  # Ajouter le numéro de page HTML
                            "url": f"{base_url}{value}/",
                            "parameters": parameters_data,  # Ajout des données Parameters
                            "time_coordinates": time_coordinates_data,  # Ajout des données Time Co-ordinates(UT)
                            "spatial_coordinates" : spatial_coordinates_data,
                            "narrative_documents" : narrative_data
                        })

                    progress.update(1)  # Mise à jour de la barre de progression

                    # Enregistrer le fichier JSON tous les 100 éléments traités
                    if (idx + 1) % 50 == 0:
                        print(f"Enregistrement des résultats après {idx + 1} pages traitées...")
                        with open("results_all_checkboxes.json", "w", encoding="utf-8") as json_file:
                            json.dump(all_data, json_file, indent=4, ensure_ascii=False)

                except Exception as e:
                    progress.write(f"Erreur pour {value}: {e}")

    print(f"Nombre total de pages contenant des données : {len(all_data)}")
    
    # Enregistrement final après la fin du traitement de toutes les pages
    with open("results_all_checkboxes.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, indent=4, ensure_ascii=False)

    return all_data

# Récupérer les données
all_results = fetch_multiple_pages()

# Sauvegarder les résultats dans un fichier JSON
with open("results_all_checkboxes.json", "w", encoding="utf-8") as json_file:
    json.dump(all_results, json_file, indent=4, ensure_ascii=False)

print(f"Extraction terminée. Résultats enregistrés dans 'results_all_checkboxes.json'.")
