# BScout homepage redesign packet

This folder is a self-contained visual and asset handoff for the public homepage redesign. The approved visual direction is a white page, BScout green, crisp futuristic spray accents, restrained glass surfaces, and the same person-like rabbit mascot.

## References

- `assets/reference/homepage-approved.png` — latest approved full-page concept with the larger footer.
- `assets/reference/homepage-current.png` — existing homepage screenshot; use for real content and current information architecture.
- `assets/reference/tariff-glass-reference.JPG` — target glass material and layered title/card composition for pricing.

## Brand and existing data assets

- `assets/brand/Logo.svg` — copy of the canonical `frontend/public/Logo.svg`. Prefer the repository's canonical file at runtime; this copy keeps the packet portable.
- `assets/shops/` — current retailer marks used by the homepage carousel: Profi, Liberty, Divizion, and TGSM. Keep existing external targets from the app; do not invent social or retailer URLs.

## Mascot

- `assets/mascots/mascot-hero.png` — accepted presenting pose for the hero.
- `assets/mascots/mascot-presenting.png`, `mascot-calm.png`, `mascot-pointing.png`, `mascot-pointing-alt.png` — matching full-body pose variations for alternating homepage sections.
- These five images are RGBA PNGs with transparency and the same white rabbit / emerald jacket identity. Mirror the hero presentation only if needed so its gaze points inward toward the headline and search.
- `assets/motion/mascot-direction-blink-reference.png` — four-frame visual reference (2172×724): head looking left, center, right, and eyes closed. The file has an alpha channel, but its preview appears white. Verify that the background pixels are actually transparent and test it on white before using it as a runtime sprite. Do not ship a visible white rectangle over any background; if it is not genuinely transparent, treat it as a state reference and use a separate head layer or another clean implementation.

## Icons and decoration

- `assets/icons/benefit-icons-sprite.png` — wide 3D icon sprite (2172×724) with three panels: frosted stacked cards, emerald lightning, and glass shield/check. Verify transparency and crop by equal thirds if using the sheet directly.
- `assets/splashes/spray-wide.png` — wide emerald/charcoal particle spray (2172×724) with open center.
- `assets/splashes/spray-corner.png` — compact asymmetric corner spray (1536×1024).
- Use the sprays sparingly at section edges. Keep text, controls, and mascot faces unobstructed. Do not stretch them into continuous ribbons or turn them into a full-page noisy background.

## Important content boundary

The approved mockup is visual direction, not a data source. Its sample merchant rows and prices must not be copied into production unless current application data confirms them. Use current API-backed tariff plans and real, configured destinations only. Do not add invented prices, shops, phone numbers, addresses, contact details, social accounts, metrics, or slogans.
