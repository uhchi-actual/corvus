import type { HealthAxis } from "../../types/dashboard";

type Props = {
  axes: HealthAxis[];
  score: string;
};

const SIZE = 360;
const CENTER = SIZE / 2;
const RADIUS = 128;

function polarPoint(index: number, count: number, value: number) {
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
  const distance = (value / 100) * RADIUS;
  return {
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

  const labelPoints = axes.map((axis, index) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
    const labelRadius = RADIUS + 34;
    return {
      axis,
      x: CENTER + Math.cos(angle) * labelRadius,
      y: CENTER + Math.sin(angle) * labelRadius,
    };
  });

  return (
    <div className="healthMatrixWrap">
      <svg
        className="healthMatrixChart"
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={`Performance profile for drive score ${score}`}
      >
        <defs>
          <linearGradient id="performancePolygonGradient" x1="0" y1="0" x2="0" y2={SIZE} gradientUnits="userSpaceOnUse">
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
        {axes.map((_, index) => {
          const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
          const x = CENTER + Math.cos(angle) * RADIUS;
          const y = CENTER + Math.sin(angle) * RADIUS;
          return (
            <line
              key={`axis-${index}`}
              className="healthMatrixAxis"
              x1={CENTER}
              y1={CENTER}
              x2={x}
              y2={y}
            />
          );
        })}
        <polygon className="healthMatrixRef" points={referencePoints} />
        <polygon className="healthMatrixShape" points={dataPoints} />
        {labelPoints.map(({ axis, x, y }) => (
          <text
            key={axis.id}
            className="healthMatrixLabel"
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {axis.label}
          </text>
        ))}
        {labelPoints.map(({ axis, x, y }) => {
          const angle = Math.atan2(y - CENTER, x - CENTER);
          const valueRadius = RADIUS + 18;
          const valueX = CENTER + Math.cos(angle) * valueRadius;
          const valueY = CENTER + Math.sin(angle) * valueRadius;
          return (
            <text
              key={`${axis.id}-value`}
              className="healthMatrixValue"
              x={valueX}
              y={valueY}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {axis.value}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
