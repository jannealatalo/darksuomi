"use client";

import Link from "next/link";
import { NO_COOKIE_JOKES } from "../lib/jokes";
import { useRotating } from "../lib/useRotating";

/** "No cookies. No ads." and a dry joke that changes every 30 seconds. */
export default function NoCookies() {
  const { text, visible } = useRotating(NO_COOKIE_JOKES);
  return (
    <span className="block mt-2 text-xs leading-snug">
      <Link
        href="/privacy"
        className="font-semibold text-purple-400 hover:text-purple-300"
        title="What the site stores (nothing about you)"
      >
        No cookies. No ads.
      </Link>{" "}
      {/* Fixed height, so the page doesn't jump when the joke changes. */}
      <span
        className={`block min-h-[2.5em] text-gray-500 italic transition-opacity duration-500 ${
          visible ? "opacity-100" : "opacity-0"
        }`}
      >
        {text ?? " "}
      </span>
    </span>
  );
}
