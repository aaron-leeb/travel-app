# Replace your photos

The homepage slideshow shows these files from `static/images/`, in order:

1. `hero-caribbean.jpg`: Caribbean beach photo
2. `hero-sahara.jpg`: Sahara photo
3. `hero-kenya.jpg`: Kenya safari photo

To swap a photo, replace the file using exactly the same filename. Wide photos
around 1920 x 1080 work best; small images look blurry when stretched across
the hero. Hard-refresh the browser (Ctrl+F5) if the old photo remains.

To add, remove, or reorder slides, edit the `slideImages` list in
`static/js/app.js`. Slides change every five seconds (the `5000` in the same
file). Autoplay is off for visitors who prefer reduced motion.

The other images in `static/images/` and the copies directly in `static/` are
not used by any page.
