import type { HealthAxis } from "../../types/dashboard";

type Props = {
  axes: HealthAxis[];
  score: string;
};

const SIZE = 480;
const CENTER = SIZE / 2;
const RADIUS = 128;
const BADGE_RADIUS = 13;
const BADGE_RING = RADIUS + 30;
const SPOKE_VALUE_OFFSET = 24;

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
    const meta = AXIS_META[axis.id] ?? { code: String(index + 1), hint: axis.label };
    return { axis, index, vertex, badge, meta };
  });

  return (
    <div className="healthMatrixWrap">
      <div className="matrixStage">
        <svg
          className="healthMatrixChart"
          viewBox={`0 0 ${SIZE} ${SIZE}`}
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
          {axisLayouts.map(({ vertex, index }) => (
            <g key={`vertex-${index}`} className="matrixVertexGroup">
              <circle className="matrixVertex" cx={vertex.x} cy={vertex.y} r="5" />
              <circle className="matrixVertexRing" cx={vertex.x} cy={vertex.y} r="8" />
            </g>
          ))}
          {axisLayouts.map(({ badge, meta, vertex, index }) => {
            const angleDeg = (vertex.angle * 180) / Math.PI + 90;
            return (
              <g
                key={`badge-${index}`}
                className="matrixAxisUnit"
                transform={`translate(${badge.x} ${badge.y}) rotate(${angleDeg})`}
              >
                <circle className="matrixAxisBadgeCircle" cx={0} cy={0} r={BADGE_RADIUS} />
                <text className="matrixAxisBadgeCode" x={0} y={0}>{meta.code}</text>
                <text className="matrixAxisSpokeValue" x={0} y={SPOKE_VALUE_OFFSET}>
                  {axes[index].value}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="matrixLegendPanel">
        <p className="matrixLegendTitle">Axis legend</p>
        <ol className="matrixLegendGrid" aria-label="Performance axis legend">
          {axisLayouts.map(({ axis, meta, index }) => (
            <li key={axis.id} className="matrixLegendCard">
              <span className="matrixLegendRail" aria-hidden />
              <div className="matrixLegendRow">
                <span className="matrixAxisBadge" title={meta.hint}>{meta.code}</span>
                <div className="matrixLegendHead">
                  <strong>{axis.value}</strong>
                  <span>{axis.label}</span>
                </div>
              </div>
              <p>{meta.hint}</p>
              <span className="matrixLegendIndex">{String(index + 1).padStart(2, "0")}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
