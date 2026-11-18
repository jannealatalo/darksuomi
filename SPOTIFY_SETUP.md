# Spotify Login Integration - Setup Guide

Your Dark Suomi site now has Spotify login! 🎵

## 🎯 What It Does

- Users can login with Spotify
- See all events by default
- Green Spotify icon appears next to artists they follow
- Toggle "Show only artists I follow in Spotify" to filter
- Login is saved across sessions

## ⚙️ Setup (5 minutes)

### Step 1: Create Spotify OAuth App

1. Go to https://developer.spotify.com/dashboard
2. Login or create account
3. Click "Create an App"
4. Accept terms → Create
5. You'll get:
   - **Client ID**
   - **Client Secret**

### Step 2: Add Spotify Credentials

Edit `frontend/.env.local`:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
NEXTAUTH_SECRET=generate_with_this_command
NEXTAUTH_URL=http://localhost:3000
```

To generate NEXTAUTH_SECRET, run in PowerShell:
```powershell
$bytes = [System.Text.Encoding]::UTF8.GetBytes("secret")
$secret = [System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
$secret
```

Or use: `openssl rand -base64 32` (if you have Git Bash)

### Step 3: Set Redirect URI in Spotify Dashboard

In your Spotify app settings:
1. Click "Edit Settings"
2. Under "Redirect URIs", add:
   ```
   http://localhost:3000/api/auth/callback/spotify
   ```
3. Click "Add"
4. Save

### Step 4: Install Dependencies

```bash
cd frontend
npm install
```

This installs `next-auth`

### Step 5: Run Locally

```bash
npm run dev
```

Visit http://localhost:3000

You should see "Login with Spotify" button! 🎉

---

## 🌐 Deploy to Vercel

When you deploy to production:

1. In Spotify Dashboard, add redirect URI:
   ```
   https://darksuomi.fi/api/auth/callback/spotify
   ```

2. In Vercel, add environment variables:
   - SPOTIFY_CLIENT_ID
   - SPOTIFY_CLIENT_SECRET
   - NEXTAUTH_SECRET (same value as local)
   - NEXTAUTH_URL=https://darksuomi.fi

3. Deploy:
   ```bash
   git add .
   git commit -m "Add Spotify login integration"
   git push
   ```

---

## 🎸 Features Included

✅ Spotify OAuth login (saves session)
✅ Fetch user's followed artists
✅ Green icon next to followed artists
✅ Toggle filter: "Show only artists I follow"
✅ Shows count of followed artists
✅ Logout button
✅ Responsive UI

---

## 🐛 Troubleshooting

**"Login button doesn't work"**
- Check SPOTIFY_CLIENT_ID and CLIENT_SECRET are correct
- Verify redirect URI in Spotify Dashboard
- Clear browser cookies and try again

**"Can't fetch followed artists"**
- Make sure you have "user-follow-read" scope (already in code)
- Try logging out and logging back in
- Check browser console for errors

**"Build fails: Module not found"**
- Run: `npm install`
- Restart dev server

**".env.local not being read"**
- Restart dev server (`npm run dev`)
- Make sure file is in `frontend/` directory

---

## 📋 Files Added/Modified

**New files:**
- `frontend/auth.ts` - NextAuth configuration
- `frontend/lib/useSpotifyFollowedArtists.ts` - Hook to fetch followed artists
- `frontend/.env.local` - Configuration (don't commit!)

**Modified files:**
- `frontend/app/page.tsx` - Added Spotify login UI and filtering
- `frontend/app/layout.tsx` - Added SessionProvider
- `frontend/package.json` - Added next-auth dependency

---

## 🔐 Security Notes

- .env.local is in .gitignore (secrets not committed) ✅
- NextAuth handles token securely ✅
- Session encrypted with NEXTAUTH_SECRET ✅
- Never share your credentials ✅

---

## ✅ You're Ready!

1. Install dependencies: `npm install`
2. Add Spotify credentials to `.env.local`
3. Add redirect URI in Spotify Dashboard
4. Run: `npm run dev`
5. Click "Login with Spotify"
6. Test filtering

---

**Rock on!** 🎸🤘
