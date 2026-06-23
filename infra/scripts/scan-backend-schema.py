#!/usr/bin/env python3
"""
scan-backend-schema.py — Scan fpr-fprtool-backend API interfaces → extract request schemas → inject.

1. Build class map from backend (all .java files)
2. Scan *API.java for @URL annotations + method signatures
3. Match against exposed-ops.yaml desired paths
4. Extract DTO fields (type + nullability) from request DTOs
5. Build OpenAPI schema with data/context envelope
6. Inject into domain JSONs and fprtool-full.json

Usage:
  python infra/scripts/scan-backend-schema.py
  python infra/scripts/scan-backend-schema.py --inject
"""

import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_BACKEND = os.path.join(ROOT, '..', 'fpr-fprtool-backend')
DEFAULT_SCHEMAS = os.path.join(ROOT, 'infra', 'schemas')
CONFIG_PATH = os.path.join(ROOT, 'infra', 'config', 'exposed-ops.yaml')

TYPE_MAP = {
    'String': 'string', 'Integer': 'integer', 'int': 'integer', 'long': 'integer',
    'boolean': 'boolean', 'Boolean': 'boolean', 'Double': 'number', 'double': 'number',
    'Float': 'number', 'BigDecimal': 'number', 'LocalDate': 'string', 'LocalDateTime': 'string',
    'Instant': 'string', 'Date': 'string', 'ZonedDateTime': 'string',
}

DTO_FIELD_RE = re.compile(
    r'(@NotNullable|@Nullable)\s*\n'
    r'\s*(?:(?:private|protected|public)\s+)?'
    r'((?:List<[^>]+>|Map<[^>,]+,\s*[^>]+>|\w+(?:<[^>]+>)?))\s+'
    r'(\w+)\s*[;=]',
    re.DOTALL
)

URL_METHOD_RE = re.compile(
    r'@URL\("([^"]+)"\).*?'
    r'OptoolsPublicAPIResponse<[^>]*>\s+(\w+)\s*'
    r'\(.*?OptoolsPublicAPIRequest<(\w+)>',
    re.DOTALL
)


def build_class_map(backend_path):
    class_map = {}
    for root, dirs, files in os.walk(backend_path):
        if '/test/' in root or '/target/' in root:
            continue
        for fname in files:
            if fname.endswith('.java'):
                class_map[fname[:-5]] = os.path.join(root, fname)
    return class_map


def extract_fields(dto_content):
    fields = []
    seen = set()
    for m in DTO_FIELD_RE.finditer(dto_content):
        required = 'NotNullable' in m.group(1)
        java_type = m.group(2)
        field_name = m.group(3)
        if field_name in seen:
            continue
        seen.add(field_name)

        list_match = re.match(r'List<(.+)>', java_type)
        if list_match:
            inner = TYPE_MAP.get(list_match.group(1), 'string')
            schema = {'type': 'array', 'items': {'type': inner}}
        else:
            schema = {'type': TYPE_MAP.get(java_type, 'string')}

        fields.append({'name': field_name, 'schema': schema, 'required': required})
    return fields


def build_request_schema(fields):
    return {
        'type': 'object',
        'properties': {f['name']: f['schema'] for f in fields},
        'required': [f['name'] for f in fields if f['required']] or None,
    }


def build_operation(data_schema):
    return {
        'requestBody': {
            'required': True,
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'required': ['data', 'context'],
                        'properties': {
                            'data': {
                                'type': 'object',
                                'description': 'Request parameters',
                                'properties': data_schema.get('properties', {}),
                                'required': data_schema.get('required'),
                            },
                            'context': {
                                'type': 'object',
                                'properties': {
                                    'authServiceToken': {
                                        'type': 'string',
                                        'description': 'User JWT token',
                                    }
                                },
                                'required': ['authServiceToken'],
                            },
                            'clientInterface': {
                                'type': 'string',
                                'default': 'DESKTOP',
                            },
                            'fields': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'default': [],
                            },
                        },
                    }
                }
            },
        },
        'responses': {
            '200': {
                'description': 'Success',
                'content': {'application/json': {'schema': {'type': 'object'}}},
            }
        },
    }


