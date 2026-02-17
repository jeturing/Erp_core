#!/usr/bin/env python3
"""
✅ Migration Validation Tool - Odoo 17 → 19

Valida que todos los módulos migrados cumplan con estándares v19

Uso:
    python scripts/validate_migration.py --target extra-addons/V19
    python scripts/validate_migration.py --target extra-addons/V19 --report validation_report.json
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List
import re

# ========================
# SETUP LOGGING
# ========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# VALIDACION RULES
# ========================

VALIDATION_RULES = {
    'manifest': {
        'description': 'Validar __manifest__.py',
        'checks': [
            ('exists', 'Archivo __manifest__.py existe'),
            ('version_v19', 'Versión es v19.0.x.x.x'),
            ('has_license', 'License especificada'),
            ('has_depends', 'Dependencias definidas'),
            ('valid_syntax', 'Sintaxis Python válida'),
        ]
    },
    'python': {
        'description': 'Validar código Python',
        'checks': [
            ('no_api_multi', 'Sin @api.multi'),
            ('no_api_one', 'Sin @api.one'),
            ('valid_syntax', 'Sintaxis Python válida'),
        ]
    },
    'xml': {
        'description': 'Validar archivos XML',
        'checks': [
            ('valid_xml', 'XML bien formado'),
            ('no_syntax_errors', 'Sin errores de sintaxis'),
        ]
    },
    'structure': {
        'description': 'Validar estructura de carpetas',
        'checks': [
            ('has_init', 'Tiene __init__.py en raíz'),
            ('has_models', 'Tiene carpeta models/ (si es aplicable)'),
        ]
    }
}

# ========================
# CLASE DE VALIDACIÓN
# ========================

class ModuleValidator:
    """Valida un módulo Odoo v19"""

    def __init__(self, module_path: Path):
        self.path = Path(module_path)
        self.name = self.path.name
        self.results = {
            'module': self.name,
            'path': str(self.path),
            'validation_results': {},
            'issues': [],
            'warnings': [],
            'is_valid': True,
            'score': 0.0  # 0-100
        }

    def validate(self) -> Dict:
        """Ejecuta todas las validaciones"""
        logger.info(f"Validando módulo: {self.name}")

        # Validar manifest
        self._validate_manifest()

        # Validar Python
        self._validate_python()

        # Validar XML
        self._validate_xml()

        # Validar estructura
        self._validate_structure()

        # Calcular score
        self._calculate_score()

        return self.results

    def _validate_manifest(self):
        """Valida __manifest__.py"""
        manifest_path = self.path / '__manifest__.py'
        result = {'passed': 0, 'failed': 0, 'checks': {}}

        # Check 1: Existe
        if manifest_path.exists():
            result['checks']['exists'] = True
            result['passed'] += 1
        else:
            result['checks']['exists'] = False
            result['failed'] += 1
            self.results['issues'].append('❌ Falta __manifest__.py')
            self.results['is_valid'] = False
            self.results['validation_results']['manifest'] = result
            return

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check 2: Versión es v19
            version_match = re.search(r"'version':\s*'([^']*)'", content)
            if version_match:
                version = version_match.group(1)
                if version.startswith('19.0'):
                    result['checks']['version_v19'] = True
                    result['passed'] += 1
                else:
                    result['checks']['version_v19'] = False
                    result['failed'] += 1
                    self.results['warnings'].append(f"⚠️ Versión es {version}, esperado 19.0.x")
            else:
                result['checks']['version_v19'] = False
                result['failed'] += 1
                self.results['warnings'].append('⚠️ No se encontró version')

            # Check 3: License especificada
            if 'license' in content:
                result['checks']['has_license'] = True
                result['passed'] += 1
            else:
                result['checks']['has_license'] = False
                result['failed'] += 1
                self.results['warnings'].append('⚠️ License no especificada')

            # Check 4: Dependencias definidas
            if 'depends' in content:
                result['checks']['has_depends'] = True
                result['passed'] += 1
            else:
                result['checks']['has_depends'] = False
                result['failed'] += 1
                self.results['warnings'].append('⚠️ Dependencias no definidas')

            # Check 5: Sintaxis válida
            try:
                compile(content, str(manifest_path), 'exec')
                result['checks']['valid_syntax'] = True
                result['passed'] += 1
            except SyntaxError as e:
                result['checks']['valid_syntax'] = False
                result['failed'] += 1
                self.results['issues'].append(f'❌ Error de sintaxis en manifest: {e}')
                self.results['is_valid'] = False

        except Exception as e:
            self.results['issues'].append(f'❌ Error leyendo manifest: {e}')
            self.results['is_valid'] = False

        self.results['validation_results']['manifest'] = result

    def _validate_python(self):
        """Valida archivos Python"""
        result = {'passed': 0, 'failed': 0, 'checks': {}, 'files_checked': 0}

        py_files = list(self.path.glob('**/*.py'))

        if not py_files:
            logger.warning(f"  No se encontraron archivos Python en {self.name}")
            self.results['validation_results']['python'] = result
            return

        result['files_checked'] = len(py_files)

        # Check 1: Sin @api.multi
        multi_count = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '@api.multi' in content:
                        multi_count += 1
            except Exception:
                pass

        if multi_count == 0:
            result['checks']['no_api_multi'] = True
            result['passed'] += 1
        else:
            result['checks']['no_api_multi'] = False
            result['failed'] += 1
            self.results['warnings'].append(f'⚠️ {multi_count} archivos con @api.multi')

        # Check 2: Sin @api.one
        one_count = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '@api.one' in content:
                        one_count += 1
            except Exception:
                pass

        if one_count == 0:
            result['checks']['no_api_one'] = True
            result['passed'] += 1
        else:
            result['checks']['no_api_one'] = False
            result['failed'] += 1
            self.results['issues'].append(f'❌ {one_count} archivos con @api.one (removido en v18)')
            self.results['is_valid'] = False

        # Check 3: Sintaxis válida
        syntax_errors = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    compile(content, str(py_file), 'exec')
            except SyntaxError:
                syntax_errors += 1

        if syntax_errors == 0:
            result['checks']['valid_syntax'] = True
            result['passed'] += 1
        else:
            result['checks']['valid_syntax'] = False
            result['failed'] += 1
            self.results['issues'].append(f'❌ {syntax_errors} archivos con errores de sintaxis')
            self.results['is_valid'] = False

        self.results['validation_results']['python'] = result

    def _validate_xml(self):
        """Valida archivos XML"""
        result = {'passed': 0, 'failed': 0, 'checks': {}, 'files_checked': 0}

        xml_files = list(self.path.glob('**/*.xml'))

        if not xml_files:
            self.results['validation_results']['xml'] = result
            return

        result['files_checked'] = len(xml_files)

        # Check 1: XML bien formado
        try:
            import xml.etree.ElementTree as ET
            xml_errors = 0

            for xml_file in xml_files:
                try:
                    ET.parse(xml_file)
                except ET.ParseError:
                    xml_errors += 1

            if xml_errors == 0:
                result['checks']['valid_xml'] = True
                result['passed'] += 1
            else:
                result['checks']['valid_xml'] = False
                result['failed'] += 1
                self.results['warnings'].append(f'⚠️ {xml_errors} archivos XML con errores')

        except ImportError:
            logger.warning("xml.etree no disponible, saltando validación XML")

        self.results['validation_results']['xml'] = result

    def _validate_structure(self):
        """Valida estructura de carpetas"""
        result = {'passed': 0, 'failed': 0, 'checks': {}}

        # Check 1: Tiene __init__.py
        init_path = self.path / '__init__.py'
        if init_path.exists():
            result['checks']['has_init'] = True
            result['passed'] += 1
        else:
            result['checks']['has_init'] = False
            result['failed'] += 1
            self.results['warnings'].append('⚠️ Falta __init__.py en raíz')

        # Check 2: Tiene models/ (si es aplicable)
        models_path = self.path / 'models'
        if models_path.exists() or (self.path / 'models.py').exists():
            result['checks']['has_models'] = True
            result['passed'] += 1
        else:
            # No es error, algunos módulos no tienen modelos
            result['checks']['has_models'] = None  # N/A

        self.results['validation_results']['structure'] = result

    def _calculate_score(self):
        """Calcula score de validación 0-100"""
        total_checks = 0
        passed_checks = 0

        for category, result in self.results['validation_results'].items():
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)

            total_checks += passed + failed
            passed_checks += passed

        if total_checks > 0:
            self.results['score'] = (passed_checks / total_checks) * 100
        else:
            self.results['score'] = 0.0


# ========================
# FUNCIÓN PRINCIPAL
# ========================

def main():
    parser = argparse.ArgumentParser(
        description='Validar módulos Odoo v19 migrados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Validar todos los módulos en V19
  %(prog)s --target extra-addons/V19

  # Validar y generar reporte JSON
  %(prog)s --target extra-addons/V19 --report validation_report.json

  # Validar módulo específico
  %(prog)s --target extra-addons/V19 --module [nombre]
        """
    )

    parser.add_argument('--target', required=True, help='Directorio con módulos a validar')
    parser.add_argument('--module', help='Validar módulo específico')
    parser.add_argument('--report', help='Guardar reporte en JSON')
    parser.add_argument('--strict', action='store_true', help='Fallar si hay warnings')

    args = parser.parse_args()

    target_dir = Path(args.target)

    if not target_dir.exists():
        logger.error(f"❌ Directorio no existe: {target_dir}")
        sys.exit(1)

    # Encontrar módulos
    if args.module:
        modules = [target_dir / args.module]
    else:
        modules = [d for d in target_dir.iterdir() if d.is_dir() and (d / '__manifest__.py').exists()]

    logger.info(f"🔍 Validando {len(modules)} módulo(s)...")
    logger.info("")

    # Validar cada módulo
    all_results = {
        'timestamp': str(Path.cwd()),
        'target_directory': str(target_dir),
        'modules_found': len(modules),
        'modules': [],
        'summary': {
            'total_modules': len(modules),
            'valid_modules': 0,
            'invalid_modules': 0,
            'average_score': 0.0
        }
    }

    total_score = 0.0

    for module_path in sorted(modules):
        validator = ModuleValidator(module_path)
        results = validator.validate()

        all_results['modules'].append(results)

        # Print resultado
        status_icon = '✅' if results['is_valid'] else '❌'
        score_str = f"{results['score']:.0f}%"
        print(f"{status_icon} {results['module']:<40} [{score_str}]", end="")

        if results['warnings']:
            print(f" {len(results['warnings'])} ⚠️", end="")
        if results['issues']:
            print(f" {len(results['issues'])} ❌", end="")

        print()

        total_score += results['score']

        if results['is_valid']:
            all_results['summary']['valid_modules'] += 1
        else:
            all_results['summary']['invalid_modules'] += 1

    # Resumen
    avg_score = total_score / len(modules) if modules else 0
    all_results['summary']['average_score'] = avg_score

    logger.info("")
    logger.info(f"📊 RESUMEN:")
    logger.info(f"   Módulos válidos: {all_results['summary']['valid_modules']}/{len(modules)}")
    logger.info(f"   Score promedio: {avg_score:.1f}%")

    # Guardar reporte
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 Reporte guardado: {args.report}")

    # Exit code
    if args.strict and all_results['summary']['invalid_modules'] > 0:
        logger.error("❌ Modo strict: hay módulos inválidos")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
