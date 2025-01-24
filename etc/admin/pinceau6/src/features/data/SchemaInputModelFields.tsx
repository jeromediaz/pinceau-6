import React, {useCallback, useEffect, useMemo, useRef, useState,} from "react";
import SchemaInput from "./SchemaInput";
import {SelectInput, TextInput, useDataProvider} from "react-admin";
import {useQuery} from "@tanstack/react-query";
import {useWatch} from "react-hook-form";

type SchemaInputModelFieldsProps = {
    sourcePrefix?: string;
    source?: string;
    model: string;
    allowModel?: boolean;
    onSchemaChanged?: (schema: any) => void
    hideName?: boolean;
    schemaMode?: string;
};


export const SchemaInputModelFields: React.FC<SchemaInputModelFieldsProps> = (props) => {
    const {
        sourcePrefix,
        model,
        allowModel = false,
        onSchemaChanged,
        hideName,
        schemaMode = 'default'
    } = props
    const [modelChoices, setModelChoices] = useState([]);
    const [fields, setFields] = useState([]);
    const dataProvider = useDataProvider();
    const [modelName, setModelName] = useState(model);

    const rootSchemaData = useRef();
    const modelSchemaData = useRef();

    const modelFieldName = useMemo(() => {
        if (!sourcePrefix) {
            return "_meta.model";
        }
        return `${sourcePrefix}._meta.model`;
    }, [sourcePrefix]);

    const recordModelValue = useWatch<string>({name: modelFieldName});

    const onInputModelChange = useCallback(
        (event) => {
            if (event.target.value) {
                setModelName(event.target.value);
            } else {
                setModelName(model);
            }
        },
        [model],
    );

    const {data: schemaData} = useQuery({
        queryKey: ["data", "schema", modelName, schemaMode],
        queryFn: () => dataProvider.collectionSchema(modelName, schemaMode),
        enabled: true,
    });

    useEffect(() => {
        if (!schemaData) {
            return;
        }

        modelSchemaData.current = schemaData;
        if (onSchemaChanged) {
            onSchemaChanged(schemaData);
        }
        setFields(schemaData.fields);

        if (schemaData.name == model) {
            rootSchemaData.current = schemaData;

            const models = [];
            const availableModels = [];
            if (!schemaData.isAbstract) {
                availableModels.push(schemaData.name);
                models.push({id: schemaData.name, name: schemaData.name});
            }

            if (schemaData.subModels) {
                availableModels.push(...schemaData.subModels);
                const subModels = schemaData.subModels.map((value: string) => {
                    return {id: value, name: value};
                });
                models.push(...subModels);
            }
            setModelChoices(models);

            if (availableModels.indexOf(recordModelValue) !== -1) {
                setModelName(recordModelValue);
            } else if (models.length == 1) {
                setModelName(models[0]["id"]);
            }
        }
    }, [onSchemaChanged, sourcePrefix, schemaData, model, recordModelValue]);

    return (
        <>
            {allowModel && modelChoices.length <= 1 && (
                <TextInput
                    source={modelFieldName}
                    defaultValue={modelName}
                    style={{display: "none"}}
                />
            )}
            {allowModel && modelChoices.length > 1 && (
                <SelectInput
                    source={modelFieldName}
                    choices={modelChoices}
                    onChange={onInputModelChange}
                />
            )}
            {fields.map((value: object) => {
                const {source, type, ...others} = value;
                return (
                    <SchemaInput
                        key={source}
                        sourcePrefix={sourcePrefix}
                        source={source}
                        type={type}
                        hideName={hideName}
                        schemaMode={schemaMode}
                        {...others}
                    />
                );
            })}
        </>
    );
};

export default SchemaInputModelFields;
