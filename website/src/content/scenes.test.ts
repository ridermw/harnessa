import { describe, it, expect } from 'vitest';
import { scenes, sceneAliases } from './scenes';

describe('scene manifest', () => {
  it('has exactly 30 scenes', () => {
    expect(scenes).toHaveLength(30);
  });

  it('has all unique scene IDs', () => {
    const ids = scenes.map((s) => s.id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });

  it('has sequential short numbers from 01 through 30', () => {
    scenes.forEach((scene, index) => {
      const expected = String(index + 1).padStart(2, '0');
      expect(scene.short, `scene "${scene.id}" at index ${index}`).toBe(expected);
    });
  });

  it('has all alias targets pointing to valid scene IDs', () => {
    const validIds = new Set(scenes.map((s) => s.id));
    for (const [alias, target] of Object.entries(sceneAliases)) {
      expect(validIds.has(target), `alias "${alias}" → "${target}" is not a valid scene ID`).toBe(true);
    }
  });

  it('has no scene ID that collides with an alias key', () => {
    const sceneIds = new Set(scenes.map((s) => s.id));
    const aliasKeys = Object.keys(sceneAliases);
    for (const alias of aliasKeys) {
      expect(sceneIds.has(alias as any), `alias key "${alias}" collides with a scene ID`).toBe(false);
    }
  });
});
