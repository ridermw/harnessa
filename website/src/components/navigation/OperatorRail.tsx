import { useState, useEffect, useCallback, useRef } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SceneEntry {
  readonly id: string;
  readonly short: string;
  readonly eyebrow: string;
  readonly title: string;
}

export interface OperatorRailProps {
  scenes: ReadonlyArray<SceneEntry>;
  activeScene: string;
  onJumpToScene: (id: string) => void;
  appendixOpen: boolean;
}

// ---------------------------------------------------------------------------
// Hook – useRailState
// ---------------------------------------------------------------------------

function readInitialRailState(): boolean {
  const urlParam = new URLSearchParams(window.location.search).get('rail');
  if (urlParam === 'open') return true;
  if (urlParam === 'closed') return false;
  try {
    return localStorage.getItem('harnessa-rail-open') !== 'false';
  } catch {
    return true;
  }
}

export function useRailState() {
  const [railOpen, setRailOpen] = useState(readInitialRailState);

  useEffect(() => {
    try {
      localStorage.setItem('harnessa-rail-open', String(railOpen));
    } catch {
      // localStorage may be unavailable (private browsing, etc.)
    }
  }, [railOpen]);

  const toggleRail = useCallback(() => setRailOpen((prev) => !prev), []);

  return { railOpen, setRailOpen, toggleRail } as const;
}

// ---------------------------------------------------------------------------
// Toggle button (lives in the topbar)
// ---------------------------------------------------------------------------

export interface RailToggleButtonProps {
  railOpen: boolean;
  onToggle: () => void;
}

export function RailToggleButton({ railOpen, onToggle }: RailToggleButtonProps) {
  return (
    <button
      type="button"
      className="chrome-button rail-toggle"
      onClick={onToggle}
      aria-expanded={railOpen}
      aria-controls="scene-rail"
      title={railOpen ? 'Hide scene rail (S)' : 'Show scene rail (S)'}
    >
      {railOpen ? '◂ Scenes' : 'Scenes ▸'}
    </button>
  );
}

// ---------------------------------------------------------------------------
// OperatorRail component
// ---------------------------------------------------------------------------

export function OperatorRail({
  scenes,
  activeScene,
  onJumpToScene,
  appendixOpen,
}: OperatorRailProps) {
  const { railOpen, toggleRail } = useRailState();
  const toggleButtonRef = useRef<HTMLButtonElement | null>(null);
  const firstNavButtonRef = useRef<HTMLButtonElement | null>(null);
  const previousRailOpen = useRef(railOpen);

  // ---- Focus management ----
  useEffect(() => {
    // Only act on transitions, not the initial render
    if (previousRailOpen.current === railOpen) return;
    previousRailOpen.current = railOpen;

    if (railOpen) {
      // Rail just opened → focus first scene button
      requestAnimationFrame(() => {
        firstNavButtonRef.current?.focus();
      });
    } else {
      // Rail just closed → focus toggle button (if it exists in the DOM)
      requestAnimationFrame(() => {
        toggleButtonRef.current?.focus();
      });
    }
  }, [railOpen]);

  // ---- Keyboard shortcuts ----
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
      ) {
        return;
      }

      // 'S' toggles the rail
      if (event.key.toLowerCase() === 's' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        toggleRail();
        return;
      }

      // Escape closes the rail (only if appendix is NOT open)
      if (event.key === 'Escape' && railOpen && !appendixOpen) {
        event.preventDefault();
        toggleRail();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [appendixOpen, railOpen, toggleRail]);

  return (
    <>
      {/* Toggle button — rendered outside the rail so it's always accessible.
          The parent component should place this inside .topbar__status. */}
      <button
        ref={toggleButtonRef}
        type="button"
        className="chrome-button rail-toggle"
        onClick={toggleRail}
        aria-expanded={railOpen}
        aria-controls="scene-rail"
        title={railOpen ? 'Hide scene rail (S)' : 'Show scene rail (S)'}
      >
        {railOpen ? '◂ Scenes' : 'Scenes ▸'}
      </button>

      {/* The rail itself */}
      <aside
        id="scene-rail"
        className="progress-rail"
        role="navigation"
        aria-label="Scene navigation"
        data-rail-open={railOpen}
      >
        <div className="progress-rail__header">
          <span className="chrome-pill">Operator rail</span>
          <p>
            Use ↑ ↓ or J / K to move. Press A for appendix. Press S to
            toggle rail.
          </p>
        </div>
        <nav className="scene-nav">
          {scenes.map((scene, index) => (
            <button
              key={scene.id}
              ref={index === 0 ? firstNavButtonRef : undefined}
              className={
                scene.id === activeScene
                  ? 'scene-nav__item is-active'
                  : 'scene-nav__item'
              }
              onClick={() => onJumpToScene(scene.id)}
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
    </>
  );
}

export default OperatorRail;
