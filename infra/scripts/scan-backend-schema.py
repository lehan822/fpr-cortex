#!/usr/bin/env python3
"""
scan-backend-schema.py — Scan fpr-fprtool-backend API interfaces → extract request schemas → inject.

1. Build class map from backend (all .java files)
2. Parse *API.java files method-by-method to extract @URL + request DTO pairs
3. Match against exposed-ops.yaml desired paths
4. Extract DTO fields (type + nullability) from request DTOs
5. Build OpenAPI schema with data/context envelope
6. Inject into domain JSONs and fprtool-full.json, fixing paths to actual @URL

Usage:
  python infra/scripts/scan-backend-schema.py              # dry-run
  python infra/scripts/scan-backend-schema.py --inject     # write schemas
"""

import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required.", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_BACKEND = os.path.join(ROOT, '..', 'fpr-fprtool-backend')
DEFAULT_SCHEMAS = os.path.join(ROOT, 'infra', 'schemas')
CONFIG_PATH = os.path.join(ROOT, 'infra', 'config', 'exposed-ops.yaml')

TYPE_MAP = {
    'String': 'string', 'Integer': 'integer', 'Long': 'integer', 'int': 'integer', 'long': 'integer',
    'boolean': 'boolean', 'Boolean': 'boolean', 'Double': 'number', 'double': 'number',
    'Float': 'number', 'BigDecimal': 'number', 'LocalDate': 'string', 'LocalDateTime': 'string',
    'Instant': 'string', 'Date': 'string', 'ZonedDateTime': 'string',
}

# Types that suggest a complex/nested object (not a primitive)
PRIMITIVE_TYPES = {'String', 'Integer', 'Long', 'int', 'long', 'boolean', 'Boolean',
    'Double', 'double', 'Float', 'BigDecimal', 'LocalDate', 'LocalDateTime',
    'Instant', 'Date', 'ZonedDateTime'}

DTO_FIELD_RE = re.compile(
    r'(@NotNullable|@Nullable)\s*\n'
    r'\s*(?:(?:private|protected|public)\s+)?'
    r'(?:final\s+)?'
    r'((?:List<[^>]+>|Map<[^>,]+,\s*[^>]+>|\w+(?:<[^>]+>)?))\s+'
    r'(\w+)\s*[;=]',
    re.DOTALL
)

