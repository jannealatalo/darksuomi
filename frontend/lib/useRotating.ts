"use client";

import { useEffect, useState } from "react";

/** How often the header's tagline and no-cookies joke change. */
export const ROTATE_EVERY_MS = 30000;
const FADE_MS = 500;

/**
 * One line of `list` at a time: a random start per visit, then the next one
 * every `everyMs`, fading out and in. `text` is null until the page has
 * loaded (the page is pre-rendered, so server and browser start equal);
 * `visible` drives the fade. No rotation when reduced motion is asked for.
 */
export function useRotating(list: string[], everyMs = ROTATE_EVERY_MS) {
  const [index, setIndex] = useState<number | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one random pick per visit
    setIndex(Math.floor(Math.random() * list.length));
    setVisible(true);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let fade: ReturnType<typeof setTimeout>;
    const timer = setInterval(() => {
      setVisible(false);
      fade = setTimeout(() => {
        setIndex((i) => ((i ?? 0) + 1) % list.length);
        setVisible(true);
      }, FADE_MS);
    }, everyMs);
    return () => {
      clearInterval(timer);
      clearTimeout(fade);
    };
  }, [list, everyMs]);

  return { text: index === null ? null : list[index], visible };
}
