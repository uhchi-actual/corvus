/** 0 = red, 100 = teal. */
export function scoreColor(value: number): string {
  const t = Math.max(0, Math.min(1, value / 100));
  const red = { r: 168, g: 34, b: 46 };
  const teal = { r: 31, g: 113, b: 108 };
  const r = Math.round(red.r + (teal.r - red.r) * t);
  const g = Math.round(red.g + (teal.g - red.g) * t);
  const b = Math.round(red.b + (teal.b - red.b) * t);
  return `rgb(${r},${g},${b})`;
}
