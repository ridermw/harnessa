const { v4: uuidv4 } = require('uuid');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Planner phase: analyze code structure (1-2s)
async function runPlanner(code, language) {
  await sleep(randomBetween(1000, 2000));

  const lines = code.split('\n');
  const lineCount = lines.length;
  const functionMatches = code.match(/function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*\{|def\s+\w+|func\s+\w+/g) || [];
  const hasClasses = /class\s+\w+/.test(code);

  return {
    summary: `Analyzed ${lineCount} lines of ${language} code with ${functionMatches.length} function(s)${hasClasses ? ' and class definitions' : ''}.`,
    focusAreas: [
      'Error handling patterns',
      'Code complexity assessment',
      'Security vulnerability scan',
      'Code quality indicators',
      'Debugging artifact detection',
    ],
    complexity: lineCount > 100 ? 'high' : lineCount > 30 ? 'medium' : 'low',
    lineCount,
    functionCount: functionMatches.length,
  };
}

// Generator phase: deep code analysis (2-3s)
async function runGenerator(code, language, plannerOutput) {
  await sleep(randomBetween(2000, 3000));

  const bugs = [];
  const lines = code.split('\n');

  // Check for console.log debugging artifacts
  lines.forEach((line, i) => {
    if (/console\.(log|debug|info|warn)\s*\(/.test(line)) {
      bugs.push({
        id: uuidv4(),
        type: 'debugging-artifact',
        severity: 'low',
        line: i + 1,
        description: `Debugging statement found: ${line.trim().substring(0, 60)}`,
        suggestion: 'Remove console statements before production or use a proper logging library.',
      });
    }
  });

  // Check for TODO/FIXME comments
  lines.forEach((line, i) => {
    if (/\/\/\s*(TODO|FIXME|HACK|XXX|BUG)/i.test(line)) {
      bugs.push({
        id: uuidv4(),
        type: 'unresolved-todo',
        severity: 'medium',
        line: i + 1,
        description: `Unresolved marker: ${line.trim().substring(0, 60)}`,
        suggestion: 'Address or remove TODO/FIXME comments before shipping.',
      });
    }
  });

  // Check for hardcoded secrets
  lines.forEach((line, i) => {
    if (/(?:password|secret|api_key|apikey|token|auth)\s*[:=]\s*['"][^'"]{4,}/i.test(line)) {
      bugs.push({
        id: uuidv4(),
        type: 'hardcoded-secret',
        severity: 'critical',
        line: i + 1,
        description: `Possible hardcoded secret detected on line ${i + 1}.`,
        suggestion: 'Use environment variables or a secrets manager instead of hardcoding credentials.',
      });
    }
  });

  // Check for missing error handling (try/catch)
  const hasTryCatch = /try\s*\{/.test(code);
  const hasAsync = /async\s/.test(code);
  const hasPromise = /\.then\s*\(|Promise/.test(code);
  if ((hasAsync || hasPromise) && !hasTryCatch) {
    bugs.push({
      id: uuidv4(),
      type: 'missing-error-handling',
      severity: 'high',
      line: null,
      description: 'Async code detected without try/catch error handling.',
      suggestion: 'Wrap async operations in try/catch blocks to handle failures gracefully.',
    });
  }

  // Check for long functions (>100 lines proxy: check total length)
  if (plannerOutput.lineCount > 100 && plannerOutput.functionCount <= 1) {
    bugs.push({
      id: uuidv4(),
      type: 'long-function',
      severity: 'medium',
      line: null,
      description: `Code is ${plannerOutput.lineCount} lines with only ${plannerOutput.functionCount} function(s). Functions may be too long.`,
      suggestion: 'Break large functions into smaller, focused helper functions for better maintainability.',
    });
  }

  // Check for deeply nested code
  let maxIndent = 0;
  lines.forEach((line) => {
    const indent = line.match(/^(\s*)/)[1].length;
    if (indent > maxIndent) maxIndent = indent;
  });
  if (maxIndent > 16) {
    bugs.push({
      id: uuidv4(),
      type: 'deep-nesting',
      severity: 'medium',
      line: null,
      description: `Code has deeply nested blocks (indentation depth: ${maxIndent} spaces).`,
      suggestion: 'Reduce nesting with early returns, guard clauses, or by extracting helper functions.',
    });
  }

  // Check for magic numbers
  const magicNumbers = code.match(/[^a-zA-Z0-9_](\d{2,})[^a-zA-Z0-9_:/.]/g) || [];
  if (magicNumbers.length > 3) {
    bugs.push({
      id: uuidv4(),
      type: 'magic-numbers',
      severity: 'low',
      line: null,
      description: `Found ${magicNumbers.length} potential magic numbers in the code.`,
      suggestion: 'Extract magic numbers into named constants for better readability.',
    });
  }

  return {
    findings: bugs,
    analysisNotes: `Deep analysis of ${plannerOutput.lineCount} lines complete. Found ${bugs.length} issue(s).`,
  };
}

// Evaluator phase: generate scores and verdict (2-3s)
async function runEvaluator(code, language, plannerOutput, generatorOutput) {
  await sleep(randomBetween(2000, 3000));

  const bugs = generatorOutput.findings;
  const criticalCount = bugs.filter((b) => b.severity === 'critical').length;
  const highCount = bugs.filter((b) => b.severity === 'high').length;
  const mediumCount = bugs.filter((b) => b.severity === 'medium').length;
  const lowCount = bugs.filter((b) => b.severity === 'low').length;

  // Base scores
  let readability = 8;
  let maintainability = 8;
  let performance = 8;
  let security = 9;
  let errorHandling = 8;

  // Deduct based on findings
  readability -= lowCount * 0.5 + mediumCount * 1;
  maintainability -= mediumCount * 1.5 + highCount * 1;
  security -= criticalCount * 3 + highCount * 1;
  errorHandling -= highCount * 2;
  performance -= mediumCount * 0.5;

  // Complexity penalty
  if (plannerOutput.complexity === 'high') {
    maintainability -= 1;
    readability -= 1;
  }

  // Bonus for clean code
  if (bugs.length === 0) {
    readability = Math.min(readability + 1, 10);
    maintainability = Math.min(maintainability + 1, 10);
  }

  const clamp = (v) => Math.max(1, Math.min(10, Math.round(v * 10) / 10));

  const scores = {
    readability: clamp(readability),
    maintainability: clamp(maintainability),
    performance: clamp(performance),
    security: clamp(security),
    errorHandling: clamp(errorHandling),
  };

  const overall = Math.round(
    ((scores.readability + scores.maintainability + scores.performance + scores.security + scores.errorHandling) / 5) * 10
  ) / 10;

  const verdict = criticalCount > 0 ? 'FAIL' : overall >= 7 ? 'PASS' : overall >= 5 ? 'NEEDS_IMPROVEMENT' : 'FAIL';

  return {
    scores,
    overall,
    verdict,
    summary:
      verdict === 'PASS'
        ? `Code quality is good (${overall}/10). ${bugs.length === 0 ? 'No issues found.' : `${bugs.length} minor issue(s) to address.`}`
        : verdict === 'NEEDS_IMPROVEMENT'
          ? `Code needs improvement (${overall}/10). Found ${bugs.length} issue(s) requiring attention.`
          : `Code does not meet quality standards (${overall}/10). ${criticalCount} critical issue(s) found.`,
  };
}

async function analyzeCode(code, language, onPhaseUpdate) {
  // Phase 1: Planner
  onPhaseUpdate?.('planner', 'running');
  const plannerOutput = await runPlanner(code, language);
  onPhaseUpdate?.('planner', 'done', plannerOutput);

  // Phase 2: Generator
  onPhaseUpdate?.('generator', 'running');
  const generatorOutput = await runGenerator(code, language, plannerOutput);
  onPhaseUpdate?.('generator', 'done', generatorOutput);

  // Phase 3: Evaluator
  onPhaseUpdate?.('evaluator', 'running');
  const evaluatorOutput = await runEvaluator(code, language, plannerOutput, generatorOutput);
  onPhaseUpdate?.('evaluator', 'done', evaluatorOutput);

  return {
    plannerOutput,
    generatorOutput,
    evaluatorOutput,
    scores: evaluatorOutput.scores,
    overall: evaluatorOutput.overall,
    bugs: generatorOutput.findings,
    verdict: evaluatorOutput.verdict,
    summary: evaluatorOutput.summary,
  };
}

module.exports = { analyzeCode };
