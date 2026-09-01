# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: home.spec.ts >> Home Page >> should have responsive layout
- Location: e2e\tests\home.spec.ts:16:3

# Error details

```
Error: browserContext.newPage: Executable doesn't exist at D:\eco_nojin\node_modules\.pnpm\playwright-core@1.62.1\node_modules\playwright-core\.local-browsers\ffmpeg-1011\ffmpeg-win64.exe
╔═════════════════════════════════════════════════════════════════╗
║ Video rendering requires ffmpeg binary.                         ║
║ Downloading it will not affect any of the system-wide settings. ║
║ Please run the following command:                               ║
║                                                                 ║
║     pnpm exec playwright install ffmpeg                         ║
║                                                                 ║
║ <3 Playwright Team                                              ║
╚═════════════════════════════════════════════════════════════════╝
```