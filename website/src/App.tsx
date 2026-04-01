import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import {
  appendixCaveats,
  appendixCriteria,
  appendixRuns,
  architectureStages,
  citations,
  criticRules,
  evidenceMetrics,
  heroMetrics,
  iterationSeries,
  landscapeEvents,
  problemWalls,
  scenes,
  scorecardRows,
  skipTrio,
  telemetrySignals,
  tieringRoles,
  useTrio,
  type SceneId,
} from './content/presentation';

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

function clampSceneId(value: string | null): SceneId | null {
  if (!value) {
    return null;
  }

  const match = scenes.find((scene) => scene.id === value);
  return match?.id ?? null;
}

function App(): JSX.Element {
  const reducedMotion = usePrefersReducedMotion();
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
  const sceneRefs = useRef<Record<SceneId, HTMLElement | null>>({
    hero: null,
    problem: null,
    architecture: null,
    critic: null,
    evidence: null,
    scorecard: null,
    feedback: null,
    landscape: null,
    decision: null,
    closing: null,
  });

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
    <div className="presentation-app">
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
          <button
            className="chrome-button"
            type="button"
            onClick={() => setAppendixOpen(true)}
          >
            Appendix
          </button>
        </div>
      </header>

      <aside className="progress-rail" aria-label="Scene navigation">
        <div className="progress-rail__header">
          <span className="chrome-pill">Operator rail</span>
          <p>Use ↑ ↓ or J / K to move. Press A for appendix.</p>
        </div>
        <nav className="scene-nav">
          {scenes.map((scene) => (
            <button
              key={scene.id}
              className={scene.id === activeScene ? 'scene-nav__item is-active' : 'scene-nav__item'}
              onClick={() => jumpToScene(scene.id)}
              type="button"
            >
              <span>{scene.short}</span>
              <div>
                <strong>{scene.eyebrow}</strong>
                <small>{scene.title}</small>
              </div>
            </button>
          ))}
        </nav>
      </aside>

      <div className="mobile-warning">
        Optimized for desktop / projector. Mobile keeps all content, but the intended experience is widescreen.
      </div>

      <main className="scene-stack">
        <section
          id="hero"
          ref={setSceneRef('hero')}
          className="scene scene--hero"
          data-active={activeScene === 'hero'}
        >
          <div className="scene__content hero-layout">
            <div className="hero-copy">
              <span className="scene__eyebrow reveal">Anthropic article → Harnessa evidence → deployment pattern</span>
              <h1 className="scene__title reveal delay-1">
                Better AI software comes from agents that disagree.
              </h1>
              <p className="scene__lede reveal delay-2">
                Anthropic framed the idea. Harnessa tested it. The result was not marginal polish —
                it was a broken solo full-stack build turning into a working trio system.
              </p>
              <div className="hero-actions reveal delay-3">
                  <button className="chrome-button chrome-button--primary" onClick={() => jumpToScene('evidence')} type="button">
                  Jump to the headline
                </button>
                <button className="chrome-button" onClick={() => setAppendixOpen(true)} type="button">
                  Open appendix
                </button>
              </div>
              <div className="hero-note reveal delay-4">
                <span className="chrome-pill">Caveat</span>
                N=11 total runs. Directional, not final science — but the full-stack result is categorical, not subtle.
              </div>
            </div>
            <div className="hero-visual reveal delay-2">
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
          id="problem"
          ref={setSceneRef('problem')}
          className="scene"
          data-active={activeScene === 'problem'}
        >
          <SceneIntro
            eyebrow="Failure Mode"
            title="Single-agent coding hits two hard walls"
            lede="The first wall is context degradation. The second is more dangerous: self-evaluation bias. If the same system builds and judges the work, quality gets flattered."
          />
          <div className="two-up-grid">
            {problemWalls.map((wall, index) => (
              <article key={wall.title} className={`panel reveal delay-${index + 1}`}>
                <span className="panel__tag">{wall.title}</span>
                <p className="panel__body">{wall.body}</p>
                <div className="signal-strip">{wall.signal}</div>
              </article>
            ))}
          </div>
          <blockquote className="quote-strip reveal delay-3">
            “I watched it identify legitimate issues, then talk itself into deciding they weren’t a big deal and approve the work anyway.”
            <cite>Anthropic Labs</cite>
          </blockquote>
        </section>

        <section
          id="architecture"
          ref={setSceneRef('architecture')}
          className="scene"
          data-active={activeScene === 'architecture'}
        >
          <SceneIntro
            eyebrow="System View"
            title="Planner → Generator ↔ Evaluator"
            lede="The architecture matters more than one bigger context window. Separate roles, explicit contracts, and independent evaluation create the quality leverage."
          />
          <div className="architecture-grid reveal delay-1">
            <div className="topology-shell">
              <div className="topology-flow">
                {architectureStages.map((stage) => (
                  <div key={stage.name} className="topology-node" style={{ ['--node-accent' as string]: stage.accent }}>
                    <span className="topology-node__name">{stage.name}</span>
                    <strong>{stage.title}</strong>
                    <ul>
                      {stage.bullets.map((bullet) => (
                        <li key={bullet}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
              <div className="topology-links" aria-hidden="true">
                <span className="topology-link">Spec</span>
                <span className="topology-link topology-link--loop">Adversarial feedback loop</span>
                <span className="topology-link">Grade + bug report</span>
              </div>
            </div>
            <aside className="panel telemetry-panel reveal delay-2">
              <span className="panel__tag">Telemetry rail</span>
              <h3>Every run produces evidence, not vibes.</h3>
              <div className="telemetry-grid">
                {telemetrySignals.map((signal) => (
                  <div key={signal} className="telemetry-chip">
                    {signal}
                  </div>
                ))}
              </div>
              <p className="telemetry-note">
                Generator cannot see hidden `_eval/` tests. Evaluator can. That boundary is the Goodhart defense.
              </p>
            </aside>
          </div>
        </section>

        <section
          id="critic"
          ref={setSceneRef('critic')}
          className="scene"
          data-active={activeScene === 'critic'}
        >
          <SceneIntro
            eyebrow="Skepticism Engine"
            title="The critic needs hard rules"
            lede="Karpathy’s anecdote is the point: an LLM can argue both sides convincingly. A separate evaluator only works if it is calibrated to refuse empty praise."
          />
          <div className="critic-grid">
            <article className="panel quote-panel reveal delay-1">
              <span className="panel__tag">Karpathy problem</span>
              <p className="quote-panel__text">
                “Used an LLM to improve my argument over 4 hours. Feeling great, so convincing! Fun idea — let’s ask it to argue the opposite. LLM demolishes the entire argument. lol”
              </p>
              <cite>Andrej Karpathy</cite>
            </article>
            <article className="panel rules-panel reveal delay-2">
              <span className="panel__tag">Anti-sycophancy rules</span>
              <ul>
                {criticRules.map((rule) => (
                  <li key={rule}>{rule}</li>
                ))}
              </ul>
            </article>
            <article className="panel verdict-panel reveal delay-3">
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
        </section>

        <section
          id="evidence"
          ref={setSceneRef('evidence')}
          className="scene"
          data-active={activeScene === 'evidence'}
        >
          <SceneIntro
            eyebrow="Headline Result"
            title="Same task. Same model. Same tools. Different architecture."
            lede="The full-stack benchmark is the story to remember: WebSocket notifications were broken in solo mode and working in trio mode."
          />
          <div className="headline-grid">
            <article className="state-card state-card--solo reveal delay-1">
              <span className="panel__tag">Solo</span>
              <strong>FAIL</strong>
              <p>Core feature broken. Notification system did not work.</p>
            </article>
            <div className="state-transition reveal delay-2">
              <span className="chrome-pill chrome-pill--active">Planner + generator + evaluator</span>
              <div className="transition-arrow">FAIL → PASS</div>
              <small>That is the categorical difference the article predicted.</small>
            </div>
            <article className="state-card state-card--trio reveal delay-3">
              <span className="panel__tag">Trio</span>
              <strong>PASS</strong>
              <p>Correct notifications landed on the first trio attempt.</p>
            </article>
          </div>
          <div className="metric-comparison reveal delay-4">
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
        </section>

        <section
          id="scorecard"
          ref={setSceneRef('scorecard')}
          className="scene"
          data-active={activeScene === 'scorecard'}
        >
          <SceneIntro
            eyebrow="Benchmark Grid"
            title="Trio wins where complexity starts to bite"
            lede="The scorecard matters because it stops the story from becoming propaganda: trio is not always worth it, but it clearly helps when the task crosses the model’s solo reliability threshold."
          />
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
        </section>

        <section
          id="feedback"
          ref={setSceneRef('feedback')}
          className="scene"
          data-active={activeScene === 'feedback'}
        >
          <SceneIntro
            eyebrow="Iteration Curve"
            title="The feedback loop works before it plateaus"
            lede="Multi-iteration benchmarks start harsh, then rise sharply after explicit evaluator feedback. The Go race condition shows the limit: feedback helps, but it cannot force a model past its capability ceiling."
          />
          <div className="feedback-grid reveal delay-1">
            <div className="panel chart-panel">
              <span className="panel__tag">Average score by iteration</span>
              <IterationChart active={activeScene === 'feedback'} />
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
        </section>

        <section
          id="landscape"
          ref={setSceneRef('landscape')}
          className="scene"
          data-active={activeScene === 'landscape'}
        >
          <SceneIntro
            eyebrow="Industry Convergence"
            title="This is not one lab’s quirky workflow"
            lede="Anthropic, Claude Code, OpenAI Symphony, and community toolchains keep rediscovering the same foundations: isolated workspaces, specialized roles, and evaluation as architecture."
          />
          <div className="panel timeline-panel reveal delay-1">
            <span className="panel__tag">Convergence map</span>
            <div className="timeline">
              {landscapeEvents.map((event, index) => (
                <article key={`${event.stamp}-${event.actor}`} className="timeline__item" style={{ transitionDelay: `${index * 90}ms` } as CSSProperties}>
                  <span className="timeline__stamp">{event.stamp}</span>
                  <div className="timeline__body">
                    <strong>{event.actor}</strong>
                    <h3>{event.title}</h3>
                    <p>{event.detail}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section
          id="decision"
          ref={setSceneRef('decision')}
          className="scene"
          data-active={activeScene === 'decision'}
        >
          <SceneIntro
            eyebrow="Operating Model"
            title="Use it where it changes the answer"
            lede="The trio is not a religion. It is an operating pattern for tasks where solo output is likely to be wrong, incomplete, or self-flatteringly over-scored."
          />
          <div className="decision-grid">
            <article className="panel reveal delay-1">
              <span className="panel__tag">Use trio</span>
              <ul className="decision-list">
                {useTrio.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="panel reveal delay-2">
              <span className="panel__tag">Skip it</span>
              <ul className="decision-list decision-list--muted">
                {skipTrio.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="panel reveal delay-3">
              <span className="panel__tag">Models can punch above their weight</span>
              <div className="tiering-stack">
                {tieringRoles.map((role) => (
                  <div key={role.model} className="tiering-card">
                    <strong>{role.model}</strong>
                    <span>{role.role}</span>
                    <p>{role.note}</p>
                  </div>
                ))}
              </div>
              <p className="decision-footnote">
                Industry practice, not directly tested here: Anthropic’s `/opusplan` pattern keeps the premium reasoning model in planning mode and lets faster models do the execution work.
              </p>
            </article>
          </div>
        </section>

        <section
          id="closing"
          ref={setSceneRef('closing')}
          className="scene scene--closing"
          data-active={activeScene === 'closing'}
        >
          <div className="scene__content closing-layout">
            <div className="closing-copy">
              <span className="scene__eyebrow reveal">Takeaway</span>
              <h2 className="scene__title reveal delay-1">
                The quality ceiling is real. Architecture breaks through it.
              </h2>
              <p className="scene__lede reveal delay-2">
                When a solo agent ships broken code, the answer is not always “buy a bigger model.”
                Sometimes the answer is “stop letting the builder grade itself.”
              </p>
              <div className="closing-actions reveal delay-3">
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
      <span className="scene__eyebrow reveal">{eyebrow}</span>
      <h2 className="scene__title reveal delay-1">{title}</h2>
      <p className="scene__lede reveal delay-2">{lede}</p>
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
    <svg viewBox="0 0 100 100" className="iteration-chart" role="img" aria-label="Average score by iteration across trio runs">
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
      <circle cx="240" cy="210" r="152" className="hero-signal__ring" />
      <circle cx="240" cy="210" r="102" className="hero-signal__ring hero-signal__ring--inner" />
      <path d="M104 126 L240 82 L369 144" className="hero-signal__path" />
      <path d="M112 270 L240 210 L356 312" className="hero-signal__path hero-signal__path--accent" />
      <path d="M176 332 L240 210 L308 92" className="hero-signal__path" />
      <g className="hero-signal__pulse">
        <circle cx="104" cy="126" r="9" />
        <circle cx="240" cy="82" r="11" />
        <circle cx="369" cy="144" r="10" />
        <circle cx="112" cy="270" r="10" />
        <circle cx="240" cy="210" r="13" />
        <circle cx="356" cy="312" r="9" />
        <circle cx="176" cy="332" r="9" />
        <circle cx="308" cy="92" r="9" />
      </g>
      <foreignObject x="178" y="184" width="124" height="60">
        <div className="hero-signal__core">Planner / Generator / Evaluator</div>
      </foreignObject>
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
