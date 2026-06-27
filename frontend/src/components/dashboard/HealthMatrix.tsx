import type { HealthAxis } from "../../types/dashboard";

type Props = {
  axes: HealthAxis[];
  score: string;
};

const SIZE = 480;
const CHART_PAD = 40;
const CENTER = SIZE / 2;
const RADIUS = 118;
const BADGE_RADIUS = 13;
const BADGE_RING = RADIUS + 34;
const VALUE_RING = BADGE_RING + BADGE_RADIUS + 18;

type AxisMeta = {
  code: string;
  hint: string;
};

const AXIS_META: Record<string, AxisMeta> = {
  drive_health: {
    code: "DH",
    hint: "Composite SQL health score for this drive.",
  },
  baseline_fit: {
    code: "BF",
    hint: "Coolant fit against this vehicle's session-derived band.",
  },
  airflow: {
    code: "AF",
    hint: "Stability of mass airflow across the logged window.",
  },
  fault_clearance: {
    code: "FC",
    hint: "Penalty-free fault status from logged OBD codes.",
  },
  sensor_balance: {
    code: "SB",
    hint: "Evenness of load and trim penalties from SQL.",
  },
};

function polarPoint(index: number, count: number, value: number, radius = RADIUS) {
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
  const distance = (value / 100) * radius;
  return {
    angle,
    x: CENTER + Math.cos(angle) * distance,
    y: CENTER + Math.sin(angle) * distance,
  };
}

function polygonPoints(axes: HealthAxis[], count: number, scale: number) {
  return axes
    .map((axis, index) => {
      const value = Number(axis.value) * scale;
      const { x, y } = polarPoint(index, count, value);
      return `${x},${y}`;
    })
    .join(" ");
}

/** 0 = red, 100 = teal (chart blue). */
export function scoreColor(value: number): string {
  const t = Math.max(0, Math.min(1, value / 100));
  const red = { r: 168, g: 34, b: 46 };
  const teal = { r: 31, g: 113, b: 108 };
  const r = Math.round(red.r + (teal.r - red.r) * t);
  const g = Math.round(red.g + (teal.g - red.g) * t);
  const b = Math.round(red.b + (teal.b - red.b) * t);
  return `rgb(${r},${g},${b})`;
}

function spokeValueLabel(angle: number, x: number, y: number) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  let textAnchor: "start" | "middle" | "end" = "middle";
  if (cos > 0.45) {
    textAnchor = "start";
  } else if (cos < -0.45) {
    textAnchor = "end";
  }
  const nudge = textAnchor === "middle" ? 0 : 3;
  return {
    x: x + cos * nudge,
    y: y + sin * nudge,
    textAnchor,
  };
}

export function HealthMatrix({ axes, score }: Props) {
  const count = axes.length;
  const gridLevels = [0.25, 0.5, 0.75, 1];
  const dataPoints = polygonPoints(axes, count, 1);
  const referencePoints = polygonPoints(
    axes.map((axis) => ({ ...axis, value: "100" })),
    count,
    1,
  );

  const axisLayouts = axes.map((axis, index) => {
    const value = Number(axis.value);
    const vertex = polarPoint(index, count, value);
    const badge = polarPoint(index, count, 100, BADGE_RING);
    const valuePoint = polarPoint(index, count, 100, VALUE_RING);
    const valueLabel = spokeValueLabel(vertex.angle, valuePoint.x, valuePoint.y);
    const meta = AXIS_META[axis.id] ?? { code: String(index + 1), hint: axis.label };
    return { axis, index, vertex, badge, meta, valueLabel, value };
  });

  const legendItems = [...axisLayouts].sort((a, b) => b.value - a.value);

  return (
    <div className="healthMatrixWrap">
      <div className="matrixStage">
        <svg
          className="healthMatrixChart"
          viewBox={`-${CHART_PAD} -${CHART_PAD} ${SIZE + CHART_PAD * 2} ${SIZE + CHART_PAD * 2}`}
          role="img"
          aria-label={`Performance profile for drive score ${score}`}
        >
          <defs>
            <linearGradient
              id="performancePolygonGradient"
              x1="0"
              y1="0"
              x2="0"
              y2={SIZE}
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#cc2936" />
              <stop offset="100%" stopColor="#1f716c" />
            </linearGradient>
          </defs>
          {gridLevels.map((level) => (
            <polygon
              key={level}
              className="healthMatrixGrid"
              points={axes
                .map((_, index) => {
                  const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
                  const distance = RADIUS * level;
                  const x = CENTER + Math.cos(angle) * distance;
                  const y = CENTER + Math.sin(angle) * distance;
                  return `${x},${y}`;
                })
                .join(" ")}
            />
          ))}
          {axisLayouts.map(({ index }) => {
            const spokeEnd = polarPoint(index, count, 100, RADIUS);
            return (
              <line
                key={`axis-${index}`}
                className="healthMatrixAxis"
                x1={CENTER}
                y1={CENTER}
                x2={spokeEnd.x}
                y2={spokeEnd.y}
              />
            );
          })}
          <polygon className="healthMatrixRef" points={referencePoints} />
          <polygon className="healthMatrixShape" points={dataPoints} />
          {axisLayouts.map(({ vertex, value, index }) => {
            const dotColor = scoreColor(value);
            return (
              <g key={`vertex-${index}`} className="matrixVertexGroup">
                <circle
                  className="matrixVertexRing"
                  cx={vertex.x}
                  cy={vertex.y}
                  r="8"
                  stroke={dotColor}
                />
                <circle
                  className="matrixVertex"
                  cx={vertex.x}
                  cy={vertex.y}
                  r="5"
                  fill={dotColor}
                />
              </g>
            );
          })}
          {axisLayouts.map(({ badge, meta, valueLabel, index }) => (
            <g key={`badge-${index}`} className="matrixAxisUnit">
              <circle
                className="matrixAxisBadgeCircle"
                cx={badge.x}
                cy={badge.y}
                r={BADGE_RADIUS}
              />
              <text
                className="matrixAxisBadgeCode"
                x={badge.x}
                y={badge.y}
                textAnchor="middle"
                dominantBaseline="central"
              >
                {meta.code}
              </text>
              <text
                className="matrixAxisSpokeValue"
                x={valueLabel.x}
                y={valueLabel.y}
                textAnchor={valueLabel.textAnchor}
                dominantBaseline="central"
              >
                {axes[index].value}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <div className="matrixLegendPanel">
        <p className="matrixLegendTitle">Axis legend · high to low</p>
        <ol className="matrixLegendGrid" aria-label="Performance axis legend sorted by score">
          {legendItems.map(({ axis, meta, value }) => {
            const railColor = scoreColor(value);
            return (
              <li key={axis.id} className="matrixLegendCard">
                <span
                  className="matrixLegendRail"
                  aria-hidden
                  style={{ backgroundColor: railColor }}
                />
                <div className="matrixLegendRow">
                  <span
                    className="matrixAxisBadge"
                    title={meta.hint}
                    style={{
                      boxShadow: `inset 0 0 0 1.5px ${railColor}`,
                      backgroundColor: `color-mix(in srgb, ${railColor} 22%, transparent)`,
                    }}
                  >
                    {meta.code}
                  </span>
                  <div className="matrixLegendHead">
                    <strong style={{ color: railColor }}>{axis.value}</strong>
                    <span>{axis.label}</span>
                  </div>
                </div>
                <p className="matrixLegendHint">{meta.hint}</p>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
