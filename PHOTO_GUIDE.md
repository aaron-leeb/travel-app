# Replace your photos

Photos are in `travel-app/static/images/`.

Home slideshow, in order:
1. `hero-island.jpg`: earlier island photo
2. `hero-sahara.jpg`: Sahara photo
3. `hero-caribbean.jpg`: Caribbean beach photo
4. `hero-kenya.jpg`: Kenya safari photo. This currently copies the desert image as a placeholder. Replace it with your own Kenya photo.

Replace these files with JPG photos using exactly the same filenames. Wide photos around 1920 x 1080 work best. Refresh the browser after saving; use a hard refresh if the old photo remains.

To change captions, add slides, or use PNG/WebP images, edit `heroSlides` near the bottom of `static/js/app.js`. Set `heroIntervalMs` to change the five-second interval.

Destination cards use the image names in `app.py`. Their files are also in `static/images/`. The cold cards currently share `alpine.svg`.

The slideshow pauses while hovered, while its controls or search fields have keyboard focus, and when the browser tab is hidden. It has arrows, dots, a pause/play button, and touch swipe. Reduced-motion preferences disable autoplay initially.
