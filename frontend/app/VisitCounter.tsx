"use client";

import { useEffect, useState } from "react";

const COUNTED_KEY = "darksuomi.visitCounted";

/**
 * "12 345 visits" in the footer. A visit is counted once per browser tab
 * session (moving between pages or reloading doesn't add more); after that
 * the number is only read. Shows nothing until the number is known, or if
 * the counter isn't available.
 */
export default function VisitCounter() {
  const [visits, setVisits] = useState<number | null>(null);

  useEffect(() => {
    let counted = false;
    try {
      counted = sessionStorage.getItem(COUNTED_KEY) === "1";
    } catch {
      // Blocked storage: count this page load.
    }
    // Automated browsers (test tools, crawlers that run scripts) don't count.
    const count = !counted && !navigator.webdriver;
    // Marked before the request, so a second run of this effect (React dev
    // mode, quick re-renders) can't count the same visit twice.
    const mark = (value: boolean) => {
      try {
        if (value) sessionStorage.setItem(COUNTED_KEY, "1");
        else sessionStorage.removeItem(COUNTED_KEY);
      } catch {
        // Blocked storage: nothing to remember.
      }
    };
    if (count) mark(true);

    let cancelled = false;
    fetch("/api/visits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { visits?: number } | null) => {
        if (typeof data?.visits !== "number") throw new Error("no count");
        if (!cancelled) setVisits(data.visits);
      })
      // Not counted after all: let the next page load try again.
      .catch(() => count && mark(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (visits === null) return null;
  return (
    <>
      {" · "}
      <span title="Visits counted once per browser session, without cookies">
        {visits.toLocaleString("fi-FI")} visits
      </span>
    </>
  );
}
