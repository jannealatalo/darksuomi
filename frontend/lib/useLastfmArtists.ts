import { useEffect, useState } from "react";

const STORAGE_KEY = "darksuomi.lastfmUser";
const EMPTY = new Set<string>();

function readStoredUser(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function storeUser(user: string) {
  try {
    if (user) localStorage.setItem(STORAGE_KEY, user);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Private mode or blocked storage: the filter just isn't remembered.
  }
}

/**
 * The top artists of a Last.fm user the visitor named (no login), via
 * /api/lastfm. The username is remembered in this browser.
 */
export function useLastfmArtists() {
  const [user, setUserState] = useState("");
  // Results are stored with the user they were fetched for, so changing
  // the user shows "loading" without resetting state inside the effect.
  const [result, setResult] = useState<{
    user: string;
    artists: Set<string>;
    error: "not-found" | "unavailable" | null;
  } | null>(null);

  // The page is pre-rendered, so the stored name is read after load.
  useEffect(() => {
    const stored = readStoredUser();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- restore once per visit
    if (stored) setUserState(stored);
  }, []);

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

  const setUser = (next: string) => {
    const trimmed = next.trim();
    storeUser(trimmed);
    setUserState(trimmed);
  };

  const isCurrent = !!user && result?.user === user;
  return {
    lastfmUser: user,
    setLastfmUser: setUser,
    lastfmArtists: isCurrent ? result.artists : EMPTY,
    lastfmLoading: !!user && !isCurrent,
    lastfmError: isCurrent ? result.error : null,
  };
}
