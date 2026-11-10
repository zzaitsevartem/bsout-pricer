# Mascot motion guide: pointer tracking and blinking

This guide is specific to the BScout homepage mascot. Read it together with `AGENT_PROMPT.md`, `ASSET_GUIDE.md`, and `.agents/skills/animate/SKILL.md`. The motion should make the rabbit feel attentive to the product, not turn the page into an animation demo.

## Head follows the cursor

1. Keep the mascot's body pose fixed. Only the head and gaze turn. Do not rotate, translate, or scale the full-body image to imitate a head turn.
2. Make a small reusable client-side `HomeMascot` component. Keep the surrounding section server-rendered when possible. The image in `assets/motion/mascot-direction-blink-reference.png` gives left, center, right, and blink states; verify real alpha transparency before using it as a runtime sprite. The preview appears white-backed. If any box, edge, or mismatch is visible, use the file only as a reference and create a clean head/eye layer that matches the supplied transparent body art.
3. Listen to pointer movement only while the mascot's section is visible and only for a fine mouse pointer. Use coordinates relative to that section/mascot, clamp the turn to a restrained range (about ±6–8° yaw and ±3–4° pitch), and return the head to center on pointer leave.
4. Animate `transform` only. Use the existing motion/easing tokens or a small spring already present in the repository; do not add a dependency for this effect. Avoid global pointer listeners if a section-level listener works. Disable tracking on touch/coarse pointers and under `prefers-reduced-motion`.
5. The hero rabbit sits to the right and faces inward toward the headline/search. Later mascots alternate sides and poses, but they must keep their eyes on the cursor inside their own visible section. Use `pointer-events: none` and `aria-hidden="true"` for decorative mascot art so it never blocks controls or enters the accessibility tree.

## Natural blink

1. Use a real closed-eye visual state (a matched eyelid/head frame or a small eyelid layer), not a whole-face fade or a CSS scale that distorts the eyes.
2. Blink at a slightly varied interval of about 3–6 seconds. Close briefly for about 100–140 ms, then return to open eyes. Avoid synchronized blinking across all mascot instances.
3. Run a blink timer only for the mascot that is visible or near the viewport. Pause/clear its timer and pointer work when the section leaves view, the component unmounts, or the document is hidden. Respect reduced motion by suppressing decorative head travel and reducing or disabling periodic blink.

## Interaction checks

- Move the pointer left and right within the hero: the rabbit turns its head toward it while its body stays still; leaving the section returns the head to neutral.
- Repeat in another section to confirm each mascot follows the pointer relative to its own section.
- Wait for a blink: eyelids close and reopen quickly without a visible jump in head position, crop, or identity.
- Confirm mouse tracking is absent on touch/coarse pointers and with reduced motion enabled.
- Scroll several sections away and back: no old timers/listeners keep running, no missed blink state remains, and no mascot blocks a CTA.
- Check at desktop and mobile sizes against a white background and glass-card edges. Do not ship a white sprite rectangle, clipping seam, distorted head, or full-body rotation.

## Focused tests for Terra

Test observable states with mocked pointer events and fake timers:

- left/right pointer position changes only the head/gaze state; body stays untransformed;
- pointer leave recenters the head;
- a closed-eye state appears briefly and returns to open eyes;
- pointer listeners and blink timers stop on unmount/offscreen state;
- touch and reduced-motion modes do not start cursor-driven head travel.

Luna reads the tests after Terra writes them. Sol owns production changes and integration. No Astra is part of this task.
