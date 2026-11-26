import { CONTACT_EMAIL, DISCORD_INVITE, INSTAGRAM_URL } from "../lib/site";

const link = "text-purple-400 hover:text-purple-300";

/** Shown when a search finds no gigs: a joke and a way to tell us what is missing. */
export default function NoHits() {
  return (
    <>
      Nothing found. Maybe they broke up. Maybe they never existed. Or maybe
      their gig is just missing from our list – if so, drop us a hint via{" "}
      <a href={DISCORD_INVITE} target="_blank" rel="noopener noreferrer" className={link}>
        Discord
      </a>
      ,{" "}
      <a href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer" className={link}>
        Instagram
      </a>{" "}
      or good ol&apos;{" "}
      <a href={`mailto:${CONTACT_EMAIL}`} className={link}>
        email
      </a>
      .
    </>
  );
}
