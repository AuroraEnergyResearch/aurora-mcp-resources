#!/usr/bin/env python3
"""Build one distributable zip archive for each skill in skills/."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def discover_skills(skills_dir: Path) -> list[Path]:
    skills = sorted(
        path for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )
    if not skills:
        raise SystemExit(f"No skills found in {skills_dir}")
    return skills


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    archive_path = output_dir / f"{skill_dir.name}.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(path for path in skill_dir.rglob("*") if path.is_file()):
            archive.write(path, Path(skill_dir.name) / path.relative_to(skill_dir))
    return archive_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        default=Path("dist"),
        help="Directory for generated archives (default: dist)",
    )
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parents[1]
    skills_dir = repository_root / "skills"
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = repository_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for skill_dir in discover_skills(skills_dir):
        archive_path = package_skill(skill_dir, output_dir)
        print(archive_path.relative_to(repository_root))


if __name__ == "__main__":
    main()
