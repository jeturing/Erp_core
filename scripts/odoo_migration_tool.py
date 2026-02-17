#!/usr/bin/env python3
"""
🚀 Odoo 17 → 19 Automated Migration Tool
=============================================

Herramienta para automatizar la migración de módulos Odoo de v17 a v19

Uso:
    python odoo_migration_tool.py --source extra-addons/V17 --target extra-addons/V19 --module [module_name]

Características:
    - Detecta automáticamente patrones deprecados
    - Corrige decoradores @api.multi, @api.one
    - Actualiza __manifest__.py
    - Valida dependencias
    - Genera reporte de cambios
    - Testing básico post-migración
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime
import ast

# ========================
# CONFIGURACIÓN Y LOGGING
# ========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('odoo_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========================
# CONSTANTES
# ========================

DEPRECATED_DECORATORS = {
    '@api.multi': {
        'pattern': r'@api\.multi\s*\n',
        'replacement': '',
        'severity': 'HIGH',
        'description': 'Removido en Odoo 18'
    },
    '@api.one': {
        'pattern': r'@api\.one\s*\n',
        'replacement': '',
        'severity': 'HIGH',
        'description': 'Removido en Odoo 17'
    },
}

ODOO_19_DEPENDENCIES = [
    'base', 'web', 'sale', 'purchase', 'account', 'stock',
    'crm', 'hr', 'project', 'website', 'pos_restaurant'
]

# ========================
# CLASSES
# ========================

class OdooModule:
    """Representa un módulo Odoo"""

    def __init__(self, module_path: Path):
        self.path = Path(module_path)
        self.name = self.path.name
        self.manifest_path = self.path / '__manifest__.py'
        self.manifest = None
        self.issues = []
        self.warnings = []
        self.changes = []

        if not self.path.exists():
            raise FileNotFoundError(f"Módulo no encontrado: {module_path}")

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"__manifest__.py no encontrado en {module_path}")

        self._load_manifest()

    def _load_manifest(self):
        """Carga el manifest.py del módulo de forma segura"""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Usar ast.literal_eval para seguridad
                self.manifest = ast.literal_eval(content)
                logger.info(f"✅ Manifest cargado: {self.name}")
        except (ValueError, SyntaxError) as e:
            # Si literal_eval falla, intentar parsing manual para dicts simples
            logger.warning(f"⚠️  Usando parser manual para manifest")
            self._parse_manifest_safe(content)
        except Exception as e:
            logger.error(f"❌ Error cargando manifest: {e}")
            raise

    def _parse_manifest_safe(self, content: str):
        """Parser manual seguro para manifest.py"""
        self.manifest = {}
        # Expresiones regex seguras para extraer key-value pairs
        pairs = re.findall(r"['\"](\w+)['\"]\s*:\s*['\"]([^'\"]*)['\"]", content)
        for key, value in pairs:
            if value.lower() == 'true':
                self.manifest[key] = True
            elif value.lower() == 'false':
                self.manifest[key] = False
            else:
                self.manifest[key] = value

    def save_manifest(self):
        """Guarda el manifest actualizado en formato Python"""
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                f.write("{\n")
                for key, value in self.manifest.items():
                    if isinstance(value, str):
                        f.write(f"    '{key}': '{value}',\n")
                    elif isinstance(value, bool):
                        f.write(f"    '{key}': {str(value)},\n")
                    elif isinstance(value, list):
                        # Formatear lista
                        list_str = "[\n"
                        for item in value:
                            list_str += f"        '{item}',\n"
                        list_str += "    ]"
                        f.write(f"    '{key}': {list_str},\n")
                    elif isinstance(value, dict):
                        f.write(f"    '{key}': {value},\n")
                f.write("}\n")
            logger.info(f"✅ Manifest guardado: {self.name}")
        except Exception as e:
            logger.error(f"❌ Error guardando manifest: {e}")

    def get_python_files(self) -> List[Path]:
        """Retorna lista de archivos .py en el módulo"""
        return list(self.path.glob('**/*.py'))

    def get_xml_files(self) -> List[Path]:
        """Retorna lista de archivos .xml en el módulo"""
        return list(self.path.glob('**/*.xml'))

    def analyze(self) -> Dict:
        """Analiza el módulo en busca de issues de v17"""
        logger.info(f"🔍 Analizando módulo: {self.name}")

        analysis = {
            'module': self.name,
            'total_issues': 0,
            'total_warnings': 0,
            'python_issues': [],
            'manifest_issues': [],
            'xml_issues': [],
            'dependency_issues': []
        }

        # Analizar Python
        self._analyze_python(analysis)

        # Analizar manifest
        self._analyze_manifest(analysis)

        # Analizar XML
        self._analyze_xml(analysis)

        analysis['total_issues'] = len(self.issues)
        analysis['total_warnings'] = len(self.warnings)

        return analysis

    def _analyze_python(self, analysis: Dict):
        """Analiza archivos Python en busca de patrones deprecados"""
        logger.info(f"  Revisando archivos Python...")

        for py_file in self.get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        # Buscar @api.multi
                        if '@api.multi' in line:
                            issue = {
                                'file': str(py_file.relative_to(self.path)),
                                'line': i,
                                'pattern': '@api.multi',
                                'severity': 'HIGH',
                                'message': 'Removido en Odoo 18 - debe eliminarse',
                                'code': line.strip()
                            }
                            analysis['python_issues'].append(issue)
                            self.issues.append(issue)

                        # Buscar @api.one
                        if '@api.one' in line:
                            issue = {
                                'file': str(py_file.relative_to(self.path)),
                                'line': i,
                                'pattern': '@api.one',
                                'severity': 'HIGH',
                                'message': 'Removido en Odoo 17 - debe eliminarse',
                                'code': line.strip()
                            }
                            analysis['python_issues'].append(issue)
                            self.issues.append(issue)

                        # Buscar @api.model (deprecado, revisar)
                        if '@api.model' in line and '@api.multi' not in line and '@api.one' not in line:
                            warning = {
                                'file': str(py_file.relative_to(self.path)),
                                'line': i,
                                'pattern': '@api.model',
                                'message': 'Deprecado en Odoo 18 - considerar usar @api.model_create_multi',
                                'code': line.strip()
                            }
                            analysis['python_issues'].append(warning)
                            self.warnings.append(warning)

            except Exception as e:
                logger.error(f"    Error analizando {py_file}: {e}")

    def _analyze_manifest(self, analysis: Dict):
        """Analiza el manifest.py"""
        logger.info(f"  Revisando __manifest__.py...")

        # Verificar versión
        version = self.manifest.get('version', '17.0.1.0.0')
        if version and version.startswith('17.0.'):
            issue = {
                'field': 'version',
                'current': version,
                'expected': version.replace('17.0.', '19.0.'),
                'severity': 'HIGH',
                'message': 'Versión aún es v17'
            }
            analysis['manifest_issues'].append(issue)
            self.issues.append(issue)

        # Verificar dependencias
        depends = self.manifest.get('depends', [])
        for dep in depends:
            if dep not in ODOO_19_DEPENDENCIES and dep not in ['base', 'web']:
                warning = {
                    'field': 'depends',
                    'value': dep,
                    'severity': 'MEDIUM',
                    'message': f'Dependencia "{dep}" puede no existir en Odoo 19'
                }
                analysis['dependency_issues'].append(warning)
                self.warnings.append(warning)

        # Verificar license
        license = self.manifest.get('license', None)
        if not license:
            warning = {
                'field': 'license',
                'severity': 'LOW',
                'message': 'License no especificada'
            }
            analysis['manifest_issues'].append(warning)

    def _analyze_xml(self, analysis: Dict):
        """Analiza archivos XML"""
        logger.info(f"  Revisando archivos XML...")

        for xml_file in self.get_xml_files():
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Buscar patrones deprecados en XML
                    # Generalmente compatible, pero revisar algunos casos
                    pass
            except Exception as e:
                logger.error(f"    Error analizando {xml_file}: {e}")

    def fix(self) -> Dict:
        """Automáticamente corrige los issues encontrados"""
        logger.info(f"🔧 Corrigiendo módulo: {self.name}")

        fixes = {
            'module': self.name,
            'total_fixed': 0,
            'total_failed': 0,
            'fixes': []
        }

        # Corregir Python
        self._fix_python(fixes)

        # Corregir manifest
        self._fix_manifest(fixes)

        return fixes

    def _fix_python(self, fixes: Dict):
        """Corrige archivos Python"""
        logger.info(f"  Corrigiendo Python...")

        for py_file in self.get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Remover @api.multi
                content = re.sub(r'@api\.multi\s*\n', '', content)

                # Remover @api.one
                content = re.sub(r'@api\.one\s*\n', '', content)

                # Si hay cambios, guardar
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)

                    fixes['total_fixed'] += 1
                    fixes['fixes'].append({
                        'file': str(py_file.relative_to(self.path)),
                        'changes': 'Removidos decoradores deprecados',
                        'status': 'OK'
                    })
                    logger.info(f"    ✅ Corregido: {py_file.name}")
            except Exception as e:
                logger.error(f"    ❌ Error corrigiendo {py_file}: {e}")
                fixes['total_failed'] += 1

    def _fix_manifest(self, fixes: Dict):
        """Corrige el manifest.py"""
        logger.info(f"  Corrigiendo __manifest__.py...")

        # Actualizar versión
        if 'version' in self.manifest:
            old_version = self.manifest['version']
            self.manifest['version'] = old_version.replace('17.0.', '19.0.')
            if self.manifest['version'] != old_version:
                fixes['total_fixed'] += 1
                fixes['fixes'].append({
                    'file': '__manifest__.py',
                    'changes': f"version: {old_version} → {self.manifest['version']}",
                    'status': 'OK'
                })

        # Asegurar license
        if 'license' not in self.manifest:
            self.manifest['license'] = 'LGPL-3'
            fixes['total_fixed'] += 1
            fixes['fixes'].append({
                'file': '__manifest__.py',
                'changes': "license: agregado 'LGPL-3'",
                'status': 'OK'
            })

        # Guardar
        self.save_manifest()


class MigrationTool:
    """Herramienta principal de migración"""

    def __init__(self, source_dir: Path, target_dir: Path):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.migrations = []
        self.report = {
            'start_time': datetime.now().isoformat(),
            'modules': [],
            'summary': {}
        }

    def migrate_module(self, module_name: str, auto_fix: bool = True) -> Dict:
        """Migra un módulo específico"""
        logger.info(f"\n{'='*60}")
        logger.info(f"MIGRANDO: {module_name}")
        logger.info(f"{'='*60}")

        result = {
            'module': module_name,
            'status': 'pending',
            'steps': []
        }

        try:
            # Paso 1: Copiar módulo
            source_path = self.source_dir / module_name
            target_path = self.target_dir / module_name

            if not source_path.exists():
                raise FileNotFoundError(f"Módulo no encontrado en {source_path}")

            logger.info(f"\n1️⃣  Copiando módulo...")
            if target_path.exists():
                logger.warning(f"    ⚠️  {target_path} ya existe, removiendo...")
                shutil.rmtree(target_path)

            shutil.copytree(source_path, target_path)
            logger.info(f"    ✅ Módulo copiado")
            result['steps'].append({'name': 'copy', 'status': 'ok'})

            # Paso 2: Cargar y analizar
            logger.info(f"\n2️⃣  Analizando módulo...")
            module = OdooModule(target_path)
            analysis = module.analyze()
            logger.info(f"    Encontrados {analysis['total_issues']} issues")
            result['steps'].append({'name': 'analysis', 'status': 'ok', 'data': analysis})

            # Paso 3: Auto-fix si está habilitado
            if auto_fix and analysis['total_issues'] > 0:
                logger.info(f"\n3️⃣  Auto-fixeando...")
                fixes = module.fix()
                logger.info(f"    ✅ {fixes['total_fixed']} fixes aplicados")
                result['steps'].append({'name': 'fix', 'status': 'ok', 'data': fixes})

                # Re-analizar después de fix
                logger.info(f"\n4️⃣  Re-analizando después de fixes...")
                analysis = module.analyze()
                logger.info(f"    Issues restantes: {analysis['total_issues']}")
                result['steps'].append({'name': 're_analysis', 'status': 'ok', 'data': analysis})

            result['status'] = 'completed'
            logger.info(f"\n✅ MIGRACIÓN COMPLETADA: {module_name}")

        except Exception as e:
            logger.error(f"\n❌ ERROR en migración: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)

        self.report['modules'].append(result)
        return result

    def migrate_all(self, auto_fix: bool = True) -> Dict:
        """Migra todos los módulos en source_dir"""
        logger.info(f"🚀 INICIANDO MIGRACIÓN DE TODOS LOS MÓDULOS")
        logger.info(f"   Origen: {self.source_dir}")
        logger.info(f"   Destino: {self.target_dir}")

        if not self.source_dir.exists():
            raise FileNotFoundError(f"Directorio origen no existe: {self.source_dir}")

        # Crear directorio destino si no existe
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # Buscar todos los módulos (directorios con __manifest__.py)
        modules = []
        for item in self.source_dir.iterdir():
            if item.is_dir() and (item / '__manifest__.py').exists():
                modules.append(item.name)

        logger.info(f"Encontrados {len(modules)} módulos")

        for module_name in sorted(modules):
            self.migrate_module(module_name, auto_fix=auto_fix)

        # Generar resumen
        self._generate_summary()

        return self.report

    def _generate_summary(self):
        """Genera resumen de migración"""
        completed = sum(1 for m in self.report['modules'] if m['status'] == 'completed')
        failed = sum(1 for m in self.report['modules'] if m['status'] == 'failed')
        total = len(self.report['modules'])

        self.report['summary'] = {
            'total_modules': total,
            'completed': completed,
            'failed': failed,
            'success_rate': f"{(completed/total)*100:.1f}%" if total > 0 else "0%"
        }

        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN DE MIGRACIÓN")
        logger.info(f"{'='*60}")
        logger.info(f"Total módulos: {total}")
        logger.info(f"Completados: {completed} ✅")
        logger.info(f"Fallidos: {failed} ❌")
        logger.info(f"Tasa de éxito: {self.report['summary']['success_rate']}")

    def generate_report(self, output_file: str = 'migration_report.json'):
        """Genera reporte en JSON"""
        self.report['end_time'] = datetime.now().isoformat()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📊 Reporte guardado: {output_file}")


# ========================
# FUNCIÓN PRINCIPAL
# ========================

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Odoo 17 → 19 Automated Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Migrar un módulo específico
  %(prog)s --source extra-addons/V17 --target extra-addons/V19 --module account_custom

  # Migrar todos los módulos
  %(prog)s --source extra-addons/V17 --target extra-addons/V19 --all

  # Solo analizar sin cambios
  %(prog)s --source extra-addons/V17 --module account_custom --analyze-only

  # Generar reporte de compatibilidad
  %(prog)s --source extra-addons/V17 --report
        """
    )

    parser.add_argument('--source', required=True, help='Directorio origen (Odoo 17 modules)')
    parser.add_argument('--target', help='Directorio destino (Odoo 19 modules)')
    parser.add_argument('--module', help='Nombre específico del módulo a migrar')
    parser.add_argument('--all', action='store_true', help='Migrar todos los módulos')
    parser.add_argument('--analyze-only', action='store_true', help='Solo analizar sin cambios')
    parser.add_argument('--no-fix', action='store_true', help='No aplicar auto-fixes')
    parser.add_argument('--report', action='store_true', help='Generar reporte de compatibilidad')
    parser.add_argument('--output', default='migration_report.json', help='Archivo de salida del reporte')

    args = parser.parse_args()

    try:
        if args.report:
            # Modo reporte de compatibilidad
            logger.info("📊 Generando reporte de compatibilidad...")
            source = Path(args.source)

            compatibility_report = {
                'timestamp': datetime.now().isoformat(),
                'source': str(source),
                'modules': []
            }

            for item in source.iterdir():
                if item.is_dir() and (item / '__manifest__.py').exists():
                    logger.info(f"Analizando {item.name}...")
                    module = OdooModule(item)
                    analysis = module.analyze()

                    compatibility_report['modules'].append({
                        'name': item.name,
                        'compatible': analysis['total_issues'] == 0,
                        'issues_found': analysis['total_issues'],
                        'analysis': analysis
                    })

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(compatibility_report, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Reporte guardado: {args.output}")

        else:
            # Modo migración
            if not args.target:
                parser.error('--target es requerido para migración')

            tool = MigrationTool(Path(args.source), Path(args.target))

            if args.module:
                # Migrar módulo específico
                auto_fix = not (args.analyze_only or args.no_fix)
                tool.migrate_module(args.module, auto_fix=auto_fix)

            elif args.all:
                # Migrar todos
                auto_fix = not (args.analyze_only or args.no_fix)
                tool.migrate_all(auto_fix=auto_fix)

            else:
                parser.error('Especificar --module o --all')

            # Generar reporte
            tool.generate_report(args.output)

    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
