# SNES Studio Discord Activity

SNES Studio can run as a Discord Activity: a web app embedded in Discord and launched from the App Launcher.

## Discord application

- Name: `SNES Studio`
- Application ID / Client ID: `1514005235205668924`
- Public Key: `f47a2a4b0e4981a76f7bb7288cb9de372693dafef108d9ebf0da9b12ef3ec493`
- App Icon: `web/public/branding/discord-icon-1024.png`
- Description: `Create and share SNES-style games in Discord. Build maps, sprites, events, top-down adventures, and platformer scenes, then export your project.`
- Tags: `snes`, `super-nintendo`, `game-dev`, `pixel-art`, `education`

Do not commit a bot token or client secret. The web Activity only needs the public client ID.

## Required Developer Portal setup

1. Open Discord Developer Portal → Applications → SNES Studio.
2. Go to OAuth2 and add the redirect URI `https://127.0.0.1`.
3. Go to Installation and enable both User Install and Guild Install.
4. Go to Activities → Settings and enable Activities.
5. Keep the default Entry Point command, or rename it to `Launch SNES Studio`.
6. Deploy `web/dist` to a public HTTPS host such as Vercel, Netlify, or your own domain.
7. Go to Activities → URL Mappings and add one root mapping:

| Prefix | Target |
| --- | --- |
| `/` | `<your-public-host>` |

The target must not include `https://`. For example, use `snes-studio.vercel.app`, not `https://snes-studio.vercel.app`.

GitHub Pages can also work, but only if Pages is enabled for the repository and plan. If using project Pages, build with relative assets as this repo does, then map `/` to the project page directory target.

## Build configuration

Set the Vite public client ID when building for a different Discord application:

```powershell
$env:VITE_DISCORD_CLIENT_ID="1514005235205668924"
cd web
npm run build
```

SNES Studio defaults to the application ID above if no environment variable is set.

## Local Discord test

Discord Activities require a public URL mapping, so local Vite needs a tunnel:

```powershell
cd web
npm run dev -- --host 127.0.0.1
cloudflared tunnel --url http://localhost:5173
```

Then set Activities → URL Mappings:

| Prefix | Target |
| --- | --- |
| `/` | `<your-cloudflared-host>.trycloudflare.com` |

Launch SNES Studio from the Discord App Launcher in a test server, DM, or group DM.

## Discord limitations

- The embedded Activity runs in online demo mode unless the user opens the desktop app separately.
- Discord proxies Activity networking through URL Mappings. Add mappings before using external APIs/CDNs from inside the Activity.
- Optional AI tools are hidden by default. Users can enable them in Studio Settings.
- Project sharing is currently file-based: use `Download project`, then share the `.snesproj` file.
