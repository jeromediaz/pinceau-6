// in src/NotFound.js
import React, {useContext, useEffect, useMemo, useState} from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import { Title, useDataProvider } from "react-admin";
import { useTheme } from "@mui/material/styles";
import { dagColors } from "./styles/colors";
import { useTheme as useThemeName } from "react-admin";
import { Graphviz } from "graphviz-react";
import {ApplicationFilter} from "./App";

type ModelType = [string, string, boolean, string?, object];

const SchemaPage = () => {
  const [models, setModels] = useState<ModelType[]>([]);
  const theme = useTheme();
  const [themeName] = useThemeName();
  const dataProvider = useDataProvider();

  const [taxonomyFilter, setTaxonomyFilter] = useContext(ApplicationFilter)

  useEffect(() => {
    //if (authenticated) {
    dataProvider.models(taxonomyFilter).then(setModels);
    //}
  }, [taxonomyFilter, dataProvider]);

  const colors = useMemo(() => {
    return dagColors[themeName];
  }, [themeName]);

  const dotContent = useMemo(() => {
    const lines = [];

    lines.push(`digraph models {`);
    lines.push(`bgcolor="${colors.bgColor}"`);
    lines.push('rankdir="RL"');
    lines.push(`node [shape=box;color="${colors.strokeColor}";style=solid]`);
    lines.push(`edge [color="${colors.strokeColor}";fontcolor="${colors.strokeColor}"]`);

    models.forEach((model) => {
      const [id, name, isAbstract, parent, composition] = model;

      const color = isAbstract
        ? theme.palette.secondary.main
        : theme.palette.primary.main;

      lines.push(`"${id}" [label=<${name}>;fontcolor="${color}"]`);

      if (parent) {
        lines.push(`"${id}" -> "${parent}"`);
      }

      for (const [source, target] of Object.entries(composition)) {
        lines.push(`"${target}" -> "${id}" [label="${source}";arrowhead=diamond;arrowtail=vee]`);
      }
    });

    lines.push("}");

    return lines.join("\n");
  }, [models, theme, colors]);

  return (
    <Card>
      <Title title="Dashboard" />
      <CardContent>
        <h1>Models</h1>

        <Graphviz
          dot={dotContent}
          options={{
            fit: true,
            height: null,
            width: "100%",
            zoom: false,
          }}
        />
      </CardContent>
    </Card>
  );
};

export default SchemaPage;
