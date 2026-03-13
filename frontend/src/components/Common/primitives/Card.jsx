import React from "react";

import palette from "../../../palette";

const Card = ({ children, style = {}, className = "surface-card" }) => (
  <div
    className={className}
    style={{
      borderRadius: palette.borderRadius.lg,
      padding: palette.spacing.xl,
      backgroundColor: palette.colors.background.secondary,
      border: `1px solid ${palette.colors.border.primary}`,
      ...style,
    }}
  >
    {children}
  </div>
);

export default Card;
