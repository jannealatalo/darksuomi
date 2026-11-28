"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { NO_COOKIE_JOKES } from "../lib/jokes";

const CHANGE_EVERY_MS = 30000;

/** "No cookies. No ads." and a dry joke that changes every 30 seconds. */
export default function NoCookies() {
  const [index, setIndex] = useState<number | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Picked in the browser (the page is pre-rendered), a random start per visit.
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one random pick per visit
    setIndex(Math.floor(Math.random() * NO_COOKIE_JOKES.length));
    setVisible(true);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let fade: ReturnType<typeof setTimeout>;
    const timer = setInterval(() => {
      setVisible(false);
      fade = setTimeout(() => {
        setIndex((i) => ((i ?? 0) + 1) % NO_COOKIE_JOKES.length);
        setVisible(true);
      }, 500);
    }, CHANGE_EVERY_MS);
    return () => {
      clearInterval(timer);
      clearTimeout(fade);
    };
  }, []);

  return (
    <span className="block mt-3 text-xs leading-snug">
      <Link
        href="/privacy"
        className="font-semibold text-purple-400 hover:text-purple-300"
        title="What the site stores (nothing about you)"
      >
        No cookies. No ads.
      </Link>{" "}
      {/* Fixed height, so the page doesn't jump when the joke changes. */}
      <span
        aria-live="off"
        className={`block min-h-[2.5em] text-gray-500 italic transition-opacity duration-500 ${
          visible ? "opacity-100" : "opacity-0"
        }`}
      >
        {index === null ? " " : NO_COOKIE_JOKES[index]}
      </span>
    </span>
  );
}
