# Video Vervangings Helper

## Stap 1: Video's Optimaliseren voor Web

Voordat je video's toevoegt, optimaliseer ze:

```bash
# Comprimeer video (installeer ffmpeg eerst: brew install ffmpeg)
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac -b:a 128k -movflags +faststart output.mp4

# Voor web optimalisatie (kleinere file):
ffmpeg -i input.mp4 -c:v libx264 -crf 30 -preset fast -c:a aac -b:a 96k -movflags +faststart -vf "scale=1920:1080" output.mp4
```

## Stap 2: Video's Toevoegen aan Assets

Plaats video's in: `/longread/assets/`

Bestandsnamen (suggestie):
- `oosterweelverbinding.mp4`
- `ring-brussel.mp4` 
- `fietssnelwegen.mp4`
- `waterbeheersing.mp4`
- `albertkanaal.mp4`

## Stap 3: HTML Template voor Vervangen

Gebruik dit template voor elke video:

```html
<video autoplay muted loop playsinline preload="metadata" 
       title="[VIDEO_TITLE]"
       class="video-player">
    <source src="assets/[VIDEO_FILENAME].mp4" type="video/mp4">
    <p>Your browser doesn't support HTML5 video. <a href="assets/[VIDEO_FILENAME].mp4">Download the video</a> instead.</p>
</video>
```

## Stap 4: Vervangingslijst

1. **Oosterweelverbinding** (regel ~221)
2. **Ring Brussel** (regel ~240) 
3. **Fietssnelwegen** (regel ~299)
4. **Sigmaplan** (regel ~361)
5. **Albertkanaal** (regel ~417)

## Optimalisatie Tips

- **Maximale filesize:** ~15MB per video (voor goede laadtijden)
- **Resolutie:** 1920x1080 of 1280x720
- **Duur:** 15-60 seconden (looping videos)
- **Format:** MP4 met H.264 encoding

## Alternatieve Bronnen (Rechtenvrij)

1. **Pexels Videos** - https://www.pexels.com/videos/
2. **Pixabay Videos** - https://pixabay.com/videos/
3. **Unsplash Videos** - https://unsplash.com/videos/
4. **Videvo** - https://www.videvo.net/
5. **Wikimedia Commons** - https://commons.wikimedia.org/

Zoektermen voor infrastructuur:
- "construction", "infrastructure", "road building"
- "bridge construction", "highway", "cycling infrastructure"  
- "water management", "flooding", "harbor", "waterway"