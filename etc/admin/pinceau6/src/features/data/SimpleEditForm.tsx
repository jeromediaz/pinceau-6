import React, {useMemo} from "react";
import {SimpleForm, Toolbar} from "react-admin";
import {SchemaInputFields} from "./SchemaInputFields";

type SimpleEditFormProps = {
    fields: Array<any>;
    readOnly?: boolean
    schemaMode?: string;
};

export const SimpleEditForm: React.FC<SimpleEditFormProps> = (props) => {
    const {fields, readOnly = false, schemaMode = 'default'} = props;

    const toolbar = useMemo(() => {
        return readOnly ? <></> : <Toolbar/>
    }, [readOnly])

    return (
        <SimpleForm toolbar={toolbar}>
            <SchemaInputFields fields={fields} schemaMode={schemaMode}/>
        </SimpleForm>
    );
};

export default SimpleEditForm
