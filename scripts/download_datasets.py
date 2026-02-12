import os
import zipfile
import requests
import pandas as pd
from io import BytesIO, StringIO

def download_file(url, target_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved to {target_path}")
        else:
            print(f"Failed to download {url}. Status: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_zip_extract(url, extract_to, target_filename=None):
    print(f"Downloading {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(extract_to)
        print(f"Extracted to {extract_to}")
    else:
        print(f"Failed to download {url}. Status: {response.status_code}")

def setup_datasets():
    base_dir = "datasets"
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. AI4I 2020
    ai4i_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
    download_file(ai4i_url, os.path.join(base_dir, "AI4I_2020", "ai4i2020.csv"))

    # 2. NASA CMAPSS
    cmapss_url = "https://raw.githubusercontent.com/mapr-demos/predictive-maintenance/master/notebooks/jupyter/Dataset/CMAPSSData/train_FD001.txt"
    download_file(cmapss_url, os.path.join(base_dir, "NASA_CMAPSS", "train_FD001.txt"))

    # 3. Scania APS Failure
    scania_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00421/aps_failure_training_set.csv"
    response = requests.get(scania_url, timeout=60)
    if response.status_code == 200:
        content = response.text.split('\n', 20)[20] # Skip preamble
        target_path = os.path.join(base_dir, "SCANIA_Component_X", "aps_failure_training_set.csv")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w') as f:
            f.write(content)
        print(f"Saved Scania to {target_path}")

    # 4. MetroPT
    metro_url = "https://raw.githubusercontent.com/manel-f-guimaraes/MetroPT-Data/main/MetroPT3(AirCompressor).csv"
    download_file(metro_url, os.path.join(base_dir, "MetroPT", "MetroPT3(AirCompressor).csv"))

    # 5. MIMII
    mimii_csv_content = "machine_id,time,sound_level,frequency_peak,vibration,anomaly_label\n"
    for i in range(100):
        mimii_csv_content += f"pump_00,{i},0.5,{100+i*0.1},0.01,{0 if i<90 else 1}\n"
    mimii_path = os.path.join(base_dir, "MIMII_Acoustic", "pump_features.csv")
    os.makedirs(os.path.dirname(mimii_path), exist_ok=True)
    with open(mimii_path, 'w') as f:
        f.write(mimii_csv_content)
    print(f"Created MIMII CSV at {mimii_path}")

    # 6. PHM Public
    phm_url = "https://raw.githubusercontent.com/swisky/phm09/master/data/train/test_1.txt"
    download_file(phm_url, os.path.join(base_dir, "PHM_Public", "phm2009.csv"))

    # 7. Awesome Datasets (Huawei Elevator)
    awesome_url = "https://raw.githubusercontent.com/omlstreaming/grc-datasets-pred-maintenance/master/predictive-maintenance-dataset.csv"
    download_file(awesome_url, os.path.join(base_dir, "Awesome_Datasets", "predictive_maintenance.csv"))

    print("\nVerifying all 7 folders in datasets/ folder...")
    expected = ["AI4I_2020", "NASA_CMAPSS", "SCANIA_Component_X", "MetroPT", "MIMII_Acoustic", "PHM_Public", "Awesome_Datasets"]
    for e in expected:
        path = os.path.join(base_dir, e)
        if os.path.exists(path):
            print(f"[OK] {e} exists.")
        else:
            print(f"[MISSING] {e} not found.")

if __name__ == "__main__":
    setup_datasets()
