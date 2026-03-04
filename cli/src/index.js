import { program } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';

const API = 'https://x402scout.com';
const VERSION = '1.0.0';

// ─── Brand colors ────────────────────────────────────────────────────────────
const nvg = chalk.hex('#39FF14');        // NVG green — brand color
const nvgBold = chalk.hex('#39FF14').bold;
const dim = chalk.dim;
const red = chalk.red;
const yellow = chalk.yellow;
const cyan = chalk.cyan;
const white = chalk.white;
const gray = chalk.gray;

// ─── Helpers ─────────────────────────────────────────────────────────────────
async function fetchJSON(url) {
  const res = await fetch(url, { headers: { 'User-Agent': `x402scout-cli/${VERSION}` } });
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${url}`);
  return res.json();
}

function scoreBadge(score) {
  if (score === null || score === undefined) return gray('  —  ');
  if (score >= 70) return nvg(`  ${score} `);
  if (score >= 40) return yellow(`  ${score} `);
  return red(`  ${score} `);
}

function scoreIcon(score) {
  if (score === null || score === undefined) return gray('?');
  if (score >= 70) return nvg('✅');
  if (score >= 40) return yellow('⚠️ ');
  return red('❌');
}

function formatPrice(price) {
  if (!price) return gray('  —  ');
  return cyan(`$${Number(price).toFixed(4)}`);
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len - 1) + '…' : str;
}

function header(title) {
  console.log('');
  console.log(nvgBold('🛰️  x402Scout') + dim(' — ') + white(title));
  console.log(dim('─'.repeat(60)));
}

function footer(count) {
  console.log('');
  console.log(dim(`  ${count} result${count !== 1 ? 's' : ''} · powered by `) + nvg('x402scout.com'));
  console.log('');
}

// ─── Commands ─────────────────────────────────────────────────────────────────

// SEARCH
async function cmdSearch(query) {
  header(`Searching for: "${query}"`);
  let data;
  try {
    data = await fetchJSON(`${API}/catalog`);
  } catch (e) {
    console.error(red(`  Error fetching catalog: ${e.message}`));
    process.exit(1);
  }
  const endpoints = data.endpoints || data;
  const q = query.toLowerCase();
  const results = endpoints.filter(s => {
    const name = (s.name || '').toLowerCase();
    const desc = (s.description || '').toLowerCase();
    const cat = (s.category || '').toLowerCase();
    const url = (s.url || '').toLowerCase();
    return name.includes(q) || desc.includes(q) || cat.includes(q) || url.includes(q);
  });

  if (results.length === 0) {
    console.log(yellow(`  No results found for "${query}"`));
    console.log(dim(`  Try: x402scout top 20, x402scout browse data, x402scout stats`));
    footer(0);
    return;
  }

  const table = new Table({
    head: [
      nvgBold('SERVICE'),
      nvgBold('TRUST'),
      nvgBold('CATEGORY'),
      nvgBold('PRICE'),
    ],
    colWidths: [32, 9, 12, 10],
    style: { head: [], border: ['dim'] },
    chars: {
      'top': '─', 'top-mid': '┬', 'top-left': '┌', 'top-right': '┐',
      'bottom': '─', 'bottom-mid': '┴', 'bottom-left': '└', 'bottom-right': '┘',
      'left': '│', 'left-mid': '├', 'mid': '─', 'mid-mid': '┼',
      'right': '│', 'right-mid': '┤', 'middle': '│',
    },
  });

  for (const s of results.slice(0, 20)) {
    table.push([
      `${scoreIcon(s.trust_score)} ${truncate(s.name || s.url, 27)}`,
      scoreBadge(s.trust_score),
      gray(truncate(s.category || 'misc', 10)),
      formatPrice(s.price_usd),
    ]);
  }

  console.log(table.toString());
  footer(Math.min(results.length, 20));
}

// SCAN
async function cmdScan(url) {
  header(`Scanning: ${url}`);
  console.log(dim('  Probing for x402 compliance…'));
  let data;
  try {
    data = await fetchJSON(`${API}/scan?url=${encodeURIComponent(url)}`);
  } catch (e) {
    console.error(red(`  Scan error: ${e.message}`));
    process.exit(1);
  }

  const score = data.compliance_score ?? data.trust_score;
  const grade = data.grade || '';

  console.log('');
  console.log(`  ${scoreIcon(score)} ${nvgBold('Trust Score:')} ${scoreBadge(score)}  ${white(grade)}`);
  console.log('');

  if (data.signals && data.signals.length > 0) {
    console.log(nvg('  Signals:'));
    for (const s of data.signals) {
      console.log(`    ${s}`);
    }
    console.log('');
  }

  if (data.issues && data.issues.length > 0) {
    console.log(yellow('  Issues:'));
    for (const i of data.issues) {
      console.log(`    ${i}`);
    }
    console.log('');
  }

  if (data.recommendation) {
    console.log(dim(`  Recommendation: ${data.recommendation}`));
  }

  console.log('');
}

// TOP
async function cmdTop(n) {
  const count = parseInt(n) || 10;
  header(`Top ${count} Services by Trust Score`);
  let data;
  try {
    data = await fetchJSON(`${API}/catalog`);
  } catch (e) {
    console.error(red(`  Error: ${e.message}`));
    process.exit(1);
  }
  const endpoints = data.endpoints || data;
  const sorted = [...endpoints]
    .filter(s => s.trust_score !== null && s.trust_score !== undefined)
    .sort((a, b) => (b.trust_score || 0) - (a.trust_score || 0))
    .slice(0, count);

  const table = new Table({
    head: [
      nvgBold('#'),
      nvgBold('SERVICE'),
      nvgBold('TRUST'),
      nvgBold('CATEGORY'),
      nvgBold('PRICE'),
    ],
    colWidths: [5, 30, 9, 12, 10],
    style: { head: [], border: ['dim'] },
    chars: {
      'top': '─', 'top-mid': '┬', 'top-left': '┌', 'top-right': '┐',
      'bottom': '─', 'bottom-mid': '┴', 'bottom-left': '└', 'bottom-right': '┘',
      'left': '│', 'left-mid': '├', 'mid': '─', 'mid-mid': '┼',
      'right': '│', 'right-mid': '┤', 'middle': '│',
    },
  });

  sorted.forEach((s, i) => {
    table.push([
      dim(`${i + 1}`),
      `${scoreIcon(s.trust_score)} ${truncate(s.name || s.url, 26)}`,
      scoreBadge(s.trust_score),
      gray(truncate(s.category || 'misc', 10)),
      formatPrice(s.price_usd),
    ]);
  });

  console.log(table.toString());
  footer(sorted.length);
}

// BROWSE
async function cmdBrowse(category) {
  const label = category ? `Category: ${category}` : 'All Categories';
  header(label);
  let data;
  try {
    data = await fetchJSON(`${API}/catalog`);
  } catch (e) {
    console.error(red(`  Error: ${e.message}`));
    process.exit(1);
  }
  const endpoints = data.endpoints || data;
  const filtered = category
    ? endpoints.filter(s => (s.category || '').toLowerCase() === category.toLowerCase())
    : endpoints;

  if (filtered.length === 0) {
    console.log(yellow(`  No services found in category: "${category}"`));
    // Show available categories
    const cats = [...new Set(endpoints.map(s => s.category || 'misc'))].sort();
    console.log(dim('  Available categories: ') + cats.map(c => nvg(c)).join(dim(', ')));
    console.log('');
    return;
  }

  // Sort by trust score desc
  const sorted = [...filtered].sort((a, b) => (b.trust_score || 0) - (a.trust_score || 0));
  const display = sorted.slice(0, 25);

  const table = new Table({
    head: [
      nvgBold('SERVICE'),
      nvgBold('TRUST'),
      nvgBold('PRICE'),
      nvgBold('URL'),
    ],
    colWidths: [28, 9, 10, 30],
    style: { head: [], border: ['dim'] },
    chars: {
      'top': '─', 'top-mid': '┬', 'top-left': '┌', 'top-right': '┐',
      'bottom': '─', 'bottom-mid': '┴', 'bottom-left': '└', 'bottom-right': '┘',
      'left': '│', 'left-mid': '├', 'mid': '─', 'mid-mid': '┼',
      'right': '│', 'right-mid': '┤', 'middle': '│',
    },
  });

  for (const s of display) {
    table.push([
      `${scoreIcon(s.trust_score)} ${truncate(s.name || s.url, 24)}`,
      scoreBadge(s.trust_score),
      formatPrice(s.price_usd),
      dim(truncate(s.url, 28)),
    ]);
  }

  console.log(table.toString());
  if (filtered.length > 25) {
    console.log(dim(`  Showing 25 of ${filtered.length} results`));
  }
  footer(Math.min(display.length, filtered.length));
}

// STATS
async function cmdStats() {
  header('Ecosystem Stats');
  let data;
  try {
    data = await fetchJSON(`${API}/catalog`);
  } catch (e) {
    console.error(red(`  Error: ${e.message}`));
    process.exit(1);
  }
  const endpoints = data.endpoints || data;
  const total = endpoints.length;

  // Category breakdown
  const catMap = {};
  for (const s of endpoints) {
    const c = s.category || 'misc';
    catMap[c] = (catMap[c] || 0) + 1;
  }
  const cats = Object.entries(catMap).sort((a, b) => b[1] - a[1]);

  // Trust score distribution
  const withScore = endpoints.filter(s => s.trust_score !== null && s.trust_score !== undefined);
  const avgScore = withScore.length > 0
    ? Math.round(withScore.reduce((sum, s) => sum + s.trust_score, 0) / withScore.length)
    : null;
  const high = withScore.filter(s => s.trust_score >= 70).length;
  const mid = withScore.filter(s => s.trust_score >= 40 && s.trust_score < 70).length;
  const low = withScore.filter(s => s.trust_score < 40).length;

  // Health
  const healthy = endpoints.filter(s => s.health_status === 'healthy' || s.health_status === 'up').length;
  const priced = endpoints.filter(s => s.price_usd && s.price_usd > 0).length;

  console.log('');
  console.log(`  ${nvgBold('Total Services:')}   ${nvg(total)}`);
  console.log(`  ${nvgBold('Avg Trust Score:')}  ${scoreBadge(avgScore)}`);
  console.log(`  ${nvgBold('Healthy:')}          ${nvg(healthy)} ${dim(`/ ${total}`)}`);
  console.log(`  ${nvgBold('With Pricing:')}     ${cyan(priced)} ${dim(`/ ${total}`)}`);
  console.log('');
  console.log(`  ${nvgBold('Trust Distribution:')}`);
  console.log(`    ${nvg('●')} High (≥70):  ${nvg(high)}`);
  console.log(`    ${yellow('●')} Mid  (40–69): ${yellow(mid)}`);
  console.log(`    ${red('●')} Low  (<40):  ${red(low)}`);
  console.log('');
  console.log(`  ${nvgBold('Top Categories:')}`);
  for (const [cat, count] of cats.slice(0, 8)) {
    const bar = nvg('█'.repeat(Math.round(count / total * 20)));
    const pad = cat.padEnd(12);
    console.log(`    ${nvg(pad)}  ${bar} ${dim(count)}`);
  }
  console.log('');
  console.log(dim('  Source: x402scout.com · Updates every 6h · ') + nvg(total + ' services'));
  console.log('');
}

// ─── CLI setup ────────────────────────────────────────────────────────────────
program
  .name('x402scout')
  .description(nvgBold('🛰️  x402Scout') + ' — Terminal client for the x402 agent economy')
  .version(VERSION, '-v, --version', 'Show version')
  .addHelpText('beforeAll', '\n' + nvgBold('🛰️  x402Scout') + dim(' — Discover x402-enabled APIs from your terminal') + '\n');

program
  .command('search <query>')
  .description('Search services by keyword')
  .action(cmdSearch);

program
  .command('scan <url>')
  .description('Scan a URL for x402 compliance')
  .action(cmdScan);

program
  .command('top [n]')
  .description('Top N services by trust score (default: 10)')
  .action(cmdTop);

program
  .command('browse [category]')
  .description('Browse by category: data, agent, utility, text, …')
  .action(cmdBrowse);

program
  .command('stats')
  .description('Ecosystem stats: total services, categories, trust scores')
  .action(cmdStats);

// Default: show help if no command given
if (process.argv.length <= 2) {
  program.outputHelp();
  process.exit(0);
}

program.parse(process.argv);
