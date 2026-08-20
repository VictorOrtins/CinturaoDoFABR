/**
 * Cheap perceived-brightness heuristic (not full WCAG relative luminance —
 * no gamma correction) used to pick readable text over an arbitrary team
 * brand color used as a hero background.
 */
export function getContrastingTextColor(hex: string | null | undefined): string {
  const normalized = (hex ?? "").replace("#", "");
  if (normalized.length !== 6) return "#ffffff";

  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  const brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return brightness > 0.6 ? "#171310" : "#ffffff";
}

/**
 * The opposite of getContrastingTextColor — used for hard-shadow text
 * treatments (see docs/DESIGN.md, eatrocketfuel reference) so the shadow
 * always reads as a genuine two-tone comic outline against an arbitrary
 * team primary_color, instead of picking a fixed shadow color that could
 * vanish against some team's brand hue.
 */
export function getHardShadowColor(hex: string | null | undefined): string {
  return getContrastingTextColor(hex) === "#ffffff" ? "#171310" : "#ffffff";
}
