import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import { scenes, sceneAliases, type SceneId } from './content/scenes';
import { OperatorRail, RailToggleButton, useRailState } from './components/navigation/OperatorRail';
import { DiagramRenderer } from './diagrams/renderers';
import {
  diagram01TrioPipeline,
  diagram02GoodhartBoundary,
  diagram03SprintContract,
  diagram04FilesHandoff,
  diagram05TelemetryStack,
  diagram06HeadlineResult,
  diagram09IndustryTimeline,
  diagram10EcosystemNetwork,
  diagram11ShowcaseRebuild,
  diagram12DemoFlow,
  diagram13DecisionTree,
  diagram14ModelTiering,
} from './diagrams/specs';
import {
  heroMetrics,
  anthropicSparkComparison,
  articleVsHarnessa,
  anthropicQuote,
  wallContext,
  wallEvaluation,
  adversarialQuote,
  goodhartBoundary,
  sprintContracts,
  telemetryDetail,
  karpathyQuote,
  criticRules,
  criteriaThresholds,
  experimentDesign,
  benchmarkMatrix,
  evidenceMetrics,
  scorecardRows,
  difficultyZones,
  iterationSeries,
  claimsConfirmed,
  claimsPartial,
  claimsInconclusive,
  showcaseKeyLessons,
  showcaseComparison,
  demoFlow,
  closingQuote,
  appendixRuns,
  appendixCriteria,
  appendixCaveats,
  citations,
} from './content/acts';

/* ────────────────────────────────────────────────────────────────────
   Hooks
   ──────────────────────────────────────────────────────────────────── */

function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setPrefersReducedMotion(mediaQuery.matches);
    onChange();
    mediaQuery.addEventListener('change', onChange);
    return () => mediaQuery.removeEventListener('change', onChange);
  }, []);

  return prefersReducedMotion;
}

function useAnimatedNumber(
  target: number | undefined,
  active: boolean,
  decimals = 0,
): string {
  const [value, setValue] = useState(target ?? 0);
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (target === undefined) {
      return;
    }

    if (!active || reducedMotion) {
      setValue(target);
      return;
    }

    const duration = 900;
    const start = performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      setValue(target * (1 - Math.pow(1 - progress, 3)));

      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, active, reducedMotion]);

  return value.toFixed(decimals);
}

/* ────────────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────────────── */

function clampSceneId(value: string | null): SceneId | null {
  if (!value) {
    return null;
  }

  const match = scenes.find((scene) => scene.id === value);
  if (match) {
    return match.id;
  }

  // Support old scene IDs via alias map
  const aliased = sceneAliases[value];
  return aliased ?? null;
}

/* ────────────────────────────────────────────────────────────────────
   App
   ──────────────────────────────────────────────────────────────────── */

