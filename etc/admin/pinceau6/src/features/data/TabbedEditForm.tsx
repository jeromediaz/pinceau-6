import React, {useMemo} from "react";
import {TabbedForm, Toolbar} from "react-admin";
import {WrapInGridContainer} from "./SchemaInput";
import {SchemaInputFields} from "./SchemaInputFields";


type TabbedEditFormProps = {
    fields: Array<any>;
    readOnly?: boolean
    schemaMode?: string;
};
const TabbedEditForm: React.FC<TabbedEditFormProps> = (props) => {
    const {fields, readOnly = false, schemaMode = 'default'} = props;

    const toolbar = useMemo(() => {
        return readOnly ? <></> : <Toolbar/>
    }, [readOnly])

    return (
        <TabbedForm toolbar={toolbar}>
            {fields.map((field, i) => {
                return (
                    <TabbedForm.Tab label={field.label} key={i}>
                        <WrapInGridContainer wrap={!!field["grid"]}>
                            <SchemaInputFields fields={field.fields} schemaMode={schemaMode}/>
                        </WrapInGridContainer>
                    </TabbedForm.Tab>
                );
            })}
        </TabbedForm>
    );
};

export default TabbedEditForm
