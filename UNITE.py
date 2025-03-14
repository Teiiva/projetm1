import csv
import json

def csv_to_dict(csv_file_path):
    """
    Convertit un fichier CSV en une liste de dictionnaires.
    
    Args:
        csv_file_path (str): Chemin du fichier CSV.
        
    Returns:
        list[dict]: Liste de dictionnaires représentant chaque ligne du CSV.
    """
    data_list = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_list.append(dict(row))
    except UnicodeDecodeError:
        with open(csv_file_path, mode='r', encoding='latin-1') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_list.append(dict(row))
    return data_list

def save_dict_to_json(data_list, json_file_path):
    """
    Enregistre une liste de dictionnaires dans un fichier JSON.
    
    Args:
        data_list (list[dict]): Liste de dictionnaires.
        json_file_path (str): Chemin du fichier JSON de sortie.
    """
    with open(json_file_path, mode='w', encoding='utf-8') as file:
        json.dump(data_list, file, indent=4, ensure_ascii=False)

# Exemple d'utilisation
csv_file = "UNITE.csv"
json_file = "UNITE.json"

# Convertir CSV en dictionnaires
data = csv_to_dict(csv_file)

# Sauvegarder les dictionnaires dans un fichier JSON
save_dict_to_json(data, json_file)

print(f"Le fichier JSON a été créé avec succès : {json_file}")