def main():
    parser = argparse.ArgumentParser(description='Scan backend APIs for request schemas')
    parser.add_argument('--backend-path', default=DEFAULT_BACKEND)
    parser.add_argument('--schemas-dir', default=DEFAULT_SCHEMAS)
    parser.add_argument('--inject', action='store_true', help='Write schemas into domain JSONs')
    args = parser.parse_args()

    backend = os.path.abspath(args.backend_path)
    schemas_dir = os.path.abspath(args.schemas_dir)

    # 1. Load config
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    desired_ops = {}
    path_to_op = {}  # desired_path → op_id
    for domain, ops in config.items():
        for op in ops:
            desired_path = f'/api/v2/{op["path"]}'
            desired_ops[op['id']] = {'domain': domain, 'desired_path': desired_path}
            path_to_op[desired_path] = op['id']

    print(f"📋 {len(desired_ops)} desired ops from exposed-ops.yaml")

    # 2. Build class map
    print(f"🔍 Scanning backend...")
    class_map = build_class_map(backend)
    print(f"  {len(class_map)} Java classes")

    # 3. Scan API interfaces
    api_files = [p for name, p in class_map.items() if name.endswith('API')]
    print(f"  {len(api_files)} API interfaces")

    schemas_found = {}
    for fpath in api_files:
        with open(fpath, encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for m in URL_METHOD_RE.finditer(content):
            api_url = m.group(1)  # e.g. /api/supply-search-tool/search-regular-fare
            req_dto = m.group(3)

            # Normalize: /api/X → /api/v2/X
            if api_url.startswith('/api/'):
                check_url = '/api/v2' + api_url[4:]
            else:
                check_url = api_url

            op_id = path_to_op.get(check_url)
            if not op_id:
                continue

            if req_dto == 'EmptyRequest':
                schemas_found[op_id] = {
                    'dto': 'EmptyRequest',
                    'schema': build_request_schema([]),
                    'field_count': 0,
                }
                print(f'  ✅ {op_id}: EmptyRequest')
                continue

            if req_dto not in class_map:
                continue

            with open(class_map[req_dto], encoding='utf-8', errors='ignore') as f2:
                dto_content = f2.read()

            fields = extract_fields(dto_content)
            request_schema = build_request_schema(fields)
            schemas_found[op_id] = {
                'dto': req_dto,
                'schema': request_schema,
                'field_count': len(fields),
            }
            n_req = len(request_schema.get('required') or [])
            print(f'  ✅ {op_id}: {req_dto} ({len(fields)} fields, {n_req} required)')

    print(f"\n📊 Matched: {len(schemas_found)}/{len(desired_ops)}")

    if not args.inject:
        return

    # 4. Inject into domain JSONs
    injected = 0
    for entry in os.listdir(schemas_dir):
        domain_dir = os.path.join(schemas_dir, entry)
        if not os.path.isdir(domain_dir):
            continue
        json_path = os.path.join(domain_dir, f'{entry}.json')
        if not os.path.exists(json_path):
            continue

        with open(json_path) as f:
            spec = json.load(f)

        updated = False
        for path, methods in spec.get('paths', {}).items():
            for method, ops in methods.items():
                op_id = ops.get('operationId', '')
                if op_id in schemas_found:
                    info = schemas_found[op_id]
                    ops.pop('summary', None)
                    ops.update(build_operation(info['schema']))
                    updated = True
                    injected += 1

        if updated:
            with open(json_path, 'w') as f:
                json.dump(spec, f, indent=2)
                f.write('\n')

    print(f"  💉 Injected {injected} schemas into domain files")

    # 5. Inject into fprtool-full.json
    full_path = os.path.join(schemas_dir, 'fprtool-full.json')
    if os.path.exists(full_path):
        with open(full_path) as f:
            full_spec = json.load(f)
        updated = 0
        for path, methods in full_spec.get('paths', {}).items():
            for method, ops in methods.items():
                op_id = ops.get('operationId', '')
                if op_id in schemas_found:
                    ops.update(build_operation(schemas_found[op_id]['schema']))
                    updated += 1
        if updated:
            with open(full_path, 'w') as f:
                json.dump(full_spec, f, indent=2)
                f.write('\n')
            print(f"  💉 Injected {updated} into fprtool-full.json")


if __name__ == '__main__':
    main()