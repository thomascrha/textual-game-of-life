#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

def validate_version(version):
    """Validate that the version string follows semantic versioning format."""
    pattern = r"^\d+\.\d+\.\d+$"
    if not re.match(pattern, version):
        raise ValueError(f"Version must follow format X.Y.Z (e.g., 1.0.0), got {version}")
    return version

def update_pyproject_toml(file_path, new_version):
    """Update version in pyproject.toml file."""
    with open(file_path, 'r') as file:
        content = file.read()

    # Update version in pyproject.toml - use a function for replacement to avoid backreference issues
    def replace_version(match):
        return f'{match.group(1)}{new_version}"'

    updated_content = re.sub(
        r'(version\s*=\s*")[^"]+"',
        replace_version,
        content
    )

    if content == updated_content:
        print(f"⚠️  No version change detected in {file_path}")
        return False

    with open(file_path, 'w') as file:
        file.write(updated_content)

    print(f"✅ Updated version in {file_path} to {new_version}")
    return True

def update_tui_py(file_path, new_version):
    """Update version in tui.py file."""
    with open(file_path, 'r') as file:
        content = file.read()

    # Update version in the VERSION class constant - use a function for replacement to avoid backreference issues
    def replace_version(match):
        return f'{match.group(1)}{new_version}"'

    updated_content = re.sub(
        r'(VERSION\s*=\s*")[^"]+"',
        replace_version,
        content
    )

    if content == updated_content:
        print(f"⚠️  No version change detected in {file_path}")
        return False

    with open(file_path, 'w') as file:
        file.write(updated_content)

    print(f"✅ Updated version in {file_path} to {new_version}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Update version across project files")
    parser.add_argument("version", help="New version number (format: X.Y.Z)")
    args = parser.parse_args()

    try:
        new_version = validate_version(args.version)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Define paths to files that need updating
    project_root = Path(__file__).parent
    pyproject_path = project_root / "pyproject.toml"
    tui_path = project_root / "src" / "textual_game_of_life" / "tui.py"

    # Check that files exist
    missing_files = []
    if not pyproject_path.exists():
        missing_files.append(str(pyproject_path))
    if not tui_path.exists():
        missing_files.append(str(tui_path))

    if missing_files:
        print(f"Error: Could not find the following files:", file=sys.stderr)
        for file in missing_files:
            print(f"  - {file}", file=sys.stderr)
        return 1

    # Update the files
    updated = []
    if update_pyproject_toml(pyproject_path, new_version):
        updated.append(str(pyproject_path))
    if update_tui_py(tui_path, new_version):
        updated.append(str(tui_path))

    if not updated:
        print("No files were updated. Version might already be set correctly.")
        return 0

    print(f"\n🎉 Successfully updated version to {new_version} in {len(updated)} files")
    print("\nNext steps:")
    print("1. Review changes with 'git diff'")
    print("2. Commit changes: 'git commit -am \"Bump version to " + new_version + "\"'")
    print("3. Create a tag: 'git tag v" + new_version + "'")
    print("4. Push changes and tags: 'git push && git push --tags'")

    return 0

if __name__ == "__main__":
    sys.exit(main())

