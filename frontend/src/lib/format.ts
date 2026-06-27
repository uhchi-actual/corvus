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

type TrendPoint = { ts: string; maf_30s: string };

export function trendChartAxes(trend: TrendPoint[]) {
  if (trend.length === 0) {
    return { start: "0:00", end: "0:00", maxG: "0" };
  }

  const startMs = Date.parse(trend[0].ts);
  const endMs = Date.parse(trend[trend.length - 1].ts);
  const elapsed = (ms: number) => {
    const totalSec = Math.max(0, Math.round((ms - startMs) / 1000));
    const minutes = Math.floor(totalSec / 60);
    const seconds = totalSec % 60;
    return `${minutes}:${String(seconds).padStart(2, "0")}`;
  };
  const maxG = Math.max(...trend.map((point) => Number(point.maf_30s)));

  return {
    start: elapsed(startMs),
    end: elapsed(endMs),
    maxG: maxG.toFixed(1),
  };
}

export function formatDriveWindow(startedAt: string, endedAt: string) {
  const startMs = Date.parse(startedAt);
  const endMs = Date.parse(endedAt);
  const clock = (ms: number) =>
    new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs <= startMs) {
    return {
      clock: "—",
      durationSec: 0,
      duration: "—",
    };
  }

  const durationSec = Math.round((endMs - startMs) / 1000);
  const minutes = Math.floor(durationSec / 60);
  const seconds = durationSec % 60;
  const duration =
    minutes > 0 ? `${minutes}m ${String(seconds).padStart(2, "0")}s` : `${seconds}s`;

  return {
    clock: `${clock(startMs)} – ${clock(endMs)}`,
    durationSec,
    duration,
  };
}
