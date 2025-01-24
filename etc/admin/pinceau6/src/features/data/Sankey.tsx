import {sankey, sankeyCenter, sankeyLinkHorizontal} from "d3-sankey";

const MARGIN_Y = 25;
const MARGIN_X = 5;

type Data = {
    nodes: { id: string }[];
    links: { source: string; target: string; value: number }[];
};

type SankeyProps = {
    width: number;
    height: number;
    data: Data;
};

const COLORS = [
    "#c62828",
    "#f44336",
    "#9c27b0",
    "#673ab7",
    "#3f51b5",
    "#2196f3",
    "#29b6f6",
    "#006064",
    "#009688",
    "#4caf50",
    "#8bc34a",
    "#ffeb3b",
    "#ff9800",
    "#795548",
    "#9e9e9e",
    "#607d8b"
]

const prefixes = [
    "astro-ph.",
    "cond-mat.",
    "cs.",
    "econ.",
    "eess.",
    "gr-",
    "hep-",
    "math",
    "nlin.",
    "nucl-",
    "physics.",
    "q-",
    "quant-",
    "stat."
]

export const Sankey = ({width, height, data}: SankeyProps) => {
    // Set the sankey diagram properties
    const sankeyGenerator = sankey() // TODO: find how to type the sankey() function
        .nodeWidth(26)
        .nodePadding(29)
        .nodeSort((nodeA, nodeB) => nodeA["id"].localeCompare(nodeB["id"]))
        .linkSort((linkA, linkB) => {
            return linkA["target"]["id"].localeCompare(linkB["target"]["id"]);
        })
        .extent([
            [MARGIN_X, MARGIN_Y],
            [width - MARGIN_X, height - MARGIN_Y],
        ])
        .nodeId((node) => node.id) // Accessor function: how to retrieve the id that defines each node. This id is then used for the source and target props of links
        .nodeAlign(sankeyCenter); // Algorithm used to decide node position

    // Compute nodes and links positions
    const {nodes, links} = sankeyGenerator(data);

    //
    // Draw the nodes
    //
    const labelToColor = {}

    const allNodes = nodes.map((node, index) => {
        const label = node.id.substring(2);

        var color;
        if (label in labelToColor) {
            color = labelToColor[label]
        } else {
            const color_index = prefixes.findIndex((value) => label.startsWith(value))

            color = color_index != -1 ? COLORS[color_index] : "#a53253"

            labelToColor[label] = color
        }

        return (
            <g key={node.index}>
                <rect
                    height={node.y1 - node.y0}
                    width={sankeyGenerator.nodeWidth()}
                    x={node.x0}
                    y={node.y0}
                    stroke={"black"}
                    fill={color}
                    fillOpacity={0.8}
                    rx={0.9}
                />
            </g>
        );
    });

    //
    // Draw the links
    //
    const allLinks = links.map((link, i) => {
        const linkGenerator = sankeyLinkHorizontal();
        const path = linkGenerator(link);

        const source_label = link.source.id.substring(2);
        const target_label = link.target.id.substring(2);
        const source_color = labelToColor[source_label];
        const target_color = labelToColor[target_label];
        const strokeOpacity = source_color == target_color ? 0.1 : 0.2;

        console.log({source_color, target_color, strokeOpacity})

        return (
            <path
                key={i}
                d={path}
                stroke={source_color}
                fill="none"
                strokeOpacity={strokeOpacity}
                strokeWidth={link.width}
            />
        );
    });

    const labelCount = nodes.length / 2;
    const allLabels = nodes.filter((val, index) => index < labelCount).map((node, index) => {
        const label = data["nodes"][index]["id"].substring(2)
        return (
            <g key={`label_${node.index}`}>
                <text x={node.x1 + sankeyGenerator.nodeWidth()}
                      y={((node.y1 + node.y0) / 2)}
                      dominantBaseline={"middle"}>{label}</text>
            </g>
        );
    });

    return (
        <div>
            <svg width={width} height={height}>
                {allNodes}
                {allLinks}
                {allLabels}
            </svg>
        </div>
    );
};