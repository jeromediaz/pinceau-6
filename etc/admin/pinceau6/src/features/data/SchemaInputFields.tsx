import React from "react";
import SchemaInput from "./SchemaInput";
import { Grid } from "@mui/material";
import { ConcreteField } from "./types";

type SchemaInputFieldsProp = {
  sourcePrefix?: string;
  fields: Array<ConcreteField>;
  schemaMode: string;
};

export const SchemaInputFields: React.FC<SchemaInputFieldsProp> = (props) => {
  const {
    sourcePrefix,
    fields,
    schemaMode = "default",
  } = props;
  return (
    <>
      {fields.map((value: ConcreteField) => {
        const { source, type, grid, ...others } = value;

        if (grid && typeof grid === "object") {
          return (
            <Grid item {...grid} key={source}>
              <SchemaInput
                sourcePrefix={sourcePrefix}
                source={source}
                type={type}
                schemaMode={schemaMode}
                {...others}
              />
            </Grid>
          );
        }

        return (
          <SchemaInput
            key={source}
            sourcePrefix={sourcePrefix}
            source={source}
            type={type}
            schemaMode={schemaMode}
            {...others}
          />
        );
      })}
    </>
  );
};
