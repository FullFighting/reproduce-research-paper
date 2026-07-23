#!/usr/bin/env python3
"""Build checksums, an SPDX SBOM, and unsigned release provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout.strip()


def spdx_id(path: str) -> str:
    return "SPDXRef-File-" + hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve()
    archive = args.archive.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    destination_archive = output / archive.name
    if archive != destination_archive:
        shutil.copy2(archive, destination_archive)
    commit = git(repository, "rev-parse", "HEAD")
    version = (repository / "VERSION").read_text(encoding="utf-8").strip()
    paths = [
        item
        for item in git(repository, "ls-files", "-z").split("\0")
        if item
    ]
    files = []
    for relative in paths:
        path = repository / relative
        if not path.is_file():
            continue
        files.append(
            {
                "SPDXID": spdx_id(relative),
                "fileName": "./" + Path(relative).as_posix(),
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": sha256(path)}
                ],
                "licenseConcluded": "NOASSERTION",
                "copyrightText": "NOASSERTION",
            }
        )
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    package_id = "SPDXRef-Package-reproduce-research-paper"
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"reproduce-research-paper-{version}",
        "documentNamespace": (
            "https://github.com/FullFighting/reproduce-research-paper/"
            f"spdx/{commit}"
        ),
        "creationInfo": {
            "created": created,
            "creators": ["Tool: reproduce-research-paper-build_release_artifacts-1.0"],
        },
        "packages": [
            {
                "name": "reproduce-research-paper",
                "SPDXID": package_id,
                "versionInfo": version,
                "downloadLocation": (
                    "https://github.com/FullFighting/reproduce-research-paper"
                ),
                "filesAnalyzed": True,
                "licenseConcluded": "MIT",
                "licenseDeclared": "MIT",
                "copyrightText": "NOASSERTION",
            }
        ],
        "files": files,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": package_id,
            },
            *[
                {
                    "spdxElementId": package_id,
                    "relationshipType": "CONTAINS",
                    "relatedSpdxElement": item["SPDXID"],
                }
                for item in files
            ],
        ],
    }
    sbom_path = output / "sbom.spdx.json"
    sbom_path.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    provenance = {
        "schema_version": 1,
        "predicate_type": "https://slsa.dev/provenance/v1",
        "unsigned_notice": (
            "This local JSON is an integrity record, not a signature. "
            "GitHub artifact attestation is generated separately by CI."
        ),
        "subject": {
            "name": destination_archive.name,
            "sha256": sha256(destination_archive),
        },
        "source": {
            "repository": "https://github.com/FullFighting/reproduce-research-paper",
            "git_commit": commit,
            "version": version,
        },
        "builder": {
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "generated_at": created,
    }
    provenance_path = output / "provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    checksum_paths = [destination_archive, sbom_path, provenance_path]
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "archive": destination_archive.name,
                "commit": commit,
                "file_count": len(files),
                "artifacts": [path.name for path in checksum_paths]
                + ["SHA256SUMS"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
