/** Release date formatting, apart from the release data so client components stay small. */

const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
  "August", "September", "October", "November", "December"];

/** "14.3.2027", "March 2027" or "2027". */
export function releaseDate(d: string): string {
  const [y, m, day] = d.split("-").map(Number);
  if (day) return `${day}.${m}.${y}`;
  if (m) return `${MONTHS[m - 1]} ${y}`;
  return String(y);
}
