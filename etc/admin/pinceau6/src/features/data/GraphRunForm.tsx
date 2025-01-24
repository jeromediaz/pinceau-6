import React, {useCallback, useEffect} from "react";
import {useNavigate} from "react-router";
import {Create, Form, SaveButton, TextInput, useDataProvider} from "react-admin";
import {useMutation} from "@tanstack/react-query";
import {FieldValues} from "react-hook-form";
import Typography from "@mui/material/Typography";
import {SchemaInputFields} from "./SchemaInputFields";

type GraphRunFormProps = {
    objectId: string;
    dagAction: any; // TODO
};

export const GraphRunForm: React.FC<GraphRunFormProps> = ({objectId, dagAction}) => {
    const navigate = useNavigate();
    const dataProvider = useDataProvider();
    const {data: runMutationData, mutate} = useMutation({
        mutationFn: (payload) => dataProvider.runDAG(dagAction.name, payload),
    });

    const onSubmit = useCallback(
        (data: FieldValues) => {
            mutate(data);
        },
        [mutate],
    );

    useEffect(() => {
        if (runMutationData) {
            const {dagId} = runMutationData;

            const [rawDag, jobId] = dagId.split(":");

            const indexOfVariant = rawDag.indexOf("[");
            const dag =
                indexOfVariant > 0 ? rawDag.substring(0, indexOfVariant) : rawDag;
            const variant =
                indexOfVariant > 0
                    ? rawDag.substring(indexOfVariant + 1, rawDag.length - 1)
                    : "_default_";

            navigate(`/dag/${dag}/${variant}/show/jobs/${jobId}`);
        }
    }, [navigate, runMutationData]);

    return (
        <Create>
            <Form onSubmit={onSubmit}>
                <Typography variant="body2">{dagAction.name}</Typography>
                <TextInput
                    source={dagAction.field}
                    defaultValue={objectId}
                    style={{display: "none"}}
                />
                <div>
                    <SchemaInputFields fields={dagAction.inputs}/>
                </div>
                <SaveButton label={"RUN"} alwaysEnable={true}/>
            </Form>
        </Create>
    );
};