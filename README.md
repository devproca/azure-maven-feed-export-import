# Azure Artifacts Export & Import

## Personal Access Token

1. Create a Personal Access Token in Azure DevOps
2. Use the scope `Packaging (read)` for export, or `Packaging (read and write)` for import
3. Replace the token in the file `export.py` or `import.py`

## Maven URL

1. Open the feed in Azure DevOps
2. Click `Connect to feed`
3. Select `Maven`
4. Copy the URL from the XML snippet
5. Replace the URL in the file `export.py` or `import.py`

Format: `https://pkgs.dev.azure.com/{org}/{project}/_packaging/{feed}/maven/v1`

## Running the Script

```bash
python3 export.py # Export npm and maven
python3 export.py npm # Export npm packages
python3 export.py maven # Export maven packages

python3 import.py npm # Import npm packages
python3 import.py maven # Import maven packages
```
