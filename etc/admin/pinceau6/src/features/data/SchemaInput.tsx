import {
    ArrayInput,
    AutocompleteArrayInput,
    AutocompleteInput,
    BooleanInput,
    DateInput,
    DateTimeInput,
    FieldTitle,
    FormDataConsumer,
    NullableBooleanInput,
    NumberInput,
    PasswordInput,
    RecordContextProvider,
    ReferenceArrayInput,
    ReferenceInput,
    required,
    SelectArrayInput,
    SelectInput,
    SimpleFormIterator,
    SourceContextProvider,
    TextInput,
    TimeInput,
    useRecordContext,
    useSourceContext,
    useTranslateLabel,
} from "react-admin";
import Stack from "@mui/material/Stack";
import React, {Fragment, ReactNode, useMemo, useState} from "react";
import Typography from "@mui/material/Typography";
import Switch from "@mui/material/Switch";
import {Grid} from "@mui/material";
import FormControlLabel from "@mui/material/FormControlLabel";
import {useProcessValidation} from "./conditions";
import {SchemaInputFields} from "./SchemaInputFields";
import SchemaInputModelFields from "./SchemaInputModelFields";
import {has, unset} from "lodash";
import {FieldOpts, NamedSubField, SourceType} from "./types";
import {Graphviz} from "graphviz-react";
import get from "lodash/get";
import {ErrorBoundary} from "react-error-boundary";
import {SourceContextValue} from "ra-core";

type WrapInGridContainerProps = {
    wrap: boolean;
    children?: React.ReactNode;
};

const Fallback = ({error, resetErrorBoundary}) => {
    // Call resetErrorBoundary() to reset the error boundary and retry the render.
    return (
        <div role="alert">
            <pre style={{color: "red"}}>{error}</pre>
        </div>
    );
};

const WrapInGridContainer: React.FC<WrapInGridContainerProps> = ({
                                                                     wrap,
                                                                     children,
                                                                 }) => {
    if (!wrap) {
        return children;
    }

    return <Grid container>{children}</Grid>;
};

type SchemaInputOptionalProps = {
    label?: string;
    source?: string;
    sourcePrefix?: string;
    type: string;
    helperText?: string;
    hideName?: boolean;

};

type AccessSubContextProps = {
    source: string,
    children: ReactNode
}

const AccessSubContext: React.FC<AccessSubContextProps> = ({source: subSource, children, ...rest}) => {
    const parentSourceContext = useSourceContext();

    const sourceContext = React.useMemo<SourceContextValue>(
        () => ({
            // source is the source of the ArrayInput child
            getSource: (source: string) => {
                if (!source) {
                    // SimpleFormIterator calls getSource('') to get the arraySource
                    return parentSourceContext.getSource(subSource);
                }

                return parentSourceContext.getSource(
                    `${subSource}.${source}`
                );
            },
            // if Array source is items, and child source is name, .0.name => resources.orders.fields.items.name
            getLabel: (source: string) =>
                parentSourceContext.getLabel(`${subSource}.${source}`),
        }),
        [parentSourceContext, subSource]
    );

    const parentRecord = useRecordContext()
    const record = get(parentRecord, subSource)


    return (
        <SourceContextProvider value={sourceContext}>
            <RecordContextProvider value={record}>
                {children}
            </RecordContextProvider>
        </SourceContextProvider>
    )
}


const SchemaInputOptional: React.FC<SchemaInputOptionalProps> = ({
                                                                     label,
                                                                     source,
                                                                     type,
                                                                     ...other
                                                                 }) => {
    const workSource = other["sourcePrefix"]
        ? `${other["sourcePrefix"]}.${source}`
        : source || "";
    const workRecord = useRecordContext();

    const exist = has(workRecord, source);
    const isNonNull = get(workRecord, source) !== null;
    const [display, setDisplay] = useState<boolean>(exist && isNonNull);

    const handleSwitchChange = () => {
        if (display) {
            // we will hide
            unset(workRecord, workSource);
            setDisplay(false);
        } else {
            setDisplay(true);
        }
    };

    return (
        <Stack pl={2}>
            <FormControlLabel
                control={<Switch checked={display} onChange={handleSwitchChange}/>}
                label={label}
                labelPlacement="start"
            />

            {display && <SchemaInput source={source} type={type} {...other} />}
        </Stack>
    );
};

type Validations = {
    gt?: number | string | object;
    ge?: number | string | object;
    lt?: number | string | object;
    le?: number | string | object;
    maxLength?: number;
    minLength?: number;
};

type SchemaInputNumberProps = {
    step?: number
    min?: number
    max?: number
}

type SchemaInputProps = {
    source?: string;
    sourcePrefix?: string;
    type: SourceType;
    optional?: boolean;
    multiple?: boolean;
    condition?: any;
    label?: string;
    defaultValue?: any;
    opts?: Array<string>;
    choices?: Array<any>;
    fields?: Array<any>;
    model?: string;
    helperText?: string;
    hideName?: boolean;
    validations?: Validations;
    number?: SchemaInputNumberProps;
    schemaMode?: string;
};

