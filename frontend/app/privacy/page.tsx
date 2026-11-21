import type { Metadata } from "next";
import Link from "next/link";
import SiteFooter, { CONTACT_EMAIL } from "../SiteFooter";

export const metadata: Metadata = {
  title: "Privacy – Dark Suomi",
  description: "How Dark Suomi handles personal data.",
};

const UPDATED = "21.11.2026";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold text-gray-100">{title}</h2>
      {children}
    </section>
  );
}

export default function PrivacyPage() {
  const mail = (
    <a href={`mailto:${CONTACT_EMAIL}`} className="text-purple-400 hover:text-purple-300">
      {CONTACT_EMAIL}
    </a>
  );

  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-2xl mx-auto px-6 py-10 space-y-8 leading-relaxed">
        <p>
          <Link href="/" className="text-purple-400 hover:text-purple-300">
            ← Back to gigs
          </Link>
        </p>

        <header className="space-y-1">
          <h1 className="text-3xl font-bold text-gray-100">Privacy</h1>
          <p className="text-sm text-gray-500">Last updated {UPDATED}</p>
        </header>

        <p>
          Dark Suomi (darksuomi.fi) is a non-commercial listing of alternative
          music gigs in Finland. It is run by Dark Suomi, contact: {mail}. This
          page explains what personal data the site handles. In short: very little.
        </p>

        <Section title="Browsing the site">
          <p>
            You can use the gig listing without logging in. Dark Suomi has no
            advertising and no tracking cookies, and it does not load fonts or
            scripts from third-party services.
          </p>
          <p>
            To see how much the site is used, Dark Suomi uses{" "}
            <a
              href="https://vercel.com/docs/analytics/privacy-policy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              Vercel Web Analytics
            </a>
            . It counts page views anonymously: it uses no cookies, does not store
            IP addresses and cannot follow you across sites or days. Only
            summary numbers are kept, such as which pages are visited, the
            referring site, the country and the device type.
          </p>
          <p>
            The site is hosted by Vercel. Like any web host, Vercel keeps short-term
            technical server logs (such as IP address, browser type and the page
            requested) to run and protect the service. See{" "}
            <a
              href="https://vercel.com/legal/privacy-policy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              Vercel&apos;s privacy policy
            </a>
            .
          </p>
          <p>
            Filter choices (genres, venues) are kept only in the open page and are
            forgotten when you leave it.
          </p>
        </Section>

        <Section title="Logging in with Spotify (optional, invite only)">
          <p>
            If you log in with Spotify, the site asks Spotify only for permission to
            read the artists you follow. With that:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              Your Spotify display name and the login tokens are kept in an encrypted
              login cookie in your own browser. Dark Suomi has no user database and
              does not store them on any server.
            </li>
            <li>
              Your followed artists are fetched directly from Spotify by your browser
              and used only to mark and filter gigs on the page. They are not saved
              or sent anywhere else.
            </li>
            <li>
              The login cookie is strictly necessary for the login to work, so no
              cookie consent banner is needed. It lasts up to 30 days, or until you
              log out.
            </li>
          </ul>
          <p>
            You can remove the site&apos;s access at any time from your{" "}
            <a
              href="https://www.spotify.com/account/apps/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              Spotify account&apos;s app settings
            </a>
            . Logging out deletes the login cookie.
          </p>
        </Section>

        <Section title="Links and playlists">
          <p>
            Gig, ticket, Spotify playlist and setlist links lead to other services
            (venues, ticket sellers, Spotify, setlist.fm). Their own privacy policies
            apply when you visit them.
          </p>
        </Section>

        <Section title="Your rights">
          <p>
            Under the EU General Data Protection Regulation you can ask what data
            concerns you and ask for it to be corrected or deleted. Because Dark Suomi
            stores no personal data on its own servers, logging out (or clearing your
            browser&apos;s cookies for darksuomi.fi) removes everything. For questions,
            contact {mail}. You can also contact the Finnish Data Protection
            Ombudsman (tietosuoja.fi).
          </p>
        </Section>

        <Section title="Suomeksi lyhyesti">
          <p>
            Dark Suomi ei käytä analytiikkaa, mainoksia eikä seurantaevästeitä.
            Vapaaehtoinen Spotify-kirjautuminen lukee vain seuraamasi artistit;
            nimesi ja kirjautumistiedot säilyvät salattuna evästeenä omassa
            selaimessasi, eikä niitä tallenneta palvelimelle. Sivuston ylläpitäjä
            Vercel säilyttää tavanomaisia teknisiä lokitietoja. Yhteydenotot:{" "}
            {mail}.
          </p>
        </Section>

        <SiteFooter />
      </div>
    </main>
  );
}
