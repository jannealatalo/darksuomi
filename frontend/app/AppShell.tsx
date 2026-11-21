"use client";

import { useEffect, useState } from "react";

/**
 * The installable app's plumbing, on every page:
 *  - registers the service worker (public/sw.js) in production builds,
 *  - keeps Chrome's install prompt for <InstallButton>,
 *  - shows a small note while offline (the saved gig list is shown).
 */

type InstallPrompt = Event & { prompt: () => Promise<void>; userChoice: Promise<unknown> };

let installPrompt: InstallPrompt | null = null;
const INSTALLABLE = "darksuomi:installable";

export default function AppShell() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
    const onPrompt = (e: Event) => {
      e.preventDefault(); // show our own button instead of Chrome's mini bar
      installPrompt = e as InstallPrompt;
      window.dispatchEvent(new Event(INSTALLABLE));
    };
    const onInstalled = () => {
      installPrompt = null;
      window.dispatchEvent(new Event(INSTALLABLE));
    };
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (!offline) return null;
  return (
    <div
      role="status"
      className="fixed bottom-3 left-1/2 z-50 -translate-x-1/2 rounded bg-gray-900/95 border border-gray-700 px-3 py-1.5 text-xs text-gray-200 shadow-lg"
    >
      Offline – showing the gigs saved on this device
    </div>
  );
}

function isStandalone() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

/**
 * "Install app": Chrome/Edge/Android get the real install dialog; on an
 * iPhone/iPad (no install dialog in Safari) it explains Add to Home Screen,
 * and in the Jolla (Sailfish OS) browser, Add to app grid.
 * Hidden inside the installed app and where installing isn't possible.
 */
export function InstallButton({ className }: { className: string }) {
  const [canPrompt, setCanPrompt] = useState(false);
  const [platform, setPlatform] = useState<"ios" | "sailfish" | null>(null);
  const [showTip, setShowTip] = useState(false);

  useEffect(() => {
    if (isStandalone()) return;
    const sync = () => setCanPrompt(installPrompt !== null);
    sync();
    const ua = navigator.userAgent;
    if (/Sailfish/i.test(ua)) setPlatform("sailfish");
    else if (/iPhone|iPad|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1))
      setPlatform("ios");
    window.addEventListener(INSTALLABLE, sync);
    return () => window.removeEventListener(INSTALLABLE, sync);
  }, []);

  if (canPrompt) {
    return (
      <button
        type="button"
        className={className}
        onClick={async () => {
          const prompt = installPrompt;
          if (!prompt) return;
          await prompt.prompt();
          await prompt.userChoice;
          installPrompt = null;
          setCanPrompt(false);
        }}
      >
        Install app
      </button>
    );
  }
  if (!platform) return null;
  return (
    <>
      <button type="button" className={className} onClick={() => setShowTip((v) => !v)}>
        Install app
      </button>
      {showTip && platform === "ios" && (
        <span className="basis-full text-xs text-gray-400">
          In Safari, tap the Share button{" "}
          <span aria-hidden="true">(□↑)</span>, then <b className="text-gray-200">Add to Home Screen</b>.
        </span>
      )}
      {showTip && platform === "sailfish" && (
        <span className="basis-full text-xs text-gray-400">
          In the Jolla browser, open the page menu and choose{" "}
          <b className="text-gray-200">Add to app grid</b>. Dark Suomi then opens from its own
          icon among your apps.
        </span>
      )}
    </>
  );
}
