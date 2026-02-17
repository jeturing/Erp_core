#!/usr/bin/env python3
"""
Fix unterminated string literals in Odoo __manifest__.py files.

This script identifies and fixes manifest files that have multi-line string values
using single quotes instead of triple quotes. It handles various edge cases and
validates the fixed syntax.

Author: Claude Code Assistant
Date: 2026-02-16
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
import tempfile


class ManifestFixer:
    """Fixes unterminated string literals in __manifest__.py files."""

    def __init__(self, base_dir: str, verbose: bool = True):
        """
        Initialize the manifest fixer.

        Args:
            base_dir: Base directory containing addon modules
            verbose: Print detailed progress information
        """
        self.base_dir = Path(base_dir)
        self.verbose = verbose
        self.backup_dir = self.base_dir.parent / "manifest_backups"
        self.results = {
            "fixed": [],
            "already_valid": [],
            "failed": [],
            "total": 0
        }

    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def find_manifest_files(self) -> List[Path]:
        """Find all __manifest__.py files in the base directory."""
        manifest_files = list(self.base_dir.rglob("__manifest__.py"))
        self.log(f"Found {len(manifest_files)} manifest files")
        return manifest_files

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of the original file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file
        """
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create a backup path that preserves the directory structure
        relative_path = file_path.relative_to(self.base_dir)
        backup_path = self.backup_dir / relative_path.with_suffix(".py.bak")
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, backup_path)
        return backup_path

    def is_valid_syntax(self, content: str) -> bool:
        """
        Check if the content has valid Python syntax.

        Args:
            content: Python code to validate

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            compile(content, "<string>", "exec")
            return True
        except SyntaxError:
            return False

    def fix_manifest_content(self, content: str) -> Tuple[str, bool]:
        """
        Fix unterminated string literals in manifest content.

        This function identifies single-quoted strings that span multiple lines
        and converts them to triple-quoted strings.

        Args:
            content: The manifest file content

        Returns:
            Tuple of (fixed_content, was_modified)
        """
        if self.is_valid_syntax(content):
            return content, False

        lines = content.split("\n")
        fixed_lines = []
        i = 0
        modified = False

        while i < len(lines):
            line = lines[i]

            # Check if this line has a pattern: 'key': 'value
            # Match lines that have 'key': ' pattern
            match = re.match(r"^(\s*)'([\w_]+)':\s*'", line)

            if match:
                indent = match.group(1)
                key = match.group(2)

                # Get everything after 'key': '
                key_pattern_end = match.end()
                start_value = line[key_pattern_end:]

                # Check if the quote is closed on the same line
                # by looking for an unescaped quote after the start position
                has_closing_on_same_line = False
                for j in range(len(start_value)):
                    if start_value[j] == "'":
                        if j == 0 or start_value[j - 1] != "\\":
                            has_closing_on_same_line = True
                            break

                if not has_closing_on_same_line and i + 1 < len(lines):
                    # Multi-line string - collect all lines until closing quote
                    full_value_lines = [start_value]
                    j = i + 1
                    found_closing = False
                    closing_quote_pos = -1

                    while j < len(lines):
                        next_line = lines[j]

                        # Find if there's an unescaped single quote
                        pos = 0
                        while pos < len(next_line):
                            if next_line[pos] == "'":
                                # Check if it's escaped
                                if pos == 0 or next_line[pos - 1] != "\\":
                                    # Found closing quote
                                    full_value_lines.append(next_line[:pos])
                                    closing_quote_pos = pos
                                    found_closing = True
                                    break
                            pos += 1

                        if found_closing:
                            break
                        else:
                            full_value_lines.append(next_line)
                            j += 1

                    if found_closing:
                        # Reconstruct with triple quotes
                        value_content = "\n".join(full_value_lines)
                        rest_of_closing_line = lines[j][closing_quote_pos + 1:]

                        # Use triple quotes for the value, keeping original key quotes
                        fixed_line = f"{indent}'{key}': \"\"\"{value_content}\"\"\"{rest_of_closing_line}"
                        fixed_lines.append(fixed_line)

                        modified = True
                        i = j + 1
                        continue

            fixed_lines.append(line)
            i += 1

        fixed_content = "\n".join(fixed_lines)

        # Validate the fix
        if not self.is_valid_syntax(fixed_content):
            # If not valid, return original
            return content, False

        return fixed_content, modified

    def fix_manifest_aggressive(self, content: str) -> Tuple[str, bool]:
        """
        More aggressive fix using a smarter line-by-line parser.

        This method handles cases where the string value contains escaped quotes
        or other quote characters.

        Args:
            content: The manifest file content

        Returns:
            Tuple of (fixed_content, was_modified)
        """
        if self.is_valid_syntax(content):
            return content, False

        original_content = content
        lines = content.split("\n")
        fixed_lines = []
        i = 0
        modified = False

        while i < len(lines):
            line = lines[i]

            # Look for pattern: 'key': 'value (with possible escaped quotes inside)
            match = re.match(r"^(\s*)'([\w_]+)':\s*'(.*)$", line)

            if match:
                indent = match.group(1)
                key = match.group(2)
                start_value = match.group(3)

                # Check if this looks like a multi-line string that should be fixed
                # (closing quote not on same line)
                j = i + 1
                value_lines = [start_value]
                found_closing = False

                # Look for the closing quote, allowing for escaped quotes
                while j < len(lines):
                    next_line = lines[j]

                    # Look for an unescaped single quote
                    for k, char in enumerate(next_line):
                        if char == "'" and (k == 0 or next_line[k - 1] != "\\"):
                            # This is likely the closing quote
                            value_lines.append(next_line[:k])
                            rest = next_line[k + 1:]

                            # Convert to triple quotes
                            value_content = "\n".join(value_lines)
                            fixed_line = f"{indent}'{key}': \"\"\"{value_content}\"\"\"{rest}"
                            fixed_lines.append(fixed_line)

                            found_closing = True
                            modified = True
                            i = j + 1
                            break

                    if not found_closing:
                        value_lines.append(next_line)
                        j += 1

                if found_closing:
                    continue

            fixed_lines.append(line)
            i += 1

        fixed_content = "\n".join(fixed_lines)

        if fixed_content == original_content:
            return content, False

        # Validate the result
        if self.is_valid_syntax(fixed_content):
            return fixed_content, True

        return original_content, False

    def fix_manifest_file(self, file_path: Path) -> bool:
        """
        Fix a single manifest file.

        Args:
            file_path: Path to the manifest file

        Returns:
            True if file was successfully fixed, False otherwise
        """
        try:
            # Read the original content
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # Check if already valid
            if self.is_valid_syntax(original_content):
                self.log(f"✓ {file_path.parent.name}: Already valid syntax")
                return True

            # Create backup before modifying
            backup_path = self.create_backup(file_path)
            self.log(f"  Backup created: {backup_path}")

            # Try to fix the content
            fixed_content, modified = self.fix_manifest_content(original_content)

            if not modified:
                # Try aggressive approach
                fixed_content, modified = self.fix_manifest_aggressive(original_content)

            if not modified:
                self.log(f"✗ {file_path.parent.name}: Could not fix automatically")
                return False

            # Validate the fixed content
            if not self.is_valid_syntax(fixed_content):
                self.log(f"✗ {file_path.parent.name}: Fixed content still has syntax errors")
                return False

            # Write the fixed content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            self.log(f"✓ {file_path.parent.name}: Fixed and validated")
            return True

        except Exception as e:
            self.log(f"✗ {file_path.parent.name}: Error - {str(e)}")
            return False

    def run(self) -> Dict[str, any]:
        """
        Run the manifest fixing process on all files.

        Returns:
            Dictionary with results summary
        """
        self.log(f"\nStarting manifest file fixes in: {self.base_dir}\n")

        manifest_files = self.find_manifest_files()
        self.results["total"] = len(manifest_files)

        for file_path in sorted(manifest_files):
            if self.fix_manifest_file(file_path):
                # Check if it was already valid or was fixed
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if self.is_valid_syntax(content):
                    # Check if backup was created (means we fixed it)
                    backup_path = (
                        self.backup_dir
                        / file_path.relative_to(self.base_dir).with_suffix(".py.bak")
                    )
                    if backup_path.exists():
                        self.results["fixed"].append(str(file_path))
                    else:
                        self.results["already_valid"].append(str(file_path))
            else:
                self.results["failed"].append(str(file_path))

        return self.print_summary()

    def print_summary(self) -> Dict[str, any]:
        """Print and return the summary of results."""
        self.log("\n" + "=" * 70)
        self.log("MANIFEST FIX SUMMARY")
        self.log("=" * 70)
        self.log(f"Total files processed: {self.results['total']}")
        self.log(f"Files fixed: {len(self.results['fixed'])}")
        self.log(f"Already valid: {len(self.results['already_valid'])}")
        self.log(f"Failed to fix: {len(self.results['failed'])}")

        if self.results["fixed"]:
            self.log("\nFixed files:")
            for file_path in sorted(self.results["fixed"]):
                self.log(f"  • {Path(file_path).parent.name}")

        if self.results["failed"]:
            self.log("\nFiles that still have issues:")
            for file_path in sorted(self.results["failed"]):
                self.log(f"  • {Path(file_path).parent.name}")

        if self.results["already_valid"]:
            self.log(f"\nAlready valid files: {len(self.results['already_valid'])}")

        self.log("\n" + "=" * 70)
        self.log(
            f"Backup files saved to: {self.backup_dir}\n"
        )

        return self.results


def main():
    """Main entry point."""
    base_dir = "/Users/owner/Desktop/jcore/Erp_core/extra-addons/V19"

    if not Path(base_dir).exists():
        print(f"Error: Directory does not exist: {base_dir}")
        sys.exit(1)

    fixer = ManifestFixer(base_dir, verbose=True)
    results = fixer.run()

    # Exit with error code if there are failures
    if results["failed"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
