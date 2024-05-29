import base64
import glob
import hashlib
import json
import os
import requests
import sys
import urllib.parse

PAT = "..."
MAVEN_URL = "..."

if len(sys.argv) < 2:
    print("Usage: python import.py (maven|npm)")
    exit(1)

REPO = sys.argv[1]

if REPO not in ["maven", "npm"]:
    print("REPO must be either maven or npm, passed as the first argument")
    exit(1)

if PAT == "..." or MAVEN_URL == "...":
    print("Please set the PAT and MAVEN_URL variables")
    exit(1)

ORGANIZATION = MAVEN_URL.split("/")[3]
FEED = MAVEN_URL.split("/")[6]
PROJECT = MAVEN_URL.split("/")[4]
OUTPUT = "output"

print(f"ORGANIZATION: {ORGANIZATION}")
print(f"FEED: {FEED}")
print(f"PROJECT: {PROJECT}")


def build_npm_metadata(registry, manifest, tarball_data):
    default_tag = "latest"
    algorithms = ["sha512"]

    root = {
        "_id": manifest["name"],
        "name": manifest["name"],
        "description": manifest["description"],
        "dist-tags": {},
        "versions": {},
        "access": "public",
    }

    root["versions"][manifest["version"]] = manifest
    tag = manifest.get("tag", default_tag)
    root["dist-tags"][tag] = manifest["version"]

    tarball_name = f"{manifest['name']}-{manifest['version']}.tgz"
    tarball_uri = f"{manifest['name']}/-/{tarball_name}"

    sha1 = hashlib.sha1(tarball_data).hexdigest()
    sha512 = hashlib.sha512(tarball_data).hexdigest()
    integrity = {
        "sha1": sha1,
        "sha512": sha512,
    }

    manifest["_id"] = f"{manifest['name']}@{manifest['version']}"
    manifest["dist"] = manifest.get("dist", {})
    manifest["dist"]["integrity"] = integrity["sha512"]
    manifest["dist"]["shasum"] = integrity["sha1"]
    manifest["dist"]["tarball"] = urllib.parse.urljoin(registry, tarball_uri).replace(
        "https://", "http://"
    )

    root["_attachments"] = {}
    root["_attachments"][tarball_name] = {
        "content_type": "application/octet-stream",
        "data": base64.b64encode(tarball_data).decode(),
        "length": len(tarball_data),
    }

    return root


destination_base64_pat = base64.b64encode(f":{PAT}".encode("ascii")).decode("ascii")

exts = []
if REPO == "maven":
    exts = ["jar", "pom"]
else:
    exts = ["tgz"]

for ext in exts:
    packages = glob.glob(os.path.join(OUTPUT, f"*/*-*.{ext}"))
    for i, package_path in enumerate(packages):
        _, groupId, artifact_file = package_path.split(os.sep)
        artifactId, version = artifact_file.rsplit("-", 1)
        version = version.rstrip(f".{ext}")

        parent_folder = groupId
        if groupId == "npm":
            groupId = "@".join(artifactId.split("@")[:-1])
            artifactId = artifactId.split("@")[-1]
            parent_folder = "npm"
        else:
            groupId = groupId + "/"

        fileName = f"{artifactId}-{version}.{ext}"
        if REPO == "npm":
            upload_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_packaging/{FEED}/npm/registry/{groupId}{artifactId}"
            package_path = os.path.join(OUTPUT, parent_folder, fileName)
            with open(package_path, "rb") as f:
                body = build_npm_metadata(
                    f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_packaging/{FEED}/npm/registry",
                    {
                        "name": f"{groupId}{artifactId}",
                        "version": version,
                        "description": "",
                    },
                    f.read(),
                )
                upload_response = requests.put(
                    upload_url,
                    headers={
                        "Authorization": f"Basic {destination_base64_pat}",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps(body),
                )
        else:
            upload_url = f"https://pkgs.dev.azure.com/{ORGANIZATION}/{PROJECT}/_packaging/{FEED}/maven/v1/{groupId}/{artifactId}/{version}/{fileName}"
            package_path = os.path.join(OUTPUT, parent_folder, fileName)
            with open(package_path, "rb") as f:
                upload_response = requests.put(
                    upload_url,
                    headers={
                        "Authorization": f"Basic {destination_base64_pat}",
                        "Content-Type": "application/octet-stream",
                    },
                    data=f,
                )

        if upload_response.status_code == 202:
            print(f"Uploaded {artifactId} version {version} of group {groupId}")
        elif upload_response.status_code == 409:
            print(
                f"Skipping {artifactId} version {version} of group {groupId} as it already exists"
            )
        else:
            print(
                f"Failed to upload {artifactId} version {version} of group {groupId}. Status code: {upload_response.status_code}, Response: {upload_response.text}"
            )
        progress = (i + 1) / len(packages) * 100
        print(
            f'\rProgress: [{"#" * int(progress // 4)}{" " * (25 - int(progress // 4))}] {int(progress)}%',
            end="\r",
        )
