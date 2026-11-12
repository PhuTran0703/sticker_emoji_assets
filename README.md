# sticker_emoji_assets

Sticker artwork for the **Sticker Emoji Maker** app. The app reads
`manifest.json`, then downloads (and caches on device) the images it lists.

## Layout

```
manifest.json                      # index of every pack the app shows
stickers/<category>/<pack_id>/     # one folder per pack
    01.png, 02.png, ...            # 512x512 transparent PNG stickers
tools/remove_bg.py                 # white background -> transparent
```

`<category>` is one of the app's category ids: `animated`, `animals`, `foods`,
`texts`, `love`, `music`, `events`, `holidays`.

## Manifest entry

```json
{
  "id": "christmas_owl",           // pack id (matches the app catalog when it exists)
  "category": "animals",
  "name": "Christmas Owl",         // used for packs the app does not know yet
  "emoji": "🦉",                    // placeholder while images load
  "path": "stickers/animals/christmas_owl",
  "cover": "01.png",               // optional, defaults to the first sticker
  "stickers": ["01.png", "02.png"] // display order = this order
}
```

The app shows exactly the stickers listed here, so the list is the source of
truth for each pack's sticker count.

## Adding a pack

1. Put the source images (white background) in a folder.
2. `pip install -r tools/requirements.txt`
3. `python tools/remove_bg.py <source_dir> stickers/<category>/<pack_id>`
4. Add the pack to `manifest.json` and push.

Files are cached on device by path and never re-downloaded, so **don't
overwrite an existing PNG** — add a new file name instead.
