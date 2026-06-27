/** Strip VehId/Trip suffixes — display only the archive filename. */
export function cleanSourceFile(raw: string): string {
  const text = raw.trim();
  if (!text) {
    return text;
  }
  const csvMatch = text.match(/^[^;]+?\.csv/i);
  if (csvMatch) {
    return csvMatch[0];
  }
  const semi = text.indexOf(";");
  return semi >= 0 ? text.slice(0, semi).trim() : text;
}
