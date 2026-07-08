export const SLIDE = {
  width: 13.333,
  height: 7.5,
  marginX: 0.55,
  titleY: 0.42,
  footerY: 7.08
};

export const DEFAULT_BRAND = {
  primary: "0B1F33",
  secondary: "C8A45D",
  accent: "2E7D6B",
  danger: "B54747",
  neutral: "F4F1EA",
  text: "18212B",
  muted: "6B7280",
  background: "FFFFFF",
  fontFace: "Microsoft YaHei"
};

export function brandFrom(structure) {
  return { ...DEFAULT_BRAND, ...(structure.brand || {}) };
}

export function box(id, role, x, y, w, h, extra = {}) {
  return { id, role, x, y, w, h, ...extra };
}

export function normalizeHex(value) {
  return String(value || "").replace(/^#/, "").toUpperCase();
}