METHOD_SIG_RE = re.compile(
    r'OptoolsPublicAPIResponse<([^>]*)>\s+(\w+)\s*\(\s*'
    r'OptoolsPublicAPIRequest<(\w+)>'
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


def extract_api_methods(content):
    results = []
    current_url = None
    pending_method = None
    pending_started = False

    for line in content.split('\n'):
        stripped = line.strip()

        url_match = re.match(r'@URL\("([^"]+)"\)', stripped)
        if url_match:
            current_url = url_match.group(1)
            pending_method = None
            pending_started = False
            continue

        if pending_started:
            pending_method = (pending_method or '') + ' ' + stripped
        elif stripped.startswith('@') or stripped in ('public', 'private', 'protected', ''):
            continue
        else:
            pending_method = stripped
            pending_started = True

        if pending_method and current_url:
            sig_match = METHOD_SIG_RE.search(pending_method)
            if sig_match:
                results.append({
                    'url': current_url,
                    'response_dto': sig_match.group(1),
                    'method_name': sig_match.group(2),
                    'request_dto': sig_match.group(3),
                })
                current_url = None
                pending_method = None
                pending_started = False

    return results


def extract_dto_fields(dto_content):
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
            inner = list_match.group(1)
            if inner in PRIMITIVE_TYPES:
                inner_schema = {'type': TYPE_MAP.get(inner, 'string')}
            else:
                inner_schema = {'type': 'object'}
            schema = {'type': 'array', 'items': inner_schema}
        else:
            schema = {'type': TYPE_MAP.get(java_type, 'object' if java_type not in PRIMITIVE_TYPES else 'string')}

        fields.append({'name': field_name, 'schema': schema, 'required': required})
    return fields


def build_request_schema(fields):
    return {
        'type': 'object',
        'properties': {f['name']: f['schema'] for f in fields},
        'required': [f['name'] for f in fields if f['required']],
    }


DATA_ENVELOPE = {
    'type': 'object',
    'properties': {
        'authServiceToken': {'type': 'string', 'description': 'User JWT token'},
    },
    'required': ['authServiceToken'],
}

CLIENT_IFACE = {'type': 'string', 'default': 'DESKTOP'}
FIELDS_ARRAY = {'type': 'array', 'items': {'type': 'string'}, 'default': []}


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
                            'context': DATA_ENVELOPE,
                            'clientInterface': CLIENT_IFACE,
                            'fields': FIELDS_ARRAY,
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


def scan_and_match(backend_path, config_path=CONFIG_PATH, skip_domains=None):
    skip_domains = set(skip_domains or [])

    with open(config_path) as f:
        config = yaml.safe_load(f)

    path_to_op = {}
    for domain, ops in config.items():
        if domain in skip_domains:
            continue
        for op in ops:
            desired_path = f'/api/v2/{op["path"]}'
            op_ids = path_to_op.get(desired_path, [])
            op_ids.append(op['id'])
            path_to_op[desired_path] = op_ids

    print(f"📋 {sum(len(v) for v in path_to_op.values())} desired ops")

    class_map = build_class_map(backend_path)
    print(f"  {len(class_map)} Java classes")

    api_files = [p for name, p in class_map.items() if name.endswith('API')]
    print(f"  {len(api_files)} API interfaces")

    schemas_found = {}
    for fpath in api_files:
        with open(fpath, encoding='utf-8', errors='ignore') as f:
            content = f.read()

        methods = extract_api_methods(content)
        for m in methods:
            api_url = m['url']  # e.g. /api/supply-search-tool/search-regular-fare
            req_dto_name = m['request_dto']

            # Normalize: /api/X → /api/v2/X; /api/v1/X → /api/v2/X
            if api_url.startswith('/api/v1/'):
                check_url = '/api/v2' + api_url[7:]
            elif api_url.startswith('/api/') and not api_url.startswith('/api/v2/'):
                check_url = '/api/v2' + api_url[4:]
            else:
                check_url = api_url

            op_ids = path_to_op.get(check_url, [])
            if not op_ids:
                continue

            for op_id in op_ids:
                if req_dto_name in ('EmptyRequest', 'PEmpty'):
                    schemas_found[op_id] = {
                        'dto': 'EmptyRequest', 'schema': build_request_schema([]),
                        'field_count': 0, 'api_url': api_url,
                    }
                    print(f'  ✅ {op_id}: EmptyRequest')
                    continue

                if req_dto_name not in class_map:
                    continue

                with open(class_map[req_dto_name], encoding='utf-8', errors='ignore') as f2:
                    dto_content = f2.read()

                fields = extract_dto_fields(dto_content)
                request_schema = build_request_schema(fields)
                schemas_found[op_id] = {
                    'dto': req_dto_name, 'schema': request_schema,
                    'field_count': len(fields), 'api_url': api_url,
                }
                n_req = len(request_schema.get('required') or [])
                print(f'  ✅ {op_id}: {req_dto_name} ({len(fields)} fields, {n_req} required)')

    total_desired = sum(len(v) for v in path_to_op.values())
    print(f"\n📊 Matched: {len(schemas_found)}/{total_desired}")
    return schemas_found


def inject_schemas(schemas_found, schemas_dir=DEFAULT_SCHEMAS):
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

        path_fixes = []
        for path, methods in list(spec.get('paths', {}).items()):
            for method, ops in list(methods.items()):
                op_id = ops.get('operationId', '')
                if op_id not in schemas_found:
                    continue
                info = schemas_found[op_id]
                ops.update(build_operation(info['schema']))
                actual_url = info.get('api_url', '')
                if actual_url and actual_url != path:
                    path_fixes.append((path, method, actual_url, ops))
                    del spec['paths'][path][method]
                    if not spec['paths'][path]:
                        del spec['paths'][path]
                injected += 1

        for old_path, method, new_path, ops in path_fixes:
            spec['paths'][new_path] = {method: ops}

        if injected > 0:
            with open(json_path, 'w') as f:
                json.dump(spec, f, indent=2)
                f.write('\n')

    print(f"  💉 Injected {injected} into domain files")

    # fprtool-full.json — also fix paths
    full_path = os.path.join(schemas_dir, 'fprtool-full.json')
    if os.path.exists(full_path):
        with open(full_path) as f:
            full_spec = json.load(f)
        fu = 0
        fp_fixes = []
        for path, methods in list(full_spec.get('paths', {}).items()):
            for method, ops in list(methods.items()):
                op_id = ops.get('operationId', '')
                if op_id not in schemas_found:
                    continue
                info = schemas_found[op_id]
                ops.update(build_operation(info['schema']))
                actual_url = info.get('api_url', '')
                if actual_url and actual_url != path:
                    fp_fixes.append((path, method, actual_url, ops))
                    del full_spec['paths'][path][method]
                    if not full_spec['paths'][path]:
                        del full_spec['paths'][path]
                fu += 1
        for old_path, method, new_path, ops in fp_fixes:
            full_spec['paths'][new_path] = {method: ops}
        if fu > 0:
            with open(full_path, 'w') as f:
                json.dump(full_spec, f, indent=2)
                f.write('\n')
            print(f"  💉 Injected {fu} into fprtool-full.json")


def main():
    parser = argparse.ArgumentParser(description='Scan backend APIs for request schemas')
    parser.add_argument('--backend-path', default=DEFAULT_BACKEND)
    parser.add_argument('--schemas-dir', default=DEFAULT_SCHEMAS)
    parser.add_argument('--inject', action='store_true')
    parser.add_argument('--skip-domains', nargs='*', default=['pricing'])
    args = parser.parse_args()

    print(f"🔍 Scanning backend: {args.backend_path}")
    if args.skip_domains:
        print(f"⏭️  Skipping: {args.skip_domains}")
    schemas_found = scan_and_match(args.backend_path, skip_domains=args.skip_domains)

    if schemas_found and args.inject:
        inject_schemas(schemas_found, args.schemas_dir)


if __name__ == '__main__':
    main()