function App(): JSX.Element {
  const reducedMotion = usePrefersReducedMotion();
  const { railOpen, toggleRail } = useRailState();
  const initialScene = useMemo<SceneId>(() => {
    if (typeof window === 'undefined') {
      return 'hero';
    }
    return clampSceneId(window.location.hash.replace('#', '')) ?? 'hero';
  }, []);
  const [activeScene, setActiveScene] = useState<SceneId>(initialScene);
  const [appendixOpen, setAppendixOpen] = useState(false);
  const hashReady = useRef(false);
  const navigationLockUntil = useRef(0);
  const sceneRefs = useRef(
    Object.fromEntries(scenes.map((s) => [s.id, null])) as Record<SceneId, HTMLElement | null>,
  );

  const setSceneRef = useCallback(
    (id: SceneId) => (node: HTMLElement | null) => {
      sceneRefs.current[id] = node;
    },
    [],
  );

  const scrollToScene = useCallback(
    (id: SceneId, smooth = true) => {
      const section = document.getElementById(id);
      if (!section) {
        return;
      }

      const top = section.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: Math.max(0, top - 16),
        behavior: smooth && !reducedMotion ? 'smooth' : 'auto',
      });
    },
    [reducedMotion],
  );

  const jumpToScene = useCallback(
    (id: SceneId, smooth = true, lockMs = 450) => {
      navigationLockUntil.current = Date.now() + lockMs;
      setActiveScene(id);
      scrollToScene(id, smooth);
    },
    [scrollToScene],
  );

  const reinforceHashJump = useCallback(
    (id: SceneId, delays: readonly number[]) => {
      const timers = delays.map((delay, index) =>
        window.setTimeout(() => {
          navigationLockUntil.current = Date.now() + 900;
          if (index === 0) {
            setActiveScene(id);
          }
          scrollToScene(id, false);
        }, delay),
      );

      return () => timers.forEach((timer) => window.clearTimeout(timer));
    },
    [scrollToScene],
  );

  const sceneIndex = useMemo(
    () => scenes.findIndex((scene) => scene.id === activeScene),
    [activeScene],
  );

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = [...entries]
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

        if (visibleEntry && Date.now() >= navigationLockUntil.current) {
          setActiveScene(visibleEntry.target.id as SceneId);
        }
      },
      {
        threshold: [0.2, 0.4, 0.65],
        rootMargin: '-15% 0px -20% 0px',
      },
    );

    scenes.forEach((scene) => {
      const section = sceneRefs.current[scene.id];
      if (section) {
        observer.observe(section);
      }
    });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const hashTarget = clampSceneId(window.location.hash.replace('#', ''));
    if (hashTarget) {
      const cancelJump = reinforceHashJump(hashTarget, [120, 420, 920]);
      const readyTimer = window.setTimeout(() => {
        hashReady.current = true;
      }, 120);
      return () => {
        window.clearTimeout(readyTimer);
        cancelJump();
      };
    }
    hashReady.current = true;
  }, [reinforceHashJump]);

  useEffect(() => {
    const onHashChange = () => {
      const hashTarget = clampSceneId(window.location.hash.replace('#', ''));
      if (hashTarget) {
        reinforceHashJump(hashTarget, [0, 260, 720]);
      }
    };

    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, [reinforceHashJump]);

  useEffect(() => {
    if (!hashReady.current) {
      return;
    }
    window.history.replaceState(null, '', `#${activeScene}`);
  }, [activeScene]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
      ) {
        return;
      }

      if (event.key === 'Escape') {
        setAppendixOpen(false);
        return;
      }

      if (event.key.toLowerCase() === 'a') {
        event.preventDefault();
        setAppendixOpen((current) => !current);
        return;
      }

      if (appendixOpen) {
        return;
      }

      const nextScene = scenes[sceneIndex + 1]?.id;
      const previousScene = scenes[sceneIndex - 1]?.id;

      if (['ArrowDown', 'PageDown', 'j', 'J', ' '].includes(event.key) && nextScene) {
        event.preventDefault();
        jumpToScene(nextScene);
      }

      if (['ArrowUp', 'PageUp', 'k', 'K'].includes(event.key) && previousScene) {
        event.preventDefault();
        jumpToScene(previousScene);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [appendixOpen, jumpToScene, sceneIndex]);

  return (
    <div className="presentation-app" data-rail-open={railOpen}>
      <div className="ambient-grid" />
      <header className="topbar">
        <div className="topbar__brand">
          <span className="chrome-pill">Harnessa // Research Briefing</span>
          <div>
            <strong>The Adversarial Architecture</strong>
            <p>Matthew Williams — Senior SWE (MSFT)</p>
          </div>
        </div>
        <div className="topbar__status">
          <span className="chrome-pill chrome-pill--active">
            {scenes[sceneIndex]?.short} / {scenes.length}
          </span>
          <span className="topbar__scene">{scenes[sceneIndex]?.title}</span>
          <RailToggleButton railOpen={railOpen} onToggle={toggleRail} />
          <button
            className="chrome-button"
            type="button"
            onClick={() => setAppendixOpen(true)}
          >
            Appendix
          </button>
        </div>
      </header>

      <OperatorRail
        scenes={scenes}
        activeScene={activeScene}
        onJumpToScene={(id) => jumpToScene(id as SceneId)}
        appendixOpen={appendixOpen}
      />

      <div className="mobile-warning">
        Optimized for desktop / projector. Mobile keeps all content, but the intended experience is widescreen.
      </div>

      <main className="scene-stack">

        {/* ── Act 1 — Thesis & Failure Modes ──────────────────────────── */}

        <section
          id="hero"
          ref={setSceneRef('hero')}
          className="scene layout-hero"
          data-act="1"
          data-active={activeScene === 'hero'}
        >
          <div className="scene__content hero-layout">
            <div className="hero-copy">
              <span className="scene__eyebrow reveal stagger-1">Anthropic article → Harnessa evidence → deployment pattern</span>
              <h1 className="scene__title reveal stagger-2">
                Better AI software comes from agents that disagree.
              </h1>
              <p className="scene__lede reveal stagger-3">
                Anthropic framed the idea. Harnessa tested it. The result was not marginal polish —
                it was a broken solo full-stack build turning into a working trio system.
              </p>
              <div className="hero-actions reveal stagger-4">
                <button className="chrome-button chrome-button--primary" onClick={() => jumpToScene('headline-result')} type="button">
                  Jump to the headline
                </button>
                <button className="chrome-button" onClick={() => setAppendixOpen(true)} type="button">
                  Open appendix
                </button>
              </div>
              <div className="hero-note reveal stagger-5">
                <span className="chrome-pill">Caveat</span>
                N=11 total runs. Directional, not final science — but the full-stack result is categorical, not subtle.
              </div>
            </div>
            <div className="hero-visual reveal-scale stagger-3">
              <HeroSignal />
              <div className="hero-metrics">
                {heroMetrics.map((metric) => (
                  <MetricCard
                    key={metric.label}
                    metric={metric}
                    active={activeScene === 'hero'}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="anthropic-spark"
          ref={setSceneRef('anthropic-spark')}
          className="scene layout-editorial"
          data-act="1"
          data-active={activeScene === 'anthropic-spark'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Origin"
              title="From Anthropic article to tested evidence"
              lede="Anthropic published the harness idea. Harnessa built it, instrumented it, and ran controlled experiments against it. The output is not incrementally better — it is categorically different."
            />
            <div className="scorecard-list">
              {anthropicSparkComparison.map((row, index) => (
                <article
                  key={row.approach}
                  className={row.result === 'FAIL' ? 'score-row score-row--featured reveal' : 'score-row reveal'}
                  style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}
                >
                  <div className="score-row__header">
                    <div>
                      <span className="panel__tag">{row.result}</span>
                      <h3>{row.approach}</h3>
                    </div>
                    <div className="score-row__winner">{row.cost} / {row.time}</div>
                  </div>
                  <p>{row.note}</p>
                </article>
              ))}
            </div>
            <blockquote className="quote-strip reveal delay-3">
              "{anthropicQuote.text}"
              <cite>{anthropicQuote.author}</cite>
            </blockquote>
            <div className="scorecard-list" style={{ marginTop: 'var(--space-4)' }}>
              {articleVsHarnessa.map((row, index) => (
                <article key={row.dimension} className="score-row reveal" style={{ transitionDelay: `${(index + 3) * 80}ms` } as CSSProperties}>
                  <div className="score-row__header">
                    <div>
                      <span className="panel__tag">{row.verdict === 'confirmed' ? '✅' : row.verdict === 'partial' ? '⚠️' : '❓'} {row.verdict}</span>
                      <h3>{row.dimension}</h3>
                    </div>
                  </div>
                  <p><strong>Article:</strong> {row.article}</p>
                  <p><strong>Harnessa:</strong> {row.harnessa}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section
          id="wall-context"
          ref={setSceneRef('wall-context')}
          className="scene layout-split"
          data-act="1"
          data-active={activeScene === 'wall-context'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Failure Mode"
                title="Wall 1 — Context degradation"
                lede="Long-running AI coding sessions lose coherence as context grows. The agent hedges, summarizes, and prematurely wraps up. More tokens ≠ better output."
              />
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <article className="panel reveal delay-1">
                <span className="panel__tag">{wallContext.title}</span>
                <p className="panel__body">{wallContext.body}</p>
                <div className="signal-strip">{wallContext.signal}</div>
              </article>
              <article className="panel reveal delay-2" style={{ marginTop: 'var(--space-3)' }}>
                <span className="panel__tag">Why it matters</span>
                <p className="panel__body">
                  A 200K context window does not guarantee a coherent 200K-token work session.
                  The agent's effective reasoning window is much smaller than the advertised limit.
                </p>
                <div className="signal-strip">Bigger window ≠ longer coherence</div>
              </article>
            </div>
          </div>
        </section>

        <section
          id="wall-evaluation"
          ref={setSceneRef('wall-evaluation')}
          className="scene layout-split"
          data-act="1"
          data-active={activeScene === 'wall-evaluation'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Failure Mode"
                title="Wall 2 — Self-evaluation failure"
                lede="The more dangerous wall. When the same system builds and judges, quality gets flattered. The agent names real issues, then talks itself into shipping anyway."
              />
              <blockquote className="quote-strip reveal delay-3">
                "{adversarialQuote.text}"
                <cite>{adversarialQuote.author}</cite>
              </blockquote>
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <article className="panel reveal delay-1">
                <span className="panel__tag">{wallEvaluation.title}</span>
                <p className="panel__body">{wallEvaluation.body}</p>
                <div className="signal-strip">{wallEvaluation.signal}</div>
              </article>
              <article className="panel reveal delay-2" style={{ marginTop: 'var(--space-3)' }}>
                <span className="panel__tag">Observed in Harnessa</span>
                <p className="panel__body">
                  Benchmark 2 (TypeScript): the solo agent scored functionality at 8/10 despite 50% of tests failing.
                  The evaluator was too close to its own work to be honest.
                </p>
                <div className="signal-strip">func=8, test pass rate=50%</div>
              </article>
            </div>
          </div>
        </section>

        <section
          id="adversarial-insight"
          ref={setSceneRef('adversarial-insight')}
          className="scene layout-statement"
          data-act="1"
          data-active={activeScene === 'adversarial-insight'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Core Idea"
              title="What if builder and critic were different agents?"
              lede="GANs proved that adversarial tension between a generator and discriminator creates outputs neither achieves alone. The same principle applies to code quality."
            />
          </div>
        </section>

        {/* ── Act 2 — Architecture & Control Surfaces ─────────────────── */}

        <section
          id="trio-pipeline"
          ref={setSceneRef('trio-pipeline')}
          className="scene layout-showcase"
          data-act="2"
          data-active={activeScene === 'trio-pipeline'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="System View"
              title="Planner → Generator ↔ Evaluator"
              lede="The architecture matters more than one bigger context window. Separate roles, explicit contracts, and independent evaluation create the quality leverage."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram01TrioPipeline} />
            </div>
          </div>
        </section>

        <section
          id="goodhart-boundary"
          ref={setSceneRef('goodhart-boundary')}
          className="scene layout-compare"
          data-act="2"
          data-active={activeScene === 'goodhart-boundary'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Isolation"
              title="The Goodhart boundary"
              lede={`"${goodhartBoundary.principle}" — Goodhart's Law means that if the generator can see the acceptance tests, it will optimize for passing them rather than building genuinely correct software.`}
            />
            <div className="compare-panels">
              <div className="compare-panel compare-panel--fail">
                <span className="panel__tag" style={{ color: 'var(--signal-green)' }}>Generator sees</span>
                <ul style={{ margin: '0.5rem 0', paddingLeft: '1.2rem', color: 'var(--muted)' }}>
                  {goodhartBoundary.generatorTree.map(f => <li key={f}><code>{f}</code></li>)}
                </ul>
                <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                  Cannot see <code>_eval/</code> — physically excluded via <code>git sparse-checkout</code>.
                </p>
              </div>
              <div className="compare-divider" />
              <div className="compare-panel compare-panel--pass">
                <span className="panel__tag" style={{ color: 'var(--signal-amber)' }}>Evaluator sees</span>
                <ul style={{ margin: '0.5rem 0', paddingLeft: '1.2rem', color: 'var(--muted)' }}>
                  {goodhartBoundary.evaluatorTree.map(f => <li key={f}><code>{f}</code></li>)}
                </ul>
                <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                  Full access including <code>_eval/</code> — acceptance tests, fixtures, and hidden grading criteria.
                </p>
              </div>
            </div>
            <div className="reveal-scale stagger-4" style={{ marginTop: 'var(--space-4)' }}>
              <DiagramRenderer spec={diagram02GoodhartBoundary} />
            </div>
            <div className="aggregate-strip reveal delay-3" style={{ marginTop: 'var(--space-3)' }}>
              <div>
                <span className="chrome-pill">Mechanism</span>
                <strong>{goodhartBoundary.mechanism}</strong>
              </div>
            </div>
          </div>
        </section>

        <section
          id="sprint-contracts"
          ref={setSceneRef('sprint-contracts')}
          className="scene layout-showcase"
          data-act="2"
          data-active={activeScene === 'sprint-contracts'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Contracts"
              title="Spec-driven sprint agreements"
              lede="The planner creates the contract. The generator proposes. The evaluator holds the line. No one agent decides when 'done' means done."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram03SprintContract} />
              <div className="aggregate-strip reveal delay-3" style={{ marginTop: 'var(--space-3)' }}>
                <p>{sprintContracts.keyInsight}</p>
              </div>
            </div>
          </div>
        </section>

        <section
          id="files-on-disk"
          ref={setSceneRef('files-on-disk')}
          className="scene layout-split"
          data-act="2"
          data-active={activeScene === 'files-on-disk'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Communication"
                title="Files on disk, not chat history"
                lede="Agents communicate through files, not message threads. Every handoff is an artifact on disk — auditable, resumable, and free from context window pressure."
              />
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram04FilesHandoff} />
            </div>
          </div>
        </section>

        <section
          id="telemetry-layer"
          ref={setSceneRef('telemetry-layer')}
          className="scene layout-editorial"
          data-act="2"
          data-active={activeScene === 'telemetry-layer'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Instrumentation"
              title="Every run produces structured evidence"
              lede={telemetryDetail.description}
            />
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram05TelemetryStack} />
            </div>
          </div>
        </section>

        {/* ── Act 3 — Critic Calibration & Experimental Setup ──────────── */}

        <section
          id="karpathy-problem"
          ref={setSceneRef('karpathy-problem')}
          className="scene layout-editorial"
          data-act="3"
          data-active={activeScene === 'karpathy-problem'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Skepticism Engine"
              title="The Karpathy problem"
              lede={karpathyQuote.insight}
            />
            <div className="critic-grid">
              <article className="panel quote-panel reveal delay-1">
                <span className="panel__tag">Karpathy problem</span>
                <p className="quote-panel__text">
                  "{karpathyQuote.text}"
                </p>
                <cite>{karpathyQuote.author}</cite>
              </article>
              <article className="panel verdict-panel reveal delay-2">
                <span className="panel__tag">Evaluator posture</span>
                <div className="verdict-code">
                  <pre>{`{ "functionality": 1, "verdict": "FAIL" }`}</pre>
                  <pre>{`{ "functionality": 10, "verdict": "PASS" }`}</pre>
                </div>
                <p>
                  The same generator can move from broken to shippable if the critic stays skeptical enough to hold the line.
                </p>
              </article>
            </div>
            <div className="two-up-grid">
              <article className="panel reveal delay-3">
                <span className="panel__tag">The Pattern</span>
                <p className="panel__body">An LLM asked to review its own work will find real issues — then rationalize them away. It's not that the model can't identify problems. It's that the same model that created the code is incentivized to defend it.</p>
              </article>
              <article className="panel reveal delay-4">
                <span className="panel__tag">The Harnessa Solution</span>
                <p className="panel__body">Separate the builder from the critic. The evaluator cannot see the generator's reasoning or approach. It only sees the output, the tests, and the criteria. This eliminates self-review bias.</p>
              </article>
            </div>
            <div className="panel reveal delay-5">
              <span className="panel__tag">Why this matters for harness design</span>
              <p className="panel__body">If the evaluator is too agreeable, the feedback loop produces diminishing returns. Calibration — anti-sycophancy rules, threshold-based gating, rubber-stamp detection — is what makes the adversarial architecture actually adversarial.</p>
            </div>
          </div>
        </section>

        <section
          id="anti-sycophancy"
          ref={setSceneRef('anti-sycophancy')}
          className="scene layout-grid"
          data-act="3"
          data-active={activeScene === 'anti-sycophancy'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Hard Rules"
              title="Anti-people-pleasing guardrails"
              lede="Skepticism by prompt is not enough. Hard rules prevent the evaluator from rubber-stamping mediocre work, even when the LLM's instinct is to be agreeable."
            />
            <div className="scene__visual">
              <article className="panel rules-panel reveal delay-1">
                <span className="panel__tag">Anti-sycophancy rules</span>
                <ul>
                  {criticRules.map((rule) => (
                    <li key={rule}>{rule}</li>
                  ))}
                </ul>
              </article>
              <article className="panel reveal delay-2">
                <span className="panel__tag">Why hard rules?</span>
                <p className="panel__body">
                  Without explicit thresholds, evaluators trend toward 7/10 on everything.
                  Hard ceilings force honest scores even when the LLM wants to be polite.
                </p>
                <div className="signal-strip">All scores ≥ 7 = rubber-stamp suspicion</div>
              </article>
            </div>
          </div>
        </section>

        <section
          id="criteria-thresholds"
          ref={setSceneRef('criteria-thresholds')}
          className="scene layout-split"
          data-act="3"
          data-active={activeScene === 'criteria-thresholds'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Grading"
                title="Criteria and pass thresholds"
                lede="Four dimensions, weighted by importance. HIGH-weight criteria need a 6 to pass. The evaluator grades each independently — no single-number summary."
              />
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <div className="scorecard-list">
                {criteriaThresholds.map((row, index) => (
                  <article key={row.criterion} className="score-row reveal" style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}>
                    <div className="score-row__header">
                      <div>
                        <span className="panel__tag">{row.weight}</span>
                        <h3>{row.criterion}</h3>
                      </div>
                      <div className="score-row__winner">≥ {row.threshold}</div>
                    </div>
                    <p>{row.meaning}</p>
                    <p style={{ opacity: 0.7, fontSize: '0.85em' }}>{row.calibrationLow} · {row.calibrationHigh}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="experiment-design"
          ref={setSceneRef('experiment-design')}
          className="scene layout-statement"
          data-act="3"
          data-active={activeScene === 'experiment-design'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Controls"
              title="Solo vs trio — same model, different architecture"
              lede={`The independent variable is architecture. Everything else is controlled: ${experimentDesign.controls.map((c) => c.variable.toLowerCase()).join(', ')}. ${experimentDesign.coverage.benchmarks} benchmarks across ${experimentDesign.coverage.languages} languages, ${experimentDesign.coverage.totalRuns} total runs.`}
            />
          </div>
        </section>

        <section
          id="benchmark-matrix"
          ref={setSceneRef('benchmark-matrix')}
          className="scene layout-grid"
          data-act="3"
          data-active={activeScene === 'benchmark-matrix'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Test Suite"
              title="Five benchmarks across three languages"
              lede="Each benchmark has real code with a seeded bug or missing feature, visible tests (some failing), and hidden acceptance tests the generator cannot see."
            />
            <div className="scene__visual">
              {benchmarkMatrix.map((row, index) => (
                <article key={row.id} className="score-row reveal" style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}>
                  <div className="score-row__header">
                    <div>
                      <span className="panel__tag">{row.size} · {row.type}</span>
                      <h3>{row.description}</h3>
                    </div>
                    <div className="score-row__winner">{row.language}</div>
                  </div>
                  <p><code>{row.id}</code> · {row.loc} · {row.duration}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── Act 4 — Results ─────────────────────────────────────────── */}

        <section
          id="headline-result"
          ref={setSceneRef('headline-result')}
          className="scene layout-hero"
          data-act="4"
          data-active={activeScene === 'headline-result'}
        >
          <div className="scene__content">
            <span className="scene__eyebrow reveal stagger-1">Headline Result</span>
            <h1 className="scene__title reveal stagger-2">Same task. Same model. Same tools. Different architecture.</h1>
            <p className="scene__lede reveal stagger-3">
              The full-stack benchmark is the story to remember: WebSocket notifications were broken in solo mode and working in trio mode.
            </p>
            <div className="reveal stagger-4">
              <DiagramRenderer spec={diagram06HeadlineResult} />
            </div>
            <div className="metric-comparison reveal stagger-5">
              {evidenceMetrics.map((metric) => (
                <div key={metric.label} className="comparison-row">
                  <span>{metric.label}</span>
                  <div className="comparison-row__values">
                    <strong className="comparison-row__solo">{metric.solo}</strong>
                    <strong className="comparison-row__trio">{metric.trio}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section
          id="full-scorecard"
          ref={setSceneRef('full-scorecard')}
          className="scene layout-showcase"
          data-act="4"
          data-active={activeScene === 'full-scorecard'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Benchmark Grid"
              title="Trio wins where complexity starts to bite"
              lede="The scorecard matters because it stops the story from becoming propaganda: trio is not always worth it, but it clearly helps when the task crosses the model's solo reliability threshold."
            />
            <div className="scene__visual">
              <div>
                <div className="scorecard-list">
                  {scorecardRows.map((row, index) => (
                    <article
                      key={row.benchmark}
                      className={row.benchmark === 'medium-feature-fullstack' ? 'score-row score-row--featured reveal' : 'score-row reveal'}
                      style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}
                    >
                      <div className="score-row__header">
                        <div>
                          <span className="panel__tag">{row.verdict}</span>
                          <h3>{row.label}</h3>
                        </div>
                        <div className="score-row__winner">{row.winner}</div>
                      </div>
                      <div className="score-bars">
                        <ScoreBar label="Solo" value={row.solo} tone="solo" />
                        <ScoreBar label="Trio" value={row.trio} tone="trio" />
                      </div>
                      <p>{row.note}</p>
                    </article>
                  ))}
                </div>
                <div className="aggregate-strip reveal delay-4">
                  <div>
                    <span className="chrome-pill">Aggregate</span>
                    <strong>Mean functionality: 4.8 → 7.6</strong>
                  </div>
                  <p>Trio is ~1.8x slower in wall-clock time, but the overhead buys quality right where solo starts to crack.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="difficulty-classification"
          ref={setSceneRef('difficulty-classification')}
          className="scene layout-split"
          data-act="4"
          data-active={activeScene === 'difficulty-classification'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Difficulty Zones"
                title="Too easy, in the zone, too hard"
                lede="The trio is not universally better. Its value depends on where the task sits relative to the model's solo capability ceiling."
              />
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <div className="scorecard-list">
                {difficultyZones.map((zone, index) => (
                  <article key={zone.zone} className="score-row reveal" style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}>
                    <div className="score-row__header">
                      <div>
                        <span className="panel__tag" style={{ borderColor: zone.color }}>{zone.zone}</span>
                        <h3>{zone.description}</h3>
                      </div>
                    </div>
                    <p><strong>{zone.example}</strong></p>
                    <ul style={{ margin: '0.5em 0 0 1.2em', opacity: 0.8, fontSize: '0.85em' }}>
                      {zone.benchmarks.map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="iteration-curve"
          ref={setSceneRef('iteration-curve')}
          className="scene layout-showcase"
          data-act="4"
          data-active={activeScene === 'iteration-curve'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Iteration Curve"
              title="The feedback loop works before it plateaus"
              lede="Multi-iteration benchmarks start harsh, then rise sharply after explicit evaluator feedback. The Go race condition shows the limit: feedback helps, but it cannot force a model past its capability ceiling."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <div className="feedback-grid">
                <div className="panel chart-panel">
                  <span className="panel__tag">Average score by iteration</span>
                  <IterationChart active={activeScene === 'iteration-curve'} />
                </div>
                <div className="panel feedback-notes">
                  <span className="panel__tag">What the chart says</span>
                  <ul>
                    <li>Python bugfix: 5.0 → 9.5 after one evaluator catch.</li>
                    <li>Python tags: 3.25 → 8.0 after targeted feedback.</li>
                    <li>Go race: 2.75 → 6.5 → 7.25, but still no PASS verdict.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="claims-confirmed"
          ref={setSceneRef('claims-confirmed')}
          className="scene layout-grid"
          data-act="4"
          data-active={activeScene === 'claims-confirmed'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Validated"
              title="Five confirmed claims from the article"
              lede="These Anthropic article claims held up under controlled testing. The evidence is directional (N=11) but consistent."
            />
            <div className="scene__visual">
              {claimsConfirmed.map((item, index) => (
                <article key={item.claim} className="score-row reveal" style={{ transitionDelay: `${index * 80}ms` } as CSSProperties}>
                  <div className="score-row__header">
                    <div>
                      <span className="panel__tag">✅ {item.articleRef}</span>
                      <h3>{item.claim}</h3>
                    </div>
                  </div>
                  <p>{item.evidence}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── Act 5 — Nuance, Caveats, and Industry Context ───────────── */}

        <section
          id="claims-partial"
          ref={setSceneRef('claims-partial')}
          className="scene layout-editorial"
          data-act="5"
          data-active={activeScene === 'claims-partial'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Nuance"
              title="Partial and inconclusive claims"
              lede="Not every article claim survived testing. Honest reporting means showing where the evidence is thin or mixed."
            />
            <div className="two-up-grid">
              <article className="panel reveal delay-1">
                <span className="panel__tag">⚠️ Partially confirmed</span>
                <ul className="decision-list">
                  {claimsPartial.map((item) => (
                    <li key={item.claim}>
                      <strong>{item.claim}</strong> <em>({item.articleRef})</em>
                      <br />{item.evidence}
                    </li>
                  ))}
                </ul>
              </article>
              <article className="panel reveal delay-2">
                <span className="panel__tag">❓ Inconclusive</span>
                <ul className="decision-list decision-list--muted">
                  {claimsInconclusive.map((item) => (
                    <li key={item.claim}>
                      <strong>{item.claim}</strong> <em>({item.articleRef})</em>
                      <br />{item.evidence}
                    </li>
                  ))}
                </ul>
              </article>
            </div>
          </div>
        </section>

        <section
          id="evaluator-leniency"
          ref={setSceneRef('evaluator-leniency')}
          className="scene layout-statement"
          data-act="5"
          data-active={activeScene === 'evaluator-leniency'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Measurement Gap"
              title="The evaluator is not perfect"
              lede="Even with hard rules and anti-sycophancy prompting, the evaluator still shows leniency. This is an unsolved problem, not an oversight."
            />
          </div>
        </section>

        <section
          id="industry-timeline"
          ref={setSceneRef('industry-timeline')}
          className="scene layout-showcase"
          data-act="5"
          data-active={activeScene === 'industry-timeline'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Industry Convergence"
              title="This is not one lab's quirky workflow"
              lede="Anthropic, Claude Code, OpenAI Symphony, and community toolchains keep rediscovering the same foundations: isolated workspaces, specialized roles, and evaluation as architecture."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram09IndustryTimeline} />
              <div className="panel reveal delay-2" style={{ marginTop: 'var(--space-3)' }}>
                <span className="panel__tag">⚠️ Industry context — not Harnessa experiment evidence</span>
                <p className="panel__body">These events show convergence toward multi-agent orchestration across the industry. Harnessa validates one specific architecture; the timeline shows that the broader pattern is not an isolated bet.</p>
              </div>
            </div>
          </div>
        </section>

        <section
          id="ecosystem-network"
          ref={setSceneRef('ecosystem-network')}
          className="scene layout-showcase"
          data-act="5"
          data-active={activeScene === 'ecosystem-network'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Ecosystem"
              title="Outside voices confirm the direction"
              lede="Independent teams and projects keep arriving at the same architectural patterns — isolated agents, structured evaluation, and adversarial feedback loops."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <div>
                <DiagramRenderer spec={diagram10EcosystemNetwork} />
                <div className="scorecard-list" style={{ marginTop: 'var(--space-3)' }}>
                  <article className="score-row reveal delay-2">
                    <div className="score-row__header">
                      <div>
                        <span className="panel__tag">Independent validation</span>
                        <h3>Cross-model review pattern</h3>
                      </div>
                    </div>
                    <p>Using one model to evaluate another model's work — the same principle Harnessa uses — is emerging independently across toolchains. GStack's /codex and /review skills implement this as a second-opinion gate.</p>
                  </article>
                  <article className="score-row reveal delay-3">
                    <div className="score-row__header">
                      <div>
                        <span className="panel__tag">Open source</span>
                        <h3>OpenHands and community harnesses</h3>
                      </div>
                    </div>
                    <p>Open-source projects are building their own multi-agent evaluation loops. The pattern is converging on: isolated workspaces, structured evaluation criteria, and adversarial feedback as architecture rather than prompting.</p>
                  </article>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="showcase-rebuild"
          ref={setSceneRef('showcase-rebuild')}
          className="scene layout-split"
          data-act="5"
          data-active={activeScene === 'showcase-rebuild'}
        >
          <div className="scene__content">
            <div className="scene__intro">
              <SceneIntro
                eyebrow="Case Study"
                title="Monolith to proper app in two iterations"
                lede="The showcase rebuild is the trio pattern in action: iteration 1 shipped a 1-file monolith. The evaluator rejected it. Iteration 2 produced a 32-file full-stack application."
              />
              <div className="panel reveal delay-4" style={{ marginTop: 'var(--space-3)' }}>
                <span className="panel__tag">Key lessons</span>
                <ul className="decision-list">
                  {showcaseKeyLessons.map((lesson) => (
                    <li key={lesson}>{lesson}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="scene__visual reveal-scale stagger-4">
              <DiagramRenderer spec={diagram11ShowcaseRebuild} />
              <div className="headline-grid" style={{ marginTop: 'var(--space-4)' }}>
                <article className="state-card state-card--solo reveal delay-2">
                  <span className="panel__tag">Iteration 1 — {showcaseComparison.iteration1.verdict}</span>
                  <strong>{showcaseComparison.iteration1.files} file · {showcaseComparison.iteration1.lines} lines · {showcaseComparison.iteration1.tests} tests</strong>
                  <p>{showcaseComparison.iteration1.note}</p>
                </article>
                <article className="state-card state-card--trio reveal delay-3">
                  <span className="panel__tag">Iteration 2 — {showcaseComparison.iteration2.verdict}</span>
                  <strong>{showcaseComparison.iteration2.files} files · {showcaseComparison.iteration2.components} components · {showcaseComparison.iteration2.tests} tests</strong>
                  <p>{showcaseComparison.iteration2.note}</p>
                </article>
              </div>
            </div>
          </div>
        </section>

        {/* ── Act 6 — Practical Use, Demo, and Forward View ──────────── */}

        <section
          id="demo-flow"
          ref={setSceneRef('demo-flow')}
          className="scene layout-showcase"
          data-act="6"
          data-active={activeScene === 'demo-flow'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Live Demo"
              title="One command, three agents"
              lede="The /harnessa skill runs the full trio pipeline inside any Copilot CLI session. No API keys, no setup — just the command."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <div>
                <DiagramRenderer spec={diagram12DemoFlow} />
                <div className="panel reveal delay-2" style={{ marginTop: 'var(--space-4)' }}>
                  <span className="panel__tag">Command</span>
                  <div className="verdict-code">
                    <pre>{demoFlow.command}</pre>
                  </div>
                </div>
                <div className="scorecard-list" style={{ marginTop: 'var(--space-3)' }}>
                  {demoFlow.phases.map((phase, index) => (
                    <article key={phase.name} className="score-row reveal" style={{ transitionDelay: `${(index + 2) * 80}ms` } as CSSProperties}>
                      <div className="score-row__header">
                        <div>
                          <span className="panel__tag">{phase.name}</span>
                          <h3>{phase.description}</h3>
                        </div>
                        <div className="score-row__winner"><code>{phase.artifact}</code></div>
                      </div>
                    </article>
                  ))}
                </div>
                <div className="two-up-grid" style={{ marginTop: 'var(--space-4)' }}>
                  <article className="panel reveal delay-5">
                    <span className="panel__tag">{demoFlow.paths.skill.label}</span>
                    <p className="panel__body">{demoFlow.paths.skill.detail}</p>
                  </article>
                  <article className="panel reveal delay-6">
                    <span className="panel__tag">{demoFlow.paths.harness.label}</span>
                    <p className="panel__body">{demoFlow.paths.harness.detail}</p>
                  </article>
                </div>
                <div className="aggregate-strip reveal delay-7">
                  <p>{demoFlow.note}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="decision-tree"
          ref={setSceneRef('decision-tree')}
          className="scene layout-showcase"
          data-act="6"
          data-active={activeScene === 'decision-tree'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Operating Model"
              title="When trio is worth the overhead"
              lede="The trio is not a religion. It is an operating pattern for tasks where solo output is likely to be wrong, incomplete, or self-flatteringly over-scored."
            />
            <div className="scene__visual reveal-scale stagger-4">
              <div>
                <DiagramRenderer spec={diagram13DecisionTree} />
                <div className="two-up-grid" style={{ marginTop: 'var(--space-3)' }}>
                  <article className="panel reveal delay-2">
                    <span className="panel__tag">Use trio when</span>
                    <ul className="decision-list">
                      <li>Multi-file features where integration matters</li>
                      <li>Uncertain correctness — "will this actually work?"</li>
                      <li>Medium-complexity tasks at the edge of model capability</li>
                      <li>Broken output is expensive to debug manually</li>
                    </ul>
                  </article>
                  <article className="panel reveal delay-3">
                    <span className="panel__tag">Skip trio when</span>
                    <ul className="decision-list">
                      <li>Single-line fixes or simple refactors</li>
                      <li>Dependency version bumps</li>
                      <li>Tasks with known, verified answers</li>
                      <li>When the overhead costs more than the risk</li>
                    </ul>
                  </article>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="model-tiering"
          ref={setSceneRef('model-tiering')}
          className="scene layout-grid"
          data-act="6"
          data-active={activeScene === 'model-tiering'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Model Strategy"
              title="Opus plans, Sonnet builds"
              lede="Not every agent needs the most expensive model. Match model capability to role: reasoning-heavy roles get the premium model, execution roles get the fast one."
            />
            <div className="scene__visual">
              <div className="reveal delay-1" style={{ gridColumn: '1 / -1' }}>
                <DiagramRenderer spec={diagram14ModelTiering} />
              </div>
              <article className="panel reveal delay-2" style={{ gridColumn: '1 / -1' }}>
                <span className="panel__tag">⚠️ Industry pattern — not directly tested in Harnessa V1</span>
                <p className="panel__body">Harnessa V1 used the same model (claude-sonnet-4) for all roles. Model tiering — using premium reasoning models for planning/evaluation and faster models for execution — is an industry pattern observed in Claude Code's coordinator model, not a validated Harnessa finding.</p>
              </article>
              <article className="panel reveal delay-3">
                <span className="panel__tag">Reasoning tier (Opus-class)</span>
                <ul className="decision-list">
                  <li>Planning and spec expansion</li>
                  <li>Evaluation and grading</li>
                  <li>Contract negotiation</li>
                  <li>Higher cost per token, fewer calls</li>
                </ul>
              </article>
              <article className="panel reveal delay-4">
                <span className="panel__tag">Execution tier (Sonnet-class)</span>
                <ul className="decision-list">
                  <li>Code generation and implementation</li>
                  <li>Test writing</li>
                  <li>Iteration on feedback</li>
                  <li>Lower cost per token, many calls</li>
                </ul>
              </article>
            </div>
          </div>
        </section>

        <section
          id="round-robin"
          ref={setSceneRef('round-robin')}
          className="scene layout-statement"
          data-act="6"
          data-active={activeScene === 'round-robin'}
        >
          <div className="scene__content">
            <SceneIntro
              eyebrow="Conjecture"
              title="Cross-model evaluation and role rotation"
              lede="What happens when different models evaluate each other's work? The theory: disagreements between models surface blind spots that same-model evaluation misses."
            />
          </div>
        </section>

        <section
          id="closing"
          ref={setSceneRef('closing')}
          className="scene layout-hero"
          data-act="6"
          data-active={activeScene === 'closing'}
        >
          <div className="scene__content closing-layout">
            <div className="closing-copy">
              <span className="scene__eyebrow reveal stagger-1">Takeaway</span>
              <h2 className="scene__title reveal stagger-2">
                The quality ceiling is real. Architecture breaks through it.
              </h2>
              <p className="scene__lede reveal stagger-3">
                When a solo agent ships broken code, the answer is not always "buy a bigger model."
                Sometimes the answer is "stop letting the builder grade itself."
              </p>
              <blockquote className="quote-strip reveal stagger-4">
                "{closingQuote.text}"
                <cite>{closingQuote.author}</cite>
              </blockquote>
              <div className="closing-actions reveal stagger-5">
                <a className="chrome-button chrome-button--primary" href="https://github.com/ridermw/harnessa" target="_blank" rel="noreferrer">
                  View the repo
                </a>
                <button className="chrome-button" onClick={() => setAppendixOpen(true)} type="button">
                  Review appendix
                </button>
              </div>
            </div>
            <div className="closing-panels reveal delay-4">
              <article className="panel">
                <span className="panel__tag">Bottom line</span>
                <p>Separate building from judging. Keep the evaluator skeptical. Instrument every run.</p>
              </article>
              <article className="panel">
                <span className="panel__tag">Footer</span>
                <p>Matthew Williams — Senior SWE (MSFT) · Based on Anthropic Labs research by Prithvi Rajasekaran</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <AppendixPanel open={appendixOpen} onClose={() => setAppendixOpen(false)} />
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────
   Sub-components
   ──────────────────────────────────────────────────────────────────── */

function SceneIntro({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede: string;
}): JSX.Element {
  return (
    <header className="scene__header">
      <span className="scene__eyebrow reveal stagger-1">{eyebrow}</span>
      <h2 className="scene__title reveal stagger-2">{title}</h2>
      <p className="scene__lede reveal stagger-3">{lede}</p>
    </header>
  );
}

function MetricCard({
  metric,
  active,
}: {
  metric: {
    label: string;
    value?: number;
    display: string;
    suffix?: string;
    prefix?: string;
    decimals?: number;
    note: string;
  };
  active: boolean;
}): JSX.Element {
  const animated = useAnimatedNumber(metric.value, active, metric.decimals ?? 0);
  const display = metric.value === undefined
    ? metric.display
    : `${metric.prefix ?? ''}${animated}${metric.suffix ?? ''}`;

  return (
    <article className="metric-card">
      <span>{metric.label}</span>
      <strong>{display}</strong>
      <small>{metric.note}</small>
    </article>
  );
}

function ScoreBar({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'solo' | 'trio';
}): JSX.Element {
  const width = `${(value / 10) * 100}%`;
  return (
    <div className="score-bar">
      <div className="score-bar__label">
        <span>{label}</span>
        <strong>{value.toFixed(2).replace(/\.00$/, '')}</strong>
      </div>
      <div className="score-bar__track">
        <div
          className={tone === 'solo' ? 'score-bar__fill score-bar__fill--solo' : 'score-bar__fill score-bar__fill--trio'}
          style={{ width }}
        />
      </div>
    </div>
  );
}

function IterationChart({ active }: { active: boolean }): JSX.Element {
  const maxValue = 10;
  const chartHeight = 100;
  const chartWidth = 100;
  const dashStyle = active ? undefined : { strokeDashoffset: 100 };

  return (
    <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="iteration-chart" role="img" aria-label="Average score by iteration across trio runs">
      <line x1="8" y1="22" x2="98" y2="22" className="iteration-chart__threshold" />
      <text x="8" y="18" className="iteration-chart__label">PASS</text>
      {[0, 1, 2].map((index) => {
        const x = 18 + index * 28;
        return (
          <g key={index}>
            <line x1={x} y1="12" x2={x} y2="92" className="iteration-chart__grid" />
            <text x={x} y="97" className="iteration-chart__axis">
              {index + 1}
            </text>
          </g>
        );
      })}
      {iterationSeries.map((series) => {
        const points = series.values
          .map((value, index) => {
            const x = 18 + index * 28;
            const y = 92 - (value / maxValue) * 78;
            return `${x},${y}`;
          })
          .join(' ');

        return (
          <g key={series.label}>
            <polyline
              points={points}
              className="iteration-chart__line"
              style={{
                stroke: series.color,
                ...dashStyle,
              }}
            />
            {series.values.map((value, index) => {
              const x = 18 + index * 28;
              const y = 92 - (value / maxValue) * 78;
              return (
                <g key={`${series.label}-${index}`}>
                  <circle cx={x} cy={y} r="2.3" fill={series.color} />
                  <text x={x + 2} y={y - 4} className="iteration-chart__label">
                    {value}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}
      <text x={94} y={97} className="iteration-chart__axis">Iteration</text>
      <text x={3} y={14} className="iteration-chart__axis" transform={`rotate(-90 3 ${chartHeight / 2})`}>
        Avg score
      </text>
    </svg>
  );
}

function HeroSignal(): JSX.Element {
  return (
    <svg viewBox="0 0 480 420" className="hero-signal" aria-hidden="true">
      <defs>
        <linearGradient id="signalPath" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4dd6ff" />
          <stop offset="100%" stopColor="#ffb648" />
        </linearGradient>
      </defs>
      {/* Subtle outer ring only — no confusing lines/dots */}
      <circle cx="240" cy="210" r="160" className="hero-signal__ring" />
    </svg>
  );
}

function AppendixPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}): JSX.Element {
  return (
    <div className={open ? 'appendix appendix--open' : 'appendix'} aria-hidden={!open}>
      <div className="appendix__scrim" onClick={onClose} />
      <div className="appendix__panel" role="dialog" aria-modal="true" aria-label="Appendix">
        <div className="appendix__header">
          <div>
            <span className="chrome-pill">Appendix</span>
            <h2>Evidence, caveats, and source material</h2>
          </div>
          <button className="chrome-button" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="appendix__grid">
          <article className="panel">
            <span className="panel__tag">Experiment matrix</span>
            <div className="appendix-table">
              <table>
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Benchmark</th>
                    <th>Mode</th>
                    <th>Verdict</th>
                    <th>Score</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {appendixRuns.map((run) => (
                    <tr key={run[0]}>
                      {run.map((cell) => (
                        <td key={cell}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel">
            <span className="panel__tag">Criteria</span>
            <div className="appendix-table">
              <table>
                <thead>
                  <tr>
                    <th>Criterion</th>
                    <th>Weight</th>
                    <th>Threshold</th>
                    <th>Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {appendixCriteria.map((row) => (
                    <tr key={row[0]}>
                      {row.map((cell) => (
                        <td key={cell}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel">
            <span className="panel__tag">Caveats</span>
            <ul className="appendix-list">
              {appendixCaveats.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="panel">
            <span className="panel__tag">Sources</span>
            <ul className="appendix-links">
              {citations.map((citation) => (
                <li key={citation.href}>
                  <a href={citation.href} target="_blank" rel="noreferrer">
                    {citation.label}
                  </a>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </div>
    </div>
  );
}

export default App;
