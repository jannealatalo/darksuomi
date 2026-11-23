import { useEffect, useState, useSyncExternalStore } from "react";

const STORAGE_KEY = "darksuomi.lastfmUser";
const EMPTY = new Set<string>();

// The username is one shared value for the whole site: Next keeps visited
// city pages alive (hidden), so each must see a change made on another at
// once. It lives in localStorage, with a copy in memory for when storage
// is blocked (private mode), and listeners for the open pages.
let memoryUser: string | null = null;
const listeners = new Set<() => void>();

function readUser(): string {
  if (memoryUser !== null) return memoryUser;
  try {
    memoryUser = localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    memoryUser = "";
  }
  return memoryUser;
}

function writeUser(user: string) {
  memoryUser = user;
  try {
    if (user) localStorage.setItem(STORAGE_KEY, user);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Private mode or blocked storage: the name lasts until the tab closes.
  }
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void) {
  listeners.add(notify);
  // Other tabs of the site changing the name.
  const onStorage = (e: StorageEvent) => {
    if (e.key !== STORAGE_KEY) return;
    memoryUser = e.newValue ?? "";
    notify();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(notify);
    window.removeEventListener("storage", onStorage);
  };
}

/**
 * The top artists of a Last.fm user the visitor named (no login), via
 * /api/lastfm. The username is remembered in this browser.
 */
export function useLastfmArtists() {
  // "" on the server and during hydration (the page is pre-rendered).
  const user = useSyncExternalStore(subscribe, readUser, () => "");
  // Results are stored with the user they were fetched for, so changing
  // the user shows "loading" without resetting state inside the effect.
  const [result, setResult] = useState<{
    user: string;
    artists: Set<string>;
    error: "not-found" | "unavailable" | null;
  } | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      let artists = EMPTY;
      let error: "not-found" | "unavailable" | null = null;
      try {
        const response = await fetch(`/api/lastfm?user=${encodeURIComponent(user)}`);
        const data = await response.json();
        if (response.ok && Array.isArray(data.artists)) {
          artists = new Set<string>(data.artists);
        } else {
          error = data.error === "not-found" ? "not-found" : "unavailable";
        }
      } catch {
        error = "unavailable";
      }
      if (!cancelled) setResult({ user, artists, error });
    })();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const setUser = (next: string) => writeUser(next.trim());

  const isCurrent = !!user && result?.user === user;
  return {
    lastfmUser: user,
    setLastfmUser: setUser,
    lastfmArtists: isCurrent ? result.artists : EMPTY,
    lastfmLoading: !!user && !isCurrent,
    lastfmError: isCurrent ? result.error : null,
  };
}
