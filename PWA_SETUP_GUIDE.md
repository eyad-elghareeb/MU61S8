# PWA Setup Guide for GitHub Pages

## Files Created/Updated

1. **manifest.json** - Web app manifest with app metadata
2. **sw.js** - Service worker for offline caching
3. **pwa-install.js** - Install prompt handler with auto button
4. **check-pwa.html** - Diagnostic page to test PWA functionality

## What Was Fixed

### Common Issues Addressed:

1. **Cache Version Updated** - Changed from v2 to v4 to force new cache
2. **Manifest start_url** - Changed from "/" to "/index.html" for GitHub Pages compatibility
3. **Added scope** - Explicitly set scope to "/"
4. **Multiple icon sizes** - Added 192x192 and 512x512 icons
5. **Enhanced logging** - Added [SW] and [PWA] prefixes for easier debugging
6. **Auto install button** - Creates floating install button automatically

## Testing Instructions

### Step 1: Deploy to GitHub Pages
```bash
git add .
git commit -m "Fix PWA setup"
git push
```

Wait 1-2 minutes for GitHub Pages to deploy.

### Step 2: Test with Diagnostic Page
Visit: `https://yourusername.github.io/your-repo/check-pwa.html`

This page will show:
- ✓ Service Worker registration status
- ✓ Manifest loading status
- ✓ Cache status
- ✓ Install availability
- Real-time console logs

### Step 3: Test Offline Mode
1. Visit your main site first to cache assets
2. Open DevTools → Application → Service Workers
3. Check "Offline" checkbox
4. Refresh the page - it should still work!

### Step 4: Test Installation
- **Desktop Chrome/Edge**: Look for install icon in address bar OR floating "📲 Install App" button
- **Android Chrome**: Should show install banner or "Add to Home Screen" option
- **iOS Safari**: Tap Share → "Add to Home Screen"

## Troubleshooting

### Issue: "Install prompt not appearing"
**Solutions:**
- Must visit site at least twice (with some time between visits)
- Must use HTTPS (GitHub Pages provides this)
- Try clearing browser cache and cookies
- Check check-pwa.html diagnostics

### Issue: "Offline mode not working"
**Solutions:**
- Visit the main pages first while online to cache them
- Check DevTools Console for service worker errors
- Verify sw.js is being loaded (check Network tab)
- Clear old caches: DevTools → Application → Storage → Clear site data

### Issue: "Old version showing after update"
**Solutions:**
- The cache version (v4) forces new cache on next visit
- Users may need to close all tabs and reopen
- Or wait ~24 hours for automatic update

### Issue: "Service Worker registration failed"
**Check:**
- File paths are correct (all use absolute paths starting with /)
- No mixed content (HTTP resources on HTTPS site)
- GitHub Pages deployment completed successfully

## Browser Support

| Browser | Install Support | Offline Support |
|---------|----------------|-----------------|
| Chrome Desktop | ✓ | ✓ |
| Chrome Android | ✓ | ✓ |
| Edge | ✓ | ✓ |
| Firefox | Limited | ✓ |
| Safari iOS | Manual* | ✓ |
| Safari Mac | Manual* | ✓ |

*iOS requires manual "Add to Home Screen"

## Key Features

1. **Cache-First Strategy** - Loads from cache instantly, updates in background
2. **Automatic Updates** - New cache version deployed = auto update on next visit
3. **Offline Fallback** - Shows index.html if page not cached
4. **Dynamic Caching** - Caches pages as you visit them
5. **Install Prompt** - Auto-floating button + browser native prompt

## Next Steps

1. Push changes to GitHub
2. Wait for deployment (~1-2 minutes)
3. Visit check-pwa.html to verify everything works
4. Test offline mode
5. Share with users!
