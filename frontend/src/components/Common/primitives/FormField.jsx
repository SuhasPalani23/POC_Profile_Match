import React from "react";

import palette from "../../../palette";

const FormField = ({ label, children, hint }) => (
  <div>
    <label className="mono-label" style={{ display: "block", marginBottom: palette.spacing.sm }}>
      {label}
    </label>
    {children}
    {hint ? (
      <div style={{ marginTop: palette.spacing.sm, fontSize: palette.typography.fontSize.sm, color: palette.colors.text.tertiary }}>
        {hint}
      </div>
    ) : null}
  </div>
);

export default FormField;
