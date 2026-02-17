#!/usr/bin/env python3
"""
Fix manifest syntax errors in migrated Odoo modules.
Specifically fixes unterminated string literals and other manifest issues.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

class ManifestFixer:
    """Fix syntax errors in __manifest__.py files"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.v19_dir = self.base_dir / "extra-addons" / "V19"
        self.v17_dir = self.base_dir / "extra-addons" / "V17"
        self.fixed_count = 0
        self.errors = []

    def get_manifest_path(self, module_name: str, version: str = "v19") -> Path:
        """Get path to module's __manifest__.py"""
        if version == "v19":
            return self.v19_dir / module_name / "__manifest__.py"
        else:
            return self.v17_dir / module_name / "__manifest__.py"

    def fix_multiline_strings(self, content: str) -> str:
        """Fix improperly formatted multi-line strings in manifest"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line has a key with a single-quoted string that spans multiple lines
            # Pattern: 'key': '...' followed by more content on next line
            match = re.match(r"(\s*)(['\"])(\w+)(['\"])\s*:\s*(['\"])(.*)$", line)

            if match and match.group(5) == "'" and not line.rstrip().endswith(("'", '"""', "'''", ",")):
                # This looks like an unclosed multi-line string
                indent = match.group(1)
                key = match.group(3)
                opening_quote = match.group(5)
                first_line_content = match.group(6)

                # Collect all lines until we find the closing quote
                accumulated_lines = [first_line_content]
                i += 1

                while i < len(lines):
                    next_line = lines[i]
                    accumulated_lines.append(next_line.rstrip())

                    # Check if this line ends the string
                    if next_line.rstrip().endswith(("',", "\"," , "',\n", '",\n')):
                        break
                    i += 1

                # Reconstruct with triple quotes
                content_str = "\n".join(accumulated_lines)
                content_str = content_str.rstrip('",\'')

                fixed_line = f"{indent}'{key}': \"\"\"\n{indent}    {content_str}\"\"\","
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

            i += 1

        return '\n'.join(fixed_lines)

    def fix_manifest(self, module_name: str) -> Tuple[bool, str]:
        """
        Fix a single manifest file.
        Returns (success, message)
        """
        manifest_path = self.get_manifest_path(module_name)

        if not manifest_path.exists():
            return False, f"Manifest not found: {manifest_path}"

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Apply fixes
            fixed_content = self.fix_multiline_strings(original_content)

            # Verify the fixed content is valid Python
            try:
                compile(fixed_content, str(manifest_path), 'exec')
            except SyntaxError as e:
                # Try alternative fix: use ast.literal_eval compatible format
                fixed_content = self._fix_with_ast_compatible_format(original_content)
                try:
                    compile(fixed_content, str(manifest_path), 'exec')
                except SyntaxError:
                    return False, f"Syntax error persists: {e}"

            # Write fixed content
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            self.fixed_count += 1
            return True, f"Fixed {module_name}"

        except Exception as e:
            error_msg = f"Error fixing {module_name}: {str(e)}"
            self.errors.append(error_msg)
            return False, error_msg

    def _fix_with_ast_compatible_format(self, content: str) -> str:
        """
        Alternative fix: reconstruct manifest with proper quote handling
        """
        lines = content.split('\n')
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for improperly split summary fields
            if "'summary'" in line or '"summary"' in line:
                match = re.match(r"(\s*)(['\"])summary(['\"])\s*:\s*(['\"])(.*)$", line)
                if match and not line.rstrip().endswith(('"""', "'''", '",', "',")):
                    indent = match.group(1)
                    quote_char = match.group(4)
                    summary_start = match.group(5)

                    # Collect lines until we find the closing quote
                    summary_lines = [summary_start]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        summary_lines.append(next_line.strip())
                        if next_line.rstrip().endswith(('",', "',")):
                            break
                        i += 1

                    # Reconstruct with proper triple quotes
                    summary_content = ' '.join(summary_lines).rstrip('",\'')
                    fixed_lines.append(f'{indent}"summary": """{summary_content}""",')
                    i += 1
                    continue

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines)

    def fix_all_modules(self, modules: List[str] = None) -> Dict:
        """
        Fix all or specified modules.
        Returns statistics dictionary.
        """
        if modules is None:
            # Find all modules in V19 directory
            modules = [d.name for d in self.v19_dir.iterdir() if d.is_dir()]

        results = {
            'total': len(modules),
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'details': {}
        }

        print(f"\n{'='*70}")
        print(f"FIXING MANIFEST SYNTAX ERRORS")
        print(f"{'='*70}")
        print(f"Total modules to check: {len(modules)}\n")

        for idx, module in enumerate(sorted(modules), 1):
            success, message = self.fix_manifest(module)

            if success:
                results['fixed'] += 1
                status = "✅ FIXED"
            else:
                results['failed'] += 1
                status = "❌ FAILED"

            results['details'][module] = {
                'success': success,
                'message': message
            }

            print(f"[{idx:3d}/{len(modules)}] {status} - {module}")

        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Total modules processed: {results['total']}")
        print(f"Successfully fixed:     {results['fixed']}")
        print(f"Failed:                 {results['failed']}")
        print(f"{'='*70}\n")

        return results

def main():
    """Main entry point"""
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/owner/Desktop/jcore/Erp_core"

    fixer = ManifestFixer(base_dir)

    # Get modules with syntax errors from validation report
    validation_report_path = Path(base_dir) / "validation_report.json"

    modules_to_fix = []
    if validation_report_path.exists():
        with open(validation_report_path, 'r') as f:
            report = json.load(f)
            modules_to_fix = [
                m['module'] for m in report.get('modules', [])
                if not m.get('is_valid', True)
            ]

    if not modules_to_fix:
        print("No modules to fix found in validation report")
        return

    print(f"Found {len(modules_to_fix)} modules with issues")
    results = fixer.fix_all_modules(modules_to_fix)

    # Save results
    results_file = Path(base_dir) / "manifest_fix_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {results_file}")

if __name__ == "__main__":
    main()
