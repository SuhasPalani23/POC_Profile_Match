import React from "react";

import palette from "../../../palette";
import Card from "./Card";

const MetricTile = ({ label, value, helper, accent = false }) => (
  <Card
    style={{
      background: accent
        ? "linear-gradient(130deg, rgba(201, 168, 76, 0.16), rgba(12, 12, 12, 1))"
        : palette.colors.background.secondary,
    }}
  >
    <p className="mono-label">{label}</p>
    <p
      style={{
        margin: `${palette.spacing.sm} 0 ${palette.spacing.xs} 0`,
        fontFamily: palette.typography.fontFamily.mono,
        fontSize: palette.typography.fontSize["4xl"],
        color: accent ? palette.colors.primary.cyan : palette.colors.text.primary,
      }}
    >
      {value}
    </p>
    <p style={{ color: palette.colors.text.secondary, fontSize: palette.typography.fontSize.sm }}>{helper}</p>
  </Card>
);

export default MetricTile;
