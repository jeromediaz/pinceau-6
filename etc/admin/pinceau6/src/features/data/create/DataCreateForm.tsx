import {SelectInput, SimpleForm, TabbedForm, TextInput, useCreateContext, useDataProvider} from "react-admin";
import React, {useCallback, useEffect, useRef, useState} from "react";
import {ConcreteField} from "../types";
import {useQuery} from "@tanstack/react-query";
import SchemaInputModelFields from "../SchemaInputModelFields";
import {SchemaInputFields} from "../SchemaInputFields";

export const DataCreateForm = () => {
    const {resource} = useCreateContext();
    const [modelChoices, setModelChoices] = useState([]);
    const [fields, setFields] = useState<Array<ConcreteField>>([]);
    const [layout, setLayout] = useState("");
    const dataProvider = useDataProvider();
    const collection = resource.split("/")[2];
    const [modelName, setModelName] = useState(collection);

    const rootSchemaData = useRef();
    const modelSchemaData = useRef();

    const {data: schemaData} = useQuery({
        queryKey: ["data", "schema", modelName, 'create'],
        queryFn: () => dataProvider.collectionSchema(modelName, 'create'),
    });

    const onInputModelChange = (event) => {
        if (event.target.value) {
            console.log('onInputModelChange A', event.target.value)
            setModelName(event.target.value);
        } else {
            console.log('onInputModelChange B', collection)
            setModelName(collection);
        }
    };

    const validateModelCreation = (values: any) => {
        const errors = {};
        if (
            !values._meta || !values._meta.model ||
            (modelSchemaData.current && modelSchemaData.current.isAbstract)
        ) {
            errors["_meta.model"] = {'message': "abstract"};
        }

        return errors;
    };

    const onSchemaChanged = useCallback((schema) => {
        console.log('schema changed !')
        modelSchemaData.current = schema
    }, [])

    useEffect(() => {
        if (!schemaData) {
            return;
        }
        modelSchemaData.current = schemaData;
        setFields(schemaData.fields);
        setLayout(schemaData.layout);

        if (schemaData.name === collection) {
            rootSchemaData.current = schemaData;

            const models = [];
            if (!schemaData.isAbstract) {
                models.push({id: schemaData.name, name: schemaData.name});
            }
            if (schemaData.subModels) {
                const subModels = schemaData.subModels.map((value: string) => {
                    return {id: value, name: value};
                });
                models.push(...subModels);
            }
            setModelChoices(models);
            if (models.length == 1) {
                setModelName(models[0]["id"]);
            }
        }
    }, [schemaData, collection]);

    return (
        <>
            {layout == "simple" && (
                <SimpleForm validate={validateModelCreation}>
                    <SchemaInputModelFields model={modelName} allowModel onSchemaChanged={onSchemaChanged} schemaMode={"create"}/>
                </SimpleForm>
            )}
            {layout == "tabbed" && (
                <TabbedForm>
                    <TabbedForm.Tab label={fields[0].label} key={0}>
                        {modelChoices.length <= 1 && (
                            <TextInput
                                source="_meta.model"
                                defaultValue={modelName}
                                style={{display: "none"}}
                            />
                        )}
                        {modelChoices.length > 1 && (
                            <SelectInput
                                source="_meta.model"
                                choices={modelChoices}
                                onChange={onInputModelChange}
                            />
                        )}
                        <SchemaInputFields fields={fields[0].fields}/>
                    </TabbedForm.Tab>

                    {fields.slice(1).map((field, i) => {
                        return (
                            <TabbedForm.Tab label={field.label} key={i + 1}>
                                <SchemaInputFields fields={field.fields}/>
                            </TabbedForm.Tab>
                        );
                    })}
                </TabbedForm>
            )}
        </>
    );
};