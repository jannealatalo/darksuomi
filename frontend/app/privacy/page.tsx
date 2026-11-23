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
            forgotten when you leave it. &quot;Filter what DarkSuomi recommends&quot;
            uses a list of bands kept on the site; it needs nothing from you.
          </p>
        </Section>

        <Section title="Your Last.fm username (optional)">
          <p>
            If you enter a Last.fm username to find gigs by bands you listen to:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              The username is remembered only in your own browser (local storage),
              so the site can show your bands on your next visit. Removing it on the
              page, or clearing the site data, forgets it.
            </li>
            <li>
              The site&apos;s server asks{" "}
              <a
                href="https://www.last.fm/legal/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 hover:text-purple-300"
              >
                Last.fm
              </a>{" "}
              for that user&apos;s public list of most played artists and keeps the
              answer in a temporary cache for a few hours. Nothing is saved in a
              database, and no login or password is involved.
            </li>
          </ul>
        </Section>

        <Section title="Daily updates by email (optional)">
          <p>
            If you subscribe to the daily updates, your email address is stored by{" "}
            <a
              href="https://buttondown.com/legal/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              Buttondown
            </a>
            , the newsletter service that sends the emails. It is used only to send
            you the list of new gigs, on the days there are some. Buttondown asks
            you to confirm the subscription by email, and every email has an
            unsubscribe link; unsubscribing removes you from the list. Dark Suomi
            does not share or sell the list. To have your address deleted, use the
            unsubscribe link or contact {mail}.
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
            stores no personal data on its own servers, clearing your browser&apos;s
            site data for darksuomi.fi removes everything; an email
            subscription is removed by unsubscribing. For questions,
            contact {mail}. You can also contact the Finnish Data Protection
            Ombudsman (tietosuoja.fi).
          </p>
        </Section>

        <Section title="Suomeksi lyhyesti">
          <p>
            Dark Suomi ei käytä mainoksia eikä seurantaevästeitä. Kävijämäärät
            lasketaan nimettömästi Vercel Web Analyticsilla ilman evästeitä.
            Jos annat Last.fm-käyttäjänimen, se muistetaan vain omassa
            selaimessasi, ja palvelin hakee Last.fm:stä sen julkisen listan
            kuunnelluimmista artisteista (välimuistissa muutaman tunnin). Jos tilaat päivittäiset
            keikkapäivitykset sähköpostiin, osoitteesi säilyttää uutiskirjepalvelu
            Buttondown, ja tilauksen voi perua jokaisen viestin linkistä. Sivuston
            ylläpitäjä Vercel säilyttää tavanomaisia teknisiä lokitietoja.
            Yhteydenotot:{" "}
            {mail}.
          </p>
        </Section>

        <SiteFooter />
      </div>
    </main>
  );
}