const SchemaInput: React.FC<SchemaInputProps> = (props) => {
    const {
        source,
        type,
        hideName,
        validations,
        schemaMode = 'default',
        ...other
    } = props;
    const workSource = other["sourcePrefix"]
        ? `${other["sourcePrefix"]}.${source}`
        : source || "";

    const parentSource = workSource.split(".").slice(0, -1).join(".");
    const translateLabel = useTranslateLabel();

    const multiple = other["multiple"] || false;
    const optional = other["optional"] || false;

    const fieldValidate = useMemo(() => {
        const validateArray = [];

        if (type == "text" || type == "secretstr") {
            if (!validations || !validations.minLength || validations.minLength > 0) {
                validateArray.push(required());
            }
        }
        if (validations === undefined) {
            return validateArray;
        }

        const validationFunction = (value, allFields) => {
            const errors = [];
            if (validations.ge !== undefined && value < validations.ge) {
                errors.push(`${value} should be ≥ to ${validations.ge}`);
            }
            if (validations.gt !== undefined && value <= validations.gt) {
                errors.push(`${value} should be > to ${validations.gt}`);
            }

            if (validations.le !== undefined && value > validations.le) {
                errors.push(`${value} should be ≤ to ${validations.le}`);
            }
            if (validations.lt !== undefined && value >= validations.lt) {
                errors.push(`${value} should be < to ${validations.lt}`);
            }

            if (
                validations.minLength !== undefined &&
                value.length < validations.minLength
            ) {
                errors.push(
                    `'${value}' length should be ≥ to ${validations.minLength}`,
                );
            }
            if (
                validations.maxLength !== undefined &&
                value.length < validations.maxLength
            ) {
                errors.push(
                    `'${value}' length should be ≤ to ${validations.maxLength}`,
                );
            }

            if (errors.length > 0) {
                return errors.join(", ");
            }

            return undefined;
        };

        validateArray.push(validationFunction);
        return validateArray;
    }, [type, validations]);

    if (!useProcessValidation(parentSource, other["condition"]) || !type) {
        return null;
    }
    const label = translateLabel({label: other["label"], source}) as string;

    if (optional && type !== "bool") {
        const otherCopy = {...other, optional: false};
        return (
            <SchemaInputOptional
                label={label}
                source={source}
                type={type}
                {...otherCopy}
            />
        );
    }

    const opts = (("opts" in other ? other["opts"] : []) || []) as Array<string>;

    const otherProps: NamedSubField = {
        label,
        name: !hideName ? workSource : "",
    };

    if ("helperText" in other) {
        otherProps["helperText"] = other["helperText"];
    }
    if ("defaultValue" in other) {
        otherProps["defaultValue"] = other["defaultValue"];
    }
    if (opts.indexOf("fullWidth") !== -1) {
        otherProps["fullWidth"] = true;
    }
    if (opts.indexOf("readOnly") !== -1) {
        otherProps["readOnly"] = true;
    }
    if (opts.indexOf("disabled") !== -1) {
        otherProps["disabled"] = true;
    }

    if (multiple && type == "select") {
        const choices = other["choices"] || [];
        return (
            <SelectArrayInput
                source={workSource}
                name={source}
                choices={choices}
                {...otherProps}
            />
        );
    }

    if (multiple && (type !== "group" && type !== "model" && type !== 'reference')) {
        const {...singleOther} = other;
        delete singleOther["multiple"];
        delete singleOther["sourcePrefix"]

        return (
            <ArrayInput source={source} name={source}>
                <SimpleFormIterator inline fullWidth>
                    <SchemaInput type={type} {...singleOther} />
                </SimpleFormIterator>
            </ArrayInput>
        );
    }

    if (type === "text") {
        if (opts.indexOf("multiline") !== -1) {
            otherProps["multiline"] = true;
        }
    }
    if (["url", "email"].indexOf(type) !== -1) {
        otherProps["type"] = type;
    }

    if (["int", "float"].indexOf(type) !== -1) {
        const numberProps = other["number"] || {};

        if (type === "int") {
            otherProps["step"] = 1;
        } else if ("step" in numberProps) {
            otherProps["step"] = numberProps["step"];
        }

        if ("min" in numberProps) {
            otherProps["min"] = numberProps["min"];
        }
        if ("max" in numberProps) {
            otherProps["max"] = numberProps["max"];
        }
    }

    if (type === "graphviz_dot") {
        const options = other["options"];

        return (
            <FormDataConsumer>
                {({formData, ...rest}) => {
                    const dotValue = get(formData, source);

                    if (!dotValue) {
                        return null;
                    }
                    return (
                        <ErrorBoundary FallbackComponent={Fallback} key={dotValue}>
                            <Graphviz dot={dotValue} options={options}/>
                        </ErrorBoundary>
                    );
                }}
            </FormDataConsumer>
        );
    } else if (["url", "text", "email"].indexOf(type) != -1) {
        if (optional) {
            return (
                <Stack pl={2}>
                    <Typography>
                        <FieldTitle source={source}/>
                    </Typography>

                    <TextInput
                        source={workSource}
                        {...otherProps}
                        validate={fieldValidate}
                    />
                </Stack>
            );
        }
        return (
            <TextInput source={workSource} {...otherProps} validate={fieldValidate}/>
        );
    } else if (type === "secretstr") {
        return <PasswordInput source={workSource} {...otherProps} />;
    } else if (type === "bool") {
        if (optional) {
            return <NullableBooleanInput source={workSource} {...otherProps}/>;
        }
        return <BooleanInput source={workSource} {...otherProps}/>;
    } else if (type === "float" || type === "int") {
        return (
            <NumberInput
                source={workSource}
                {...otherProps}
                validate={fieldValidate}
            />
        );
    } else if (type === "reference") {

        const renderOptions = {}
        const queryOptions = {}

        for (const [option, value] of Object.entries(other)) {
            if (option.startsWith("render_")) {
                renderOptions[option.substring(7)] = value;
            }
        }

        if ('optionValue' in renderOptions) {
            queryOptions['meta'] = {'idField': renderOptions['optionValue']}
        }

        if ("filter" in other) {
            otherProps["filter"] = other["filter"];
        }

        if (multiple) {

            return <ReferenceArrayInput
                queryOptions={queryOptions}
                source={source}
                reference={other.reference}
                {...otherProps}
            >
                <AutocompleteArrayInput {...renderOptions}/>
            </ReferenceArrayInput>;
        }

        return (
            <ReferenceInput
                queryOptions={queryOptions}
                source={source}
                reference={other.reference}
                {...otherProps}
            >
                <AutocompleteInput {...renderOptions} />
            </ReferenceInput>
        );
    } else if (type === "time") {
        return (
            <TimeInput source={workSource} {...otherProps} validate={fieldValidate}/>
        );
    } else if (type === "datetime") {
        return (
            <DateTimeInput
                source={workSource}
                {...otherProps}
                validate={fieldValidate}
            />
        );
    } else if (type === "date") {
        return (
            <DateInput source={workSource} {...otherProps} validate={fieldValidate}/>
        );
    } else if (type === "model") {
        if (multiple) {
            return (
                <ArrayInput source={workSource}>
                    <SimpleFormIterator fullWidth>
                        <SchemaInputModelFields
                            sourcePrefix={other["sourcePrefix"]}
                            model={other["model"]}
                            allowModel
                            hideName
                            schemaMode={schemaMode}
                        />
                    </SimpleFormIterator>
                </ArrayInput>
            );
        }
        return (
            <SchemaInputModelFields
                sourcePrefix={workSource}
                model={other["model"]}
                allowModel
                schemaMode={schemaMode}
                {...otherProps}
            />
        );
    } else if (type === "group") {
        const fields = other["fields"];
        const inline = opts.indexOf(FieldOpts.inline) !== -1;
        const grid = opts.indexOf(FieldOpts.grid) !== -1;
        if (!fields) {
            return null;
        }

        if (multiple) {
            if (grid) {
                return (
                    <ArrayInput source={workSource}>
                        <SimpleFormIterator inline={inline} fullWidth>
                            <FormDataConsumer>
                                {({
                                      formData, // The whole form data
                                      scopedFormData, // The data for this item of the ArrayInput
                                      ...rest
                                  }) => {
                                      return (
                                          <Fragment>
                                              <Grid container spacing={2}>
                                                  {fields.map((value: object) => {
                                                      const {source, type, grid, ...others} = value;
                                                      return (
                                                          <Grid item {...grid} key={source}>
                                                              <SchemaInput
                                                                  source={source}
                                                                  type={type}
                                                                  {...others}
                                                                  hideName
                                                              />
                                                          </Grid>
                                                      );
                                                  })}
                                              </Grid>
                                          </Fragment>
                                      );
                                }}
                            </FormDataConsumer>
                        </SimpleFormIterator>
                    </ArrayInput>
                );
            }


            return (
                <ArrayInput source={workSource} {...otherProps}>
                    <SimpleFormIterator inline={inline} fullWidth>
                        {fields.map((value: object) => {
                            const {source, type, grid, ...others} = value;
                            return (
                                <SchemaInput
                                    key={source}
                                    source={source}
                                    type={type}
                                    {...others}
                                    hideName
                                />
                            );
                        })}

                    </SimpleFormIterator>
                </ArrayInput>
            );
        }

        return (
            <Stack pl={2} sx={{width: '100%'}}>
                <Typography sx={{mb: 1}}>
                    <FieldTitle source={source}/>
                </Typography>
                <Stack sx={{pl: 2}}>
                    <SchemaInputFields sourcePrefix={workSource} fields={fields} schemaMode={schemaMode}/>
                </Stack>
            </Stack>
        );
    } else if (type === "select") {
        const choices = other["choices"] || [];
        return (
            <SelectInput source={workSource} choices={choices} {...otherProps} />
        );
    }
};

export default SchemaInput;
export {WrapInGridContainer};
