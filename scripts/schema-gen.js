#!/usr/bin/env node
/**
 * Schema Generator
 * 
 * Reads: schemas/fprtool-full.json + config/exposed-ops.yaml
 * Outputs: schemas/{domain}/{domain}.yaml (OpenAPI 3.1 per domain)
 * 
 * TODO: Implement full generation logic
 * - Parse fprtool-full.json (55 paths, 4 tags/domains)
 * - Filter by exposed-ops.yaml whitelist
 * - Split into per-domain specs with proper operationIds
 * - Output as YAML
 */

const fs = require('fs');
const path = require('path');

// Load inputs
const fullSchema = JSON.parse(fs.readFileSync('schemas/fprtool-full.json', 'utf8'));
const yaml = fs.readFileSync('config/exposed-ops.yaml', 'utf8');

// Parse whitelist (simple YAML parser for flat structure)
const exposedOps = {};
let currentDomain = null;
for (const line of yaml.split('\n')) {
  if (line.match(/^(\w+):$/)) {
    currentDomain = line.replace(':', '').trim();
    exposedOps[currentDomain] = [];
  } else if (line.match(/^\s+-\s+\w+/) && currentDomain) {
    exposedOps[currentDomain].push(line.replace(/^\s+-\s+/, '').trim());
  }
}

console.log('Exposed operations per domain:');
for (const [domain, ops] of Object.entries(exposedOps)) {
  console.log(`  ${domain}: ${ops.length} operations`);
}

// TODO: Generate per-domain OpenAPI specs
// For now, just create placeholder files
for (const domain of Object.keys(exposedOps)) {
  const outDir = path.join('schemas', domain);
  fs.mkdirSync(outDir, { recursive: true });
  
  const spec = {
    openapi: '3.1.0',
    info: {
      title: `FPR ${domain.charAt(0).toUpperCase() + domain.slice(1)} API`,
      version: '1.0.0',
      description: `Flight Pricing & Revenue - ${domain} domain operations`
    },
    paths: {},
    // TODO: populate from fullSchema filtered by domain tag + whitelist
  };
  
  fs.writeFileSync(
    path.join(outDir, `${domain}.json`),
    JSON.stringify(spec, null, 2)
  );
}

console.log('\nGenerated placeholder specs in schemas/*/');
console.log('TODO: Implement full path splitting and YAML output');
