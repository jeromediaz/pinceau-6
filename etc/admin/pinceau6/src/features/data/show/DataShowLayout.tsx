import React, {useContext, useEffect, useMemo, useState} from "react";
import {useLocation} from "react-router";
import {TitleContext} from "../../../title_context";
import {
    ChipField,
    ReferenceArrayField,
    SimpleShowLayout,
    TabbedShowLayout,
    Title,
    useDataProvider,
    useShowContext
} from "react-admin";
import {ConcreteField, FieldOpts} from "../types";
import {useQuery} from "@tanstack/react-query";
import {schemaFieldFunction} from "../SchemaField";
import {Grid} from "@mui/material";

type DataShowLayoutProps = {
    onSetModel: (_: any) => void;
};

export const DataShowLayout: React.FC<DataShowLayoutProps> = ({onSetModel}) => {
    const location = useLocation();
    const [titleContext, setTitleContext] = useContext(TitleContext);
    const {resource, record, isLoading} = useShowContext();
    const [fields, setFields] = useState<Array<ConcreteField>>([]);
    const [layout, setLayout] = useState("");
    const dataProvider = useDataProvider();

    const collection = resource.split("/")[2];

    const titlePath = useMemo(() => {
        const pathName = location.pathname;
        return pathName.substring(0, pathName.length - 5);
    }, [location.pathname]);

    const model = useMemo(() => {
        if (record) {
            if (titleContext[titlePath] !== record._meta.label) {
                setTitleContext({...titleContext, [titlePath]: record._meta.label});
            }
            //
            return record._meta.model;
        }
        return collection;
    }, [
        record,
        collection,
        titleContext,
        titlePath,
        setTitleContext,
    ]);

    const {data} = useQuery({
        queryKey: ["data", "schema", model, 'show'],
        queryFn: () => dataProvider.collectionSchema(model, 'show'),
        enabled: !isLoading && !!record,
    });

    useEffect(() => {
        if (data) {
            onSetModel(data);
            setFields(data.fields);
            setLayout(data.layout);
        }
    }, [data, onSetModel]);

    return (
        <>
            {record && <Title title={record._meta.label}/>}

            {layout == "simple" && (
                <SimpleShowLayout>
                    {schemaFieldFunction(fields, undefined, undefined, undefined, 'show')}
                </SimpleShowLayout>
            )}
            {layout == "tabbed" && (
                <TabbedShowLayout>
                    {fields.map((field, i) => {
                        const opts = field["opts"] || [];
                        const wrap = opts.indexOf(FieldOpts.grid) !== -1;

                        if (wrap) {
                            // <Grid container>{children}</Grid>
                            return (
                                <TabbedShowLayout.Tab
                                    label={field.label || `Tab ${i + 1}`}
                                    key={i}
                                >
                                    <Grid container>
                                        {schemaFieldFunction(field.fields || [], "show", true, undefined, 'show')}
                                    </Grid>
                                </TabbedShowLayout.Tab>
                            );
                        }

                        return (
                            <TabbedShowLayout.Tab
                                label={field.label || `Tab ${i + 1}`}
                                key={i}
                            >
                                {schemaFieldFunction(field.fields || [], "show", wrap, undefined, 'show')}
                            </TabbedShowLayout.Tab>
                        );
                    })}
                </TabbedShowLayout>
            )}
        </>
    );
};