import requests
import glob
import os
import base64

PAT = "..."  # Personal Access Token for the destination feed

MAVEN_URL = "https://pkgs.dev.azure.com/GoSCSITDAMS/f0e2b52f-1224-44d6-b0ce-58508ab5f2a4/_packaging/JSS_Artifact_Feed/maven/v1"

# Variables
ORGANIZATION = MAVEN_URL.split("/")[3]
FEED = MAVEN_URL.split("/")[8]
PROJECT = MAVEN_URL.split("/")[7]
OUTPUT = "output"

if PAT == "..." or MAVEN_URL == "...":
    print("Please set the PAT and MAVEN_URL variables")
    exit(1)

# Base64 encode the PAT
destination_base64_pat = base64.b64encode(f":{PAT}".encode("ascii")).decode("ascii")

# Directory where the downloaded packages are stored

# Get the list of all .jar files in the output directory
packages = glob.glob(os.path.join(OUTPUT, "*/*-*.jar"))

# Upload each package to the destination feed
for package_path in packages:
    # Extract groupId, artifactId, and version from the file path
    _, groupId, artifact_file = package_path.split(os.sep)
    artifactId, version = artifact_file.rsplit('-', 1)
    version = version.rstrip('.jar')

    print(f"Uploading {artifactId} version {version} of group {groupId}...")

    fileName = f"{artifactId}-{version}.jar"
    upload_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_packaging/{FEED}/maven/v1/{groupId}/{artifactId}/{version}/{fileName}"

    with open(package_path, 'rb') as f:
        upload_response = requests.put(upload_url, headers={"Authorization": f"Basic {destination_base64_pat}", "Content-Type": "application/octet-stream"}, data=f)

    if upload_response.status_code == 201:
        print(f"Uploaded {artifactId} version {version} of group {groupId}")
    else:
        print(f"Failed to upload {artifactId} version {version} of group {groupId}. Status code: {upload_response.status_code}, Response: {upload_response.text}")
