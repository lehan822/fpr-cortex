#!/usr/bin/env python3
"""
gen-schema.py — Generate per-domain OpenAPI schemas from exposed-ops.yaml + backend source.

Flow:
  1. Read infra/config/exposed-ops.yaml (source of truth)
  2. For standard APIs: extract request/response schema from fprtool-full.json (if exists)
  3. For CRUD APIs: scan fpr-fprtool-backend source to extract filter/sort fields
  4. Output per-domain OpenAPI 3.1 JSON → infra/schemas/{domain}/{domain}.json

Usage:
  python infra/scripts/gen-schema.py [--backend-path ../fpr-fprtool-backend] [--output-dir infra/schemas]
  python infra/scripts/gen-schema.py --upload-s3  # generate + push to S3

Requires: PyYAML (pip install pyyaml)
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
DEFAULT_OUTPUT = os.path.join(ROOT, 'infra', 'schemas')
CONFIG_PATH = os.path.join(ROOT, 'infra', 'config', 'exposed-ops.yaml')
FULL_SPEC_PATH = os.path.join(ROOT, 'infra', 'schemas', 'fprtool-full.json')

# CRUD path pattern: crud/getEntryList(entityType) or crud/getEntryDetail(entityType)
CRUD_PATTERN = re.compile(r'^crud/(getEntryList|getEntryDetail)\((\w+)\)$')


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_full_spec():
    """Load existing fprtool-full.json if available (for standard API schemas)."""
    if os.path.exists(FULL_SPEC_PATH):
        with open(FULL_SPEC_PATH) as f:
            return json.load(f)
    return None


def scan_crud_entity(backend_path, entity_type):
    """Scan backend source to find EntityAccessor for given entityType and extract metadata."""
    result = {
        'entity_type': entity_type,
        'filter_fields': [],
        'sort_fields': [],
        'accessor_file': None
    }

    # Walk all EntityAccessor files
    for root, dirs, files in os.walk(backend_path):
        if '/test/' in root or '/target/' in root:
            continue
        for fname in files:
            if 'EntityAccessor' not in fname or not fname.endswith('.java'):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, encoding='utf-8', errors='ignore') as f:
                src = f.read()

            # Check if this accessor handles our entity type
            if f'"{entity_type}"' not in src and entity_type not in src:
                continue

            # Verify it has readEntryList (for getEntryList ops)
            if 'readEntryList' not in src:
                continue

            result['accessor_file'] = fpath

            # Extract FIELD_ constants (filter fields)
            fields = set(re.findall(r'private static final String FIELD_(\w+)', src))
            if not fields:
                fields = set(re.findall(r'FIELD_(\w+)', src))
            result['filter_fields'] = sorted(fields)[:10]

            # Extract sort-related fields
            sorts = set(re.findall(r'SORT_(?:BY_)?(\w+)', src))
            result['sort_fields'] = sorted(sorts)

            return result

    return result


def generate_crud_tool_schema(op_id, crud_action, entity_info, description):
    """Generate OpenAPI operation for a CRUD endpoint."""
    entity_type = entity_info['entity_type']
    filter_desc = ', '.join(f.lower() for f in entity_info['filter_fields'][:5])

    if crud_action == 'getEntryList':
        return {
            'operationId': op_id,
            'summary': description,
            'description': (
                f"List/search {entity_type} entries via CRUD framework.\n"
                f"Available filter fields: {filter_desc or 'none documented'}\n"
                f"Request goes to POST /api/v2/crud/getEntryList"
            ),
            'tags': [],
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'required': ['data', 'context', 'clientInterface'],
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'required': ['entityType', 'search'],
                                    'properties': {
                                        'entityType': {
                                            'type': 'string',
                                            'enum': [entity_type],
                                            'description': f'Must be "{entity_type}"'
                                        },
                                        'search': {
                                            'type': 'object',
                                            'required': ['entriesCount', 'offset', 'sort', 'filter'],
                                            'properties': {
                                                'searchQuery': {
                                                    'type': 'string',
                                                    'description': 'Free-text search (optional)',
                                                    'default': ''
                                                },
                                                'entriesCount': {
                                                    'type': 'integer',
                                                    'description': 'Page size (max entries to return)',
                                                    'default': 10
                                                },
                                                'offset': {
                                                    'type': 'integer',
                                                    'description': 'Pagination offset',
                                                    'default': 0
                                                },
                                                'sort': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'fieldName': {'type': 'string', 'description': 'Field to sort by'},
                                                        'type': {'type': 'string', 'enum': ['ASCENDING', 'DESCENDING']}
                                                    }
                                                },
                                                'filter': {
                                                    'type': 'array',
                                                    'description': f'Filter conditions. Known fields: {filter_desc}',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'fieldName': {'type': 'string'},
                                                            'arguments': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'value': {}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                'context': {
                                    'type': 'object',
                                    'properties': {
                                        'authServiceToken': {'type': 'string', 'description': 'JWT auth token'}
                                    }
                                },
                                'fields': {
                                    'type': 'array',
                                    'items': {'type': 'string'},
                                    'default': []
                                },
                                'clientInterface': {
                                    'type': 'string',
                                    'default': 'desktop'
                                }
                            }
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'Entry list result',
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'data': {
                                        'type': 'object',
                                        'properties': {
                                            'totalEntries': {'type': 'string'},
                                            'entries': {'type': 'array', 'items': {'type': 'object'}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    elif crud_action == 'getEntryDetail':
        return {
            'operationId': op_id,
            'summary': description,
            'description': f"Get single {entity_type} entry by ID. POST /api/v2/crud/getEntryDetail",
            'tags': [],
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'required': ['data', 'context', 'clientInterface'],
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'required': ['entityType', 'entryId'],
                                    'properties': {
                                        'entityType': {'type': 'string', 'enum': [entity_type]},
                                        'entryId': {'type': 'string', 'description': 'Entry identifier'}
                                    }
                                },
                                'context': {
                                    'type': 'object',
                                    'properties': {
                                        'authServiceToken': {'type': 'string'}
                                    }
                                },
                                'fields': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
                                'clientInterface': {'type': 'string', 'default': 'desktop'}
                            }
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'Entry detail',
                    'content': {
                        'application/json': {
                            'schema': {'type': 'object'}
                        }
                    }
                }
            }
        }


def find_standard_op_in_spec(full_spec, op_id):
    """Find an operation by operationId in the full spec."""
    if not full_spec:
        return None, None
    for path_str, methods in full_spec.get('paths', {}).items():
        for method, operation in methods.items():
            if operation.get('operationId') == op_id:
                return path_str, operation
    return None, None


def generate_schemas(config, backend_path, full_spec):
    """Generate per-domain OpenAPI specs."""
    domain_specs = {}

    for domain, ops in config.items():
        spec = {
            'openapi': '3.1.0',
            'info': {
                'title': f'FPR {domain.capitalize()} API',
                'version': '2.0.0',
                'description': f'Auto-generated from exposed-ops.yaml — {domain} domain.'
            },
            'servers': [
                {'url': 'https://tool-api.fpr.traveloka.com', 'description': 'Production'},
                {'url': 'https://tool-flight-api.fpr.staging-traveloka.com', 'description': 'Flight Staging'},
                {'url': 'https://tool-api.fpr.staging-traveloka.com', 'description': 'Shared Staging'}
            ],
            'paths': {},
            'components': {'schemas': {}}
        }

        for op in ops:
            op_id = op['id']
            path = op['path']
            desc = op.get('description', '')

            crud_match = CRUD_PATTERN.match(path)

            if crud_match:
                # CRUD operation — scan backend
                crud_action = crud_match.group(1)
                entity_type = crud_match.group(2)
                entity_info = scan_crud_entity(backend_path, entity_type)
                operation = generate_crud_tool_schema(op_id, crud_action, entity_info, desc)

                api_path = f'/api/v2/crud/{crud_action}'
                if api_path not in spec['paths']:
                    spec['paths'][api_path] = {}
                # Use op_id as key to avoid collision
                operation['tags'] = [domain]
                spec['paths'][f'/api/v2/crud/{crud_action}#{op_id}'] = {'post': operation}

            else:
                # Standard API — look up in full spec first
                existing_path, existing_op = find_standard_op_in_spec(full_spec, op_id)

                if existing_op:
                    # Use existing schema from fprtool-full.json
                    operation = existing_op.copy()
                    operation['tags'] = [domain]
                    if existing_path not in spec['paths']:
                        spec['paths'][existing_path] = {}
                    spec['paths'][existing_path]['post'] = operation
                else:
                    # Generate minimal placeholder
                    api_path = f'/api/v2/{path}'
                    operation = {
                        'operationId': op_id,
                        'summary': desc,
                        'tags': [domain],
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'type': 'object', 'description': 'TODO: scan backend for schema'}
                                }
                            }
                        },
                        'responses': {
                            '200': {
                                'description': 'Success',
                                'content': {'application/json': {'schema': {'type': 'object'}}}
                            }
                        }
                    }
                    if api_path not in spec['paths']:
                        spec['paths'][api_path] = {}
                    spec['paths'][api_path]['post'] = operation

        domain_specs[domain] = spec

    return domain_specs


def main():
    parser = argparse.ArgumentParser(description='Generate per-domain OpenAPI schemas')
    parser.add_argument('--backend-path', default=DEFAULT_BACKEND,
                        help='Path to fpr-fprtool-backend repo')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT,
                        help='Output directory for generated schemas')
    args = parser.parse_args()

    backend_path = os.path.abspath(args.backend_path)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"📋 Loading config: {CONFIG_PATH}")
    config = load_config()

    print(f"📦 Backend path: {backend_path}")
    if not os.path.isdir(backend_path):
        print(f"⚠️  Backend not found — CRUD ops will have empty filter metadata", file=sys.stderr)

    full_spec = load_full_spec()
    if full_spec:
        print(f"📄 Loaded existing fprtool-full.json ({len(full_spec.get('paths', {}))} paths)")

    print(f"🔧 Generating schemas...")
    domain_specs = generate_schemas(config, backend_path, full_spec)

    total_ops = 0
    for domain, spec in domain_specs.items():
        domain_dir = os.path.join(output_dir, domain)
        os.makedirs(domain_dir, exist_ok=True)
        out_path = os.path.join(domain_dir, f'{domain}.json')
        with open(out_path, 'w') as f:
            json.dump(spec, f, indent=2)
        n_ops = sum(len(methods) for methods in spec['paths'].values())
        total_ops += n_ops
        print(f"  ✅ {domain}: {n_ops} ops → {out_path}")

    print(f"\n✅ Generated {total_ops} total operations across {len(domain_specs)} domains")

    # Merge all ops into fprtool-full.json (Gateway reads this file)
    if full_spec:
        merged_count = 0
        for domain, spec in domain_specs.items():
            for path, methods in spec['paths'].items():
                for method, op in methods.items():
                    op_id = op.get('operationId', '')
                    # Check if already in full spec
                    existing_path, existing_op = find_standard_op_in_spec(full_spec, op_id)
                    if not existing_op:
                        if path not in full_spec['paths']:
                            full_spec['paths'][path] = {}
                        full_spec['paths'][path][method] = op
                        merged_count += 1

        if merged_count > 0:
            with open(FULL_SPEC_PATH, 'w') as f:
                json.dump(full_spec, f, indent=2)
            print(f"  📦 Merged {merged_count} new ops into fprtool-full.json ({len(full_spec['paths'])} total)")
        else:
            print(f"  📦 fprtool-full.json already up-to-date ({len(full_spec['paths'])} paths)")


if __name__ == '__main__':
    main()
