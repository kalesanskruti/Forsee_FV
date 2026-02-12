# Create local directory structure for Forsee Intelligence Software
$directories = @(
    "d:\Forsee_Final\Forsee\datasets\nasa_cmapss",
    "d:\Forsee_Final\Forsee\datasets\ai4i_2020",
    "d:\Forsee_Final\Forsee\datasets\scania",
    "d:\Forsee_Final\Forsee\datasets\metropt",
    "d:\Forsee_Final\Forsee\datasets\mimii",
    "d:\Forsee_Final\Forsee\datasets\phm_repo",
    "d:\Forsee_Final\Forsee\ml\models\rul",
    "d:\Forsee_Final\Forsee\ml\models\precursor",
    "d:\Forsee_Final\Forsee\ml\models\health_index",
    "d:\Forsee_Final\Forsee\ml\models\clustering",
    "d:\Forsee_Final\Forsee\ml\models\drift"
)

foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir"
    } else {
        Write-Host "Exists: $dir"
    }
}

Write-Host "Local environment setup complete."
