import base64
import os
import requests
import sys

PAT = "..."
MAVEN_URL = "..."

if PAT == "..." or MAVEN_URL == "...":
    print("Please set the PAT and MAVEN_URL variables")
    exit(1)

ORGANIZATION = MAVEN_URL.split("/")[3]
FEED = MAVEN_URL.split("/")[6]
PROJECT = MAVEN_URL.split("/")[4]
OUTPUT = "output"

FILTERS = sys.argv[1:]

print(f"ORGANIZATION: {ORGANIZATION}")
print(f"FEED: {FEED}")
print(f"PROJECT: {PROJECT}")

base64_pat = base64.b64encode(f":{PAT}".encode("ascii")).decode("ascii")


def download(url, outname):
    response = requests.get(
        download_url, headers={"Authorization": f"Basic {base64_pat}"}
    )
    if response.status_code == 200:
        with open(os.path.join(OUTPUT, outname), "wb") as f:
            f.write(response.content)
        print(f"Downloaded {package_name} version {version_name} to {outname}")
    else:
        print(
            f"Failed to download {package_name} version {version_name} from {download_url}"
        )
        print(response.text)


def do_download(protocol):
    if FILTERS == [] or protocol in FILTERS:
        return True
    return False


if not os.path.exists(OUTPUT):
    os.makedirs(OUTPUT)

artifacts_url = f"https://feeds.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/Feeds/{FEED}/packages?api-version=7.1-preview.1"
response = requests.get(artifacts_url, headers={"Authorization": f"Basic {base64_pat}"})
packages = response.json()

download_queue = []

for package in packages["value"]:
    package_name = package["name"]
    versions_url = f"https://feeds.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/feeds/{FEED}/packages/{package['id']}/versions?api-version=7.1-preview.1"
    versions_response = requests.get(
        versions_url, headers={"Authorization": f"Basic {base64_pat}"}
    )
    versions = versions_response.json().get("value", [])
    protocol = package["protocolType"].lower()

    if not do_download(protocol):
        continue

    for version in versions:
        if (
            "directUpstreamSourceId" in version
            and version["directUpstreamSourceId"]
            != "00000000-0000-0000-0000-000000000000"
        ):
            print(
                f"Skipping {package_name} version {version['version']} as it is external"
            )
            continue
        version_name = version["version"]

        if protocol == "maven":
            groupId = package_name.split(":")[0]
            artifactId = package_name.split(":")[1]

            for ext in ["pom", "jar"]:
                fileName = f"{artifactId}-{version_name}.{ext}"
                download_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/feeds/{FEED}/maven/{groupId}/{artifactId}/{version_name}/{fileName}/content?api-version=7.1-preview.1"
                outname = f"{groupId}/{artifactId}-{version_name}.{ext}"
                if not os.path.exists(os.path.join(OUTPUT, groupId)):
                    os.makedirs(os.path.join(OUTPUT, groupId))
                download_queue.append((download_url, outname))
        elif protocol == "npm":
            for ext in ["tgz"]:
                fileName = f"{package_name}-{version_name}.{ext}"
                download_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/packaging/feeds/{FEED}/npm/packages/{package_name}/versions/{version_name}/content?api-version=7.1-preview.1"
                outname = f"npm/{package_name}-{version_name}.{ext}"
                if not os.path.exists(os.path.join(OUTPUT, "npm")):
                    os.makedirs(os.path.join(OUTPUT, "npm"))
                download_queue.append((download_url, outname))
        else:
            print(
                f"Skipping unknown protocol {protocol} for {package_name} version {version_name}"
            )

for i, (download_url, outname) in enumerate(download_queue):
    download(download_url, outname)
    progress = (i + 1) / len(urls) * 100
    print(
        f'\rProgress: [{"#" * int(progress // 4)}{" " * (25 - int(progress // 4))}] {int(progress)}%',
        end="\r",
    )
