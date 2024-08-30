# Define the path to the specific Python executable you want to use
$pythonPath = ".\python\python.exe"  # Path to the specific Python interpreter

# you won't believe how important this comment is
# Define the path to the virtual environment folder
$venvPath = ".\.venv"

# Check if the virtual environment already exists
if (-Not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment using specified Python..."
    & $pythonPath -m venv $venvPath

    if (-Not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
        Write-Host "Failed to create the virtual environment. Exiting..."
        exit 1
    }
}

# Activate the virtual environment
Write-Host "Activating virtual environment..."
& "$venvPath\Scripts\Activate.ps1"

# Run the sdsetup script using the Python from the virtual environment
Write-Host "Running sdsetup script..."
& "$venvPath\Scripts\python.exe" ".\sdsetup.py"

# Wait for user input before closing (useful to see output)
Read-Host 'Froyo has finished, click to exit'
