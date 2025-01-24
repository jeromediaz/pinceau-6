import {
    ArrayField,
    BooleanField,
    ChipField,
    Datagrid,
    DateField,
    Labeled,
    NumberField, RecordContextProvider,
    ReferenceArrayField,
    ReferenceField,
    SelectField, SimpleShowLayout,
    SingleFieldList,
    TextField,
    UrlField,
    useRecordContext,
    useTheme, WithListContext,
} from "react-admin";
import get from "lodash/get";
import {ChordDiagram} from "./ChordDiagram";
import React, {cloneElement, useState} from "react";
import {ConcreteField} from "./types";
import {Grid} from "@mui/material";
import {has} from "lodash";
import SchemaFieldModelFields from "./SchemaFieldModelFields";
import {DataMap} from "../dag/types";
import {AgChartsReact} from "ag-charts-react";
import {AspectRatio} from "../../aspect_ratio";
import Typography from "@mui/material/Typography";
import {Graphviz} from "graphviz-react";
import {Sankey} from "./Sankey";
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import TabContext from '@mui/lab/TabContext';
import Box from '@mui/material/Box';

type StringToLabelObjectProps = {
    children: React.ReactElement;
};


interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`vertical-tabpanel-${index}`}
            aria-labelledby={`vertical-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    <Typography>{children}</Typography>
                </Box>
            )}
        </div>
    );
}

export const StringToLabelObject: React.FC<StringToLabelObjectProps> = ({
                                                                            children,
                                                                            ...rest
                                                                        }) => {
    const record = useRecordContext();

    return cloneElement(children, {
        record: {label: record},
        ...rest,
    });
};

export type SchemaFieldOptionalProps = {
    label?: false | string;
    source?: string;
    sourcePrefix?: string;
    type: string;
};

const SchemaFieldOptional: React.FC<SchemaFieldOptionalProps> = ({
                                                                     source,
                                                                     type,
                                                                     ...other
                                                                 }) => {
    const workSource = other["sourcePrefix"]
        ? `${other["sourcePrefix"]}.${source}`
        : source || "";
    const workRecord = useRecordContext();
    const exist = has(workRecord, workSource);
    const value = get(workRecord, workSource);

    if (!exist || value == null) {
        return null;
    }

    return <SchemaField source={source} type={type} {...other} />;
};

export type SchemaFieldProps = {
    mode?: string;
    source?: string;
    type: string;
    record?: object;
    multiple?: boolean;
    sourcePrefix?: string;
    optional?: boolean;
    label?: string | false;
    fields?: ConcreteField[];
    reference?: string;
    schemaMode?: string;
};

const SchemaField: React.FC<SchemaFieldProps> = (props) => {
    const {
        mode,
        source,
        type,
        record,
        schemaMode = 'default',
        ...other
    } = props;
    const [theme] = useTheme();
    const workSource = other["sourcePrefix"]
        ? `${other["sourcePrefix"]}.${source}`
        : source || "";
    const workRecord = useRecordContext();
    const multiple = other["multiple"] || false;
    const label = "label" in other ? other["label"] : undefined;
    const render = "render" in other ? other["render"] : "";

    const [tabValue, setTabValue] = useState(0)

    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
        console.log({newValue})
        setTabValue(newValue);
    };

    const optional = other["optional"] || false;
    if (optional && type !== "bool") {
        const otherCopy = {...other, optional: false};
        return (
            <SchemaFieldOptional
                label={label}
                source={workSource}
                type={type}
                {...otherCopy}
            />
        );
    }

    if (type === "grid") {
        return (
            <>
                {!!label && (
                    <Typography variant="h6" gutterBottom>
                        {label}
                    </Typography>
                )}
                <Grid container>
                    {schemaFieldFunction(other["fields"] || [], "show", true, record, schemaMode)}
                </Grid>
            </>
        );
    }

    if (multiple && render == "chip") {
        const size = mode === "list" ? "small" : "medium";

        return (
            <ArrayField source={workSource}>
                <SingleFieldList linkType={false}>
                    <StringToLabelObject>
                        <ChipField source="label" size={size}/>
                    </StringToLabelObject>
                </SingleFieldList>
            </ArrayField>
        );
    }

    if (multiple && (type !== "group" && type !== "model" && type !== 'reference') && mode !== "list") {
        const {...singleOther} = other;
        delete singleOther["multiple"];

        const values = get(workRecord, source || workSource);

        if (!values) {
            return null;
        }

        if (values.length < 2) {
            return (
                <SchemaField source={source} type={type} {...singleOther} mode={mode} schemaMode={schemaMode}/>
            );
        }
        const range = Array(values.length)
            .fill(0)
            .map((_, i) => i);

        return (
            <>
                <ul>
                    {range.map((index) => {
                        const sourceKey = `${source}[${index}]`;
                        return (
                            <li key={sourceKey}>
                                <SchemaField
                                    schemaMode={schemaMode}
                                    source={sourceKey}
                                    type={type}
                                    {...singleOther}
                                    label={false}
                                    mode={mode}
                                />
                            </li>
                        );
                    })}
                </ul>
            </>
        );
    }

    if (type === "ag_chart") {
        const options = other["options"];

        const data = record ? get(record, source) : get(workRecord, source);

        options["data"] = data || [];
        options["theme"] = theme == "dark" ? "ag-default-dark" : "ag-default";

        //return null
        return (
            <AspectRatio
                priority="horizontal"
                ratio={{sm: 4 / 3, md: 16 / 9}}
                maxHeight={{sm: 300, md: 400}}
            >
                <AgChartsReact options={options}/>
            </AspectRatio>
        );
    } else if (type === "graphviz_dot") {
        const dotValue = record ? get(record, source) : get(workRecord, source);
        const options = other["options"];

        return <Graphviz dot={dotValue} options={options}/>;
    } else if (type === "sankey_diagram") {
        const matrixValue = record ? get(record, source) : get(workRecord, source);
        const options = other["options"];

        return <Sankey data={matrixValue} height={8000} width={800} {...options} />;

    } else if (type === "chord_diagram") {
        const matrixValue = record ? get(record, source) : get(workRecord, source);
        const options = other["options"];

        return <ChordDiagram data={matrixValue} height={800} width={800} {...options} />;

    } else if (type === "text") {
        if (render === "chip") {
            return <ChipField source={workSource} label={label}/>;
        }
        return <TextField record={record} source={workSource} label={label}/>;
    } else if (type === "url") {
        return <UrlField source={workSource}/>;
    } else if (type === "bool") {
        return <BooleanField record={record} source={workSource}/>;
    } else if (type === "int" || type === "float") {
        return <NumberField record={record} source={workSource}/>;
    } else if (type === "reference") {
        const renderOptions = {}
        const queryOptions = {}
        let chipSource = "_meta.label"

        for (const [option, value] of Object.entries(other)) {
            if (option.startsWith("render_")) {
                renderOptions[option.substring(7)] = value;
            }
        }
        let useChips = false
        if ('optionValue' in renderOptions) {
            queryOptions['meta'] = {'idField': renderOptions['optionValue']}
            chipSource = renderOptions['optionValue']
            useChips = true;
        }
        //<ChipField source={chipSource}/>
        if (useChips) {
            if (multiple) {
                return (<ArrayField source={workSource}>
                          <SingleFieldList linkType={false}>
                            <StringToLabelObject>
                              <ChipField source="label" size="small" />
                            </StringToLabelObject>
                          </SingleFieldList>
                        </ArrayField>)
            }

            return <ChipField source={workSource} />
        }

        if (multiple) {
            return (<ReferenceArrayField queryOptions={queryOptions} reference={other.reference} source={workSource}/>)
        }

        return <ReferenceField queryOptions={queryOptions} source={workSource} reference={other.reference}/>;
    } else if (type === "time") {
        return <DateField name={source} source={workSource} showTime={true}/>;
    } else if (type === "datetime") {
        return (
            <DateField
                name={source}
                source={workSource}
                showTime={true}
                showDate={true}
            />
        );
    } else if (type === "date") {
        return <DateField name={source} source={workSource} showDate={true}/>;
    } else if (type === "model") {

        if (multiple) {
            return (
                <ArrayField source={workSource}>
                    <Datagrid bulkActionButtons={false} rowClick={false}>
                        <SchemaFieldModelFields
                            sourcePrefix={other["sourcePrefix"]}
                            model={other["model"]}
                            schemaMode={schemaMode}
                        />
                    </Datagrid>
                </ArrayField>
            );
        }

        return (
            <SchemaFieldModelFields
                sourcePrefix={workSource}
                model={other["model"]}
                schemaMode={schemaMode}
            />
        );
    } else if (type === "group") {
        const fields = other["fields"];
        if (!fields) {
            return null;
        }

        const tabField = other['tabField']

        if (multiple) {
            if (tabField) {

                const values = get(workRecord, workSource)

                const tabs = values.map((localRecord, index) => {
                    const tabName = get(localRecord, tabField);
                    return <Tab label={tabName} key={index} value={index} />
                })

                return (
                    <Box sx={{ width: '100%', typography: 'body1' }}>

                        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                            <Tabs value={tabValue} onChange={handleChange} aria-label="">
                                {tabs}
                            </Tabs>
                        </Box>
                        <ArrayField source={workSource}>
                            <WithListContext render={({ data }) => {

                                return data.map((localRecord, index) => {
                                    return (
                                        <RecordContextProvider key={index} value={localRecord}>
                                            <TabPanel value={tabValue} index={index}>
                                                <SimpleShowLayout>
                                                    {schemaFieldFunction(fields, undefined, undefined, localRecord, schemaMode)}
                                                </SimpleShowLayout>
                                            </TabPanel>
                                        </RecordContextProvider>
                                    )
                                })


                            }} />
                        </ArrayField>

                    </Box>
                )
            }


            return (
                <ArrayField source={workSource}>
                    <Datagrid bulkActionButtons={false}>
                        {schemaFieldFunction(fields, undefined, undefined, undefined, schemaMode)}
                    </Datagrid>
                </ArrayField>
            );
        }

        const data = record ? get(record, source) : get(workRecord, source);

        return (
            <>
                {schemaFieldFunction(fields, undefined, undefined, data, schemaMode)}
            </>
        );
    } else if (type === "select") {
        const choices = other["choices"] || [];

        return <SelectField name={source} source={workSource} choices={choices}/>;
    }
};

export function schemaFieldFunction(
    fields: Array<ConcreteField>,
    mode = "show",
    wrap: boolean = false,
    record: DataMap | undefined = undefined,
    schemaMode: string = 'default'
) {
    if (wrap && !record) {
        return fields.map(({source, type, label, grid, ...other}) => (
            <Grid item {...grid} key={source}>
                <Labeled key={source} label={label}>
                    <SchemaField
                        key={source}
                        source={source}
                        type={type}
                        {...other}
                        mode={mode}
                        schemaMode={schemaMode}
                        record={undefined}
                    />
                </Labeled>
            </Grid>
        ));
    }
    if (wrap && record) {
        return fields.map(({source, type, label, grid, ...other}) => {
            return (
                <Grid item {...grid} key={source}>
                    <Labeled key={source} label={label}>
                        <SchemaField
                            key={source}
                            source={source}
                            type={type}
                            {...other}
                            mode={mode}
                            schemaMode={schemaMode}
                            record={record}
                        />
                    </Labeled>
                </Grid>
            );
        });
    }
    if (record) {
        return fields.map(({source, type, label, ...other}) => (
            <Labeled key={source} label={label}>
                <SchemaField
                    key={source}
                    source={source}
                    type={type}
                    {...other}
                    mode={mode}
                    schemaMode={schemaMode}
                    record={record}
                />
            </Labeled>
        ));
    }
    return fields.map(({source, type, label, ...other}) => (
        <SchemaField
            key={source}
            source={source}
            type={type}
            {...other}
            mode={mode}
            schemaMode={schemaMode}
            record={record}
        />
    ));
}

export {SchemaField};
