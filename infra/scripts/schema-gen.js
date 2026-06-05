#!/usr/bin/env node
/**
 * schema-gen.js — Split fprtool-full.json into per-domain OpenAPI 3.1 specs
 * filtered by config/exposed-ops.yaml whitelist (exact operationId match).
 *
 * Usage: node scripts/schema-gen.js [--output-dir schemas/]
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

const ROOT = path.resolve(__dirname, '..', '..');
const FULL_SPEC_PATH = path.join(ROOT, 'infra', 'schemas', 'fprtool-full.json');
const WHITELIST_PATH = path.join(ROOT, 'infra', 'config', 'exposed-ops.yaml');
const OUTPUT_DIR = process.argv.includes('--output-dir')
  ? path.resolve(process.argv[process.argv.indexOf('--output-dir') + 1])
  : path.join(ROOT, 'infra', 'schemas');

const fullSpec = JSON.parse(fs.readFileSync(FULL_SPEC_PATH, 'utf8'));
const whitelist = yaml.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));

// Build Set per domain for O(1) lookup
const whitelistSets = {};
for (const [domain, ops] of Object.entries(whitelist)) {
  whitelistSets[domain] = new Set(ops);
}

// Split by domain tag + whitelist filter
const domainSpecs = {};

for (const [pathStr, methods] of Object.entries(fullSpec.paths || {})) {
  for (const [method, operation] of Object.entries(methods)) {
    if (!operation.tags || operation.tags.length === 0) continue;

    const domain = operation.tags[0];
    const operationId = operation.operationId || '';

    if (!whitelistSets[domain] || !whitelistSets[domain].has(operationId)) continue;

    if (!domainSpecs[domain]) {
      domainSpecs[domain] = {
        openapi: '3.1.0',
        info: {
          title: `FPR ${domain.charAt(0).toUpperCase() + domain.slice(1)} API`,
          version: fullSpec.info?.version || '1.0.0',
          description: `Auto-generated from fprtool-full.json — ${domain} domain only.`
        },
        servers: fullSpec.servers || [],
        paths: {},
        components: { schemas: {} }
      };
    }

    if (!domainSpecs[domain].paths[pathStr]) {
      domainSpecs[domain].paths[pathStr] = {};
    }
    domainSpecs[domain].paths[pathStr][method] = operation;
    collectRefs(operation, domainSpecs[domain].components.schemas);
  }
}

function collectRefs(obj, targetSchemas) {
  if (!obj || typeof obj !== 'object') return;
  if (obj.$ref && typeof obj.$ref === 'string') {
    const refPath = obj.$ref.replace('#/components/schemas/', '');
    if (fullSpec.components?.schemas?.[refPath] && !targetSchemas[refPath]) {
      targetSchemas[refPath] = fullSpec.components.schemas[refPath];
      collectRefs(targetSchemas[refPath], targetSchemas);
    }
  }
  for (const value of Object.values(obj)) {
    if (typeof value === 'object') collectRefs(value, targetSchemas);
  }
}

// Write output
let totalOps = 0;
for (const [domain, spec] of Object.entries(domainSpecs)) {
  if (Object.keys(spec.components.schemas).length === 0) delete spec.components;

  const domainDir = path.join(OUTPUT_DIR, domain);
  fs.mkdirSync(domainDir, { recursive: true });

  const outputPath = path.join(domainDir, `${domain}.json`);
  fs.writeFileSync(outputPath, JSON.stringify(spec, null, 2));

  const opCount = Object.values(spec.paths).reduce(
    (sum, methods) => sum + Object.keys(methods).length, 0
  );
  totalOps += opCount;
  console.log(`✓ ${domain}: ${opCount} operations → ${path.relative(ROOT, outputPath)}`);
}

console.log(`\nTotal: ${totalOps} operations across ${Object.keys(domainSpecs).length} domains`);
