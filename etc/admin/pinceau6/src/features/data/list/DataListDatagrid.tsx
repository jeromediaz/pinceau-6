import React, {useEffect, useState} from "react";
import {CloneButton, Datagrid, EditButton, ShowButton, useDataProvider, useListContext} from "react-admin";
import {useQuery} from "@tanstack/react-query";
import {schemaFieldFunction} from "../SchemaField";
import {PageButton} from "../PageButton";
import ChatIcon from "@mui/icons-material/Chat";

type DataListDatagridProps = {
    schema?: string
}

export const DataListDatagrid: React.FC<DataListDatagridProps> = (props) => {
    const {schema} = props;
    const {resource} = useListContext();
    const [fields, setFields] = useState([]);
    const dataProvider = useDataProvider();
    const collection = schema ? schema : resource.split("/")[2];
    
    const {data} = useQuery({
        queryKey: ["data", "schema", collection, 'list'],
        queryFn: () => dataProvider.collectionSchema(collection, "list"),
    });

    useEffect(() => {
        if (data) {
            let listFields = data.fields.filter((field) => {
                if (!("hideOn" in field)) {
                    return true;
                }
                if (field["hideOn"].indexOf("list") != -1) {
                    return false;
                }
            });

            const layout = data.layout;

            if (layout == "tabbed") {
                listFields = listFields[0]["fields"];
            }

            setFields(listFields);
        }
    }, [data]);

    if (!fields) {
        return null;
    }

    return (
        <Datagrid>
            {schemaFieldFunction(fields, "list", false, undefined, 'list')}
            <>
                <EditButton/>
                <ShowButton/>
                <CloneButton/>
                {(collection == "chat" || collection == "chat_from_wrapped_dag") && (
                    <PageButton
                        label="Chat Room"
                        pathHandler={(record) => `/chat/${record.id}`}
                        icon={<ChatIcon/>}
                    />
                )}
            </>
        </Datagrid>
    );
};
