# Spotify: playlists and "DarkSuomi recommends"

The site has no visitor Spotify login. Spotify is used only through the
**Dark Suomi Spotify account**, by the nightly job:

- `playlists.py` makes the expected-setlist playlists in that account.
- `recommended.py` lists the artists that account follows into
  `frontend/data/recommended.json`. Their gigs get a "★ DarkSuomi" tag and
  the "Filter what DarkSuomi recommends" button shows only them.

**To recommend a band:** follow it on Spotify while logged in as the Dark
Suomi account. It shows up on the site after the next nightly run
(unfollow to remove it).

## Setup

Both scripts use the "Dark Suomi playlists" Spotify app and one refresh
token with the scopes `playlist-modify-public playlist-modify-private
ugc-image-upload user-follow-read`.

1. Stop `npm run dev` (the script needs port 3000).
2. Run `python spotify_authorize.py` and log in as the Dark Suomi account.
   It saves the Windows user env vars `SPOTIFY_PLAYLIST_CLIENT_ID`,
   `SPOTIFY_PLAYLIST_CLIENT_SECRET` and `SPOTIFY_PLAYLIST_REFRESH_TOKEN`.
3. Paste the printed refresh token into the GitHub secret
   `SPOTIFY_PLAYLIST_REFRESH_TOKEN`.
4. Check with `python recommended.py`.

If `recommended.py` says the token lacks the user-follow-read scope, the
token is older than that scope: repeat the steps above.
