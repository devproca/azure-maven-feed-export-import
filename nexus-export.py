import requests
import os
import json
import urllib.parse

SOURCE_SERVER = "..."
SOURCE_USER = "..."
SOURCE_PASS = "..."

if SOURCE_SERVER == "..." or SOURCE_USER == "..." or SOURCE_PASS == "...":
    print("ERROR: Please provide Nexus credentials")
    exit(1)

SOURCE_REPOS = {
    "maven-public": "",
    "npm-hosted": "",
}

EXTS = ["jar", "pom", "tgz"]


def download_repo(sourceRepo, sourceFolder):
    outputFile = f"{sourceRepo}-artifacts.txt"

    if os.path.exists(outputFile):
        os.remove(outputFile)

    url = f"{SOURCE_SERVER}/service/rest/v1/assets?repository={sourceRepo}"
    if sourceRepo == "maven-public":
        url = f"{SOURCE_SERVER}/service/rest/v1/search/assets?repository={sourceRepo}&maven.extension=jar"
    contToken = "initial"
    while contToken:
        if contToken != "initial":
            url = f"{SOURCE_SERVER}/service/rest/v1/assets?continuationToken={contToken}&repository={sourceRepo}"
            if sourceRepo == "maven-public":
                url = f"{SOURCE_SERVER}/service/rest/v1/search/assets?continuationToken={contToken}&repository={sourceRepo}&maven.extension=jar"
        response = requests.get(
            url, auth=(SOURCE_USER, SOURCE_PASS), headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            print(
                f"ERROR: Failed to get assets from repository: {sourceRepo} with error code: {response.status_code}"
            )
            break
        response = response.json()
        artifacts = [item["downloadUrl"] for item in response["items"]]
        with open(outputFile, "a") as out:
            for line in artifacts:
                if line.endswith(tuple(EXTS)) and (
                    sourceFolder in line or sourceFolder == ""
                ):
                    out.write(f"{line}\n")
                    if line.endswith(".jar"):
                        out.write(f'{line.replace(".jar", ".pom")}\n')
        contToken = response.get("continuationToken")
        print(f"Collected {len(artifacts)} artifacts")

    print("Downloading artifacts...")
    with open(outputFile, "r") as f:
        urls = [line.strip() for line in f]
    for i, url in enumerate(urls):
        path = url.split("/", 3)[-1]
        dir = f"{sourceRepo}/{os.path.dirname(path)}"
        os.makedirs(dir, exist_ok=True)
        url = urllib.parse.quote(url, safe=":/")
        response = requests.get(url, auth=(SOURCE_USER, SOURCE_PASS))
        if response.status_code == 200:
            with open(os.path.join(dir, os.path.basename(url)), "wb") as f:
                f.write(response.content)
            print(f"Downloaded artifact: {url}")
        else:
            print(
                f"ERROR: Failed to download artifact: {url} with error code: {response.status_code}"
            )
            print(response.text)
        progress = (i + 1) / len(urls) * 100
        print(
            f'\rProgress: [{"#" * int(progress // 4)}{" " * (25 - int(progress // 4))}] {int(progress)}%',
            end="\r",
        )


for repo in SOURCE_REPOS:
    download_repo(repo, SOURCE_REPOS[repo])
