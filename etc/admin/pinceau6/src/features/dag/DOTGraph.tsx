import React from "react";
import { StatusMap } from "./types";
import { useCallback, useEffect, useMemo } from "react";
import { Graphviz } from "graphviz-react";
import { useTheme } from "react-admin";
import { dagColors } from "../../styles/colors";

type Task = {
  label: string;
};

type NodeMap = {
  [key: string]: Task;
};

type Edge = [string, string, string];

type GraphData = {
  nodes: NodeMap;
  edges: Edge[];
};

type DOTGraphProps = {
  graphData: GraphData;
  statuses: StatusMap;
  updateRef: any;
  rankDir?: 'TB' | 'LR';
  fontSize?: number
};

export const DOTGraph: React.FC<DOTGraphProps> = ({
  graphData,
  statuses,
  updateRef,
  rankDir='LR',
  fontSize
}) => {
  const [theme] = useTheme();
  const [dotValue, setDotValue] = React.useState<string>("");

  const colors = useMemo(() => {
    return dagColors[theme];
  }, [theme]);

  const updateDotContent = useCallback(() => {
    const lines = [];
    lines.push("digraph {");
    lines.push(`bgcolor="${colors.bgColor}"`);
    lines.push(`rankdir="${rankDir}"`);
    if (fontSize) {
      lines.push(`fontsize="${fontSize}pt"`);
    }
    lines.push(`node [shape=box;color="${colors.strokeColor}";style=solid]`);
    lines.push(`edge [color="${colors.strokeColor}"]`);
    if (graphData) {
      for (const [key, value] of Object.entries(graphData.nodes)) {
        const status = statuses[key];
        //const className = status ? `class="task-status-${(status).toLowerCase()}"` : ''
        const fontColor = status
          ? colors.status[status.toLowerCase()]
          : colors.status["default"];
        const fontColorAttribute = ` fontcolor="${fontColor}"`;
        const subLabel = status
          ? `<br/><FONT POINT-SIZE="10">${status}</FONT>`
          : "";

        lines.push(
          `"${key}" [label=<${value.label}${subLabel}>;${fontColorAttribute}]`,
        );
      }

      graphData.edges.forEach((edge) => {
        let attributes = "";
        const edgeType = edge[2];
        const toNodeStatus = statuses[edge[1]];
        if (edgeType == "CONDITIONAL") {
          const style =
            toNodeStatus && toNodeStatus != "IDLE" ? "bold" : "dotted";
          attributes = ` [samehead=conditional;arrowtail=odot;style=${style}]`;
        } else if (edgeType == "LOOP") {
          //const style == (toNodeStatus && toNodeStatus != 'IDLE') ? 'bold' : 'dashed';
          attributes = " [samehead=loop;style=dashed]";
        } else if (edgeType == "LOOP_START") {
          const style =
            toNodeStatus && toNodeStatus != "IDLE" ? "bold" : "solid";
          attributes = ` [samehead=start;arrowtail=odiamond;style=${style}]`;
        } else if (edgeType == "LOOP_END") {
          const style =
            toNodeStatus && toNodeStatus != "IDLE" ? "bold" : "solid";
          attributes = ` [samehead=end;arrowtail=diamond;style=${style}]`;
        }

        lines.push(`"${edge[0]}" -> "${edge[1]}"${attributes}`);
      });
    }

    lines.push("}");

    const dotContent = lines.join("\n");

    setDotValue(dotContent);
  }, [fontSize, rankDir, colors, graphData, statuses]);

  useEffect(() => {
    updateRef.current = updateDotContent;
    return () => {
      updateRef.current = null;
    };
  });

  useEffect(() => {
    updateDotContent();
  }, [updateDotContent, colors]);

  if (!dotValue) {
    return null;
  }

  return (
    <Graphviz
      dot={dotValue}
      options={{
        fit: true,
        height: null,
        width: "100%",
        zoom: false,
      }}
    />
  );
};
