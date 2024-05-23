import os
import requests

import base64

PAT = "..."

MAVEN_URL = "..."

# Variables
ORGANIZATION = MAVEN_URL.split("/")[3]
FEED = MAVEN_URL.split("/")[8]
PROJECT = MAVEN_URL.split("/")[7]
OUTPUT = "output"

if PAT == "..." or MAVEN_URL == "...":
    print("Please set the PAT and MAVEN_URL variables")
    exit(1)

# Base64 encode the PAT
base64_pat = base64.b64encode(f":{PAT}".encode("ascii")).decode("ascii")

# Create the output directory if it doesn't exist
if not os.path.exists(OUTPUT):
    os.makedirs(OUTPUT)

# Get the list of artifacts in the feed
artifacts_url = f"https://feeds.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/Feeds/{FEED}/packages?api-version=7.1-preview.1"
response = requests.get(artifacts_url, headers={"Authorization": f"Basic {base64_pat}"})
packages = response.json()

# Download each artifact
for package in packages['value']:
    package_name = package['name']
    versions_url = f"https://feeds.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/feeds/{FEED}/packages/{package['id']}/versions?api-version=7.1-preview.1"
    versions_response = requests.get(versions_url, headers={"Authorization": f"Basic {base64_pat}"})
    versions = versions_response.json().get('value', [])

    for version in versions:
        if 'directUpstreamSourceId' in version and version['directUpstreamSourceId'] != '00000000-0000-0000-0000-000000000000':
            print(f"Skipping {package_name} version {version['version']} as it is external")
            continue
        version_name = version['version']
        groupId = package_name.split(":")[0]
        artifactId = package_name.split(":")[1]
        fileName = f"{artifactId}-{version_name}.jar"
        download_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/feeds/{FEED}/maven/{groupId}/{artifactId}/{version_name}/{fileName}/content?api-version=7.1-preview.1"
        outname = f"{groupId}/{artifactId}-{version_name}.jar"
        if not os.path.exists(os.path.join(OUTPUT, groupId)):
            os.makedirs(os.path.join(OUTPUT, groupId))

        print(f"Downloading {package_name} version {version_name} from {download_url}")
        response = requests.get(download_url, headers={"Authorization": f"Basic {base64_pat}"})
        if response.status_code == 200:
            with open(os.path.join(OUTPUT, outname), "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed to download {package_name} version {version_name} from {download_url}")
            print(response.text)
