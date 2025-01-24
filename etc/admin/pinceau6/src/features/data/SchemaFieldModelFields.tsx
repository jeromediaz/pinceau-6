import React, {useEffect, useMemo, useState} from "react";
import {Labeled, SimpleShowLayout, TextField, useDataProvider, useRecordContext,} from "react-admin";
import {useQuery} from "@tanstack/react-query";
import {SchemaField} from "./SchemaField";
import get from "lodash/get";
import {ConcreteField} from "./types";

type SchemaInputModelFieldsProps = {
    sourcePrefix?: string;
    source: string;
    model: string;
    allowModel: boolean;
    schemaMode?: string;
};

export const SchemaFieldModelFields: React.FC<SchemaInputModelFieldsProps> = (props) => {
    const {sourcePrefix, schemaMode="default"} = props;
    const [fields, setFields] = useState<ConcreteField[]>([]);
    const dataProvider = useDataProvider();

    const modelFieldName = useMemo(() => {
        if (!sourcePrefix) {
            return "_meta.model";
        }
        return `${sourcePrefix}._meta.model`;
    }, [sourcePrefix]);

    const record = useRecordContext();
    const recordModelValue = get(record, modelFieldName);

    console.log('SchemaFieldModelFields', {modelFieldName, sourcePrefix, record});

    const {data: schemaData} = useQuery({
        queryKey: ["data", "schema", recordModelValue, schemaMode],
        queryFn: () => dataProvider.collectionSchema(recordModelValue, schemaMode),
        enabled: !!recordModelValue,
    });

    useEffect(() => {
        if (!schemaData) {
            return;
        }

        setFields(schemaData.fields);
    }, [schemaData]);

    return (
        <SimpleShowLayout>
            <TextField source={"_meta.model"}/>
            {fields.map(({source, type, ...other}) => {
                return (
                    <Labeled key={source}>
                        <SchemaField
                            sourcePrefix={sourcePrefix}
                            source={source}
                            type={type}
                            schemaMode={schemaMode}
                            {...other}
                            mode="show"
                        />
                    </Labeled>
                );
            })}
        </SimpleShowLayout>
    );
};

export default SchemaFieldModelFields;
