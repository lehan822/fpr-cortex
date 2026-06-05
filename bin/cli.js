#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SKILLS_SRC = path.resolve(__dirname, '..', 'skills');
const SKILLS_DST = path.join(process.env.HOME, '.agents', 'skills');
const DOMAINS = ['shared', 'pricing', 'supply', 'demand', 'config'];

const command = process.argv[2];

switch (command) {
  case 'install': install(); break;
  case 'uninstall': uninstall(); break;
  case 'generate':
    execSync('node ' + path.resolve(__dirname, '..', 'scripts', 'schema-gen.js'), { stdio: 'inherit' });
    break;
  default:
    console.log(`fpr-cortex — FPR AI Skills Manager\n\nCommands:\n  install      Symlink skills to ~/.agents/skills/fpr-{domain}\n  uninstall    Remove skill symlinks\n  generate     Regenerate per-domain OpenAPI schemas\n\nUsage: npx fpr-cortex install`);
}

function install() {
  fs.mkdirSync(SKILLS_DST, { recursive: true });
  for (const domain of DOMAINS) {
    const src = path.join(SKILLS_SRC, domain);
    const dst = path.join(SKILLS_DST, `fpr-${domain}`);
    if (!fs.existsSync(src)) { console.log(`  ⚠ skip ${domain}`); continue; }
    fs.rmSync(dst, { recursive: true, force: true });
    fs.symlinkSync(src, dst, 'dir');
    console.log(`  ✓ fpr-${domain} → ${path.relative(process.env.HOME, src)}`);
  }
  console.log(`\n✅ ${DOMAINS.length} skills installed to ${SKILLS_DST}`);
}

function uninstall() {
  let removed = 0;
  for (const domain of DOMAINS) {
    const dst = path.join(SKILLS_DST, `fpr-${domain}`);
    try {
      if (fs.lstatSync(dst).isSymbolicLink()) { fs.unlinkSync(dst); removed++; console.log(`  ✓ removed fpr-${domain}`); }
    } catch (e) { /* doesn't exist */ }
  }
  console.log(`\n✅ ${removed} skills removed`);
}
