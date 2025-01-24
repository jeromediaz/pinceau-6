import React, {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {StatusMap} from "./types";
import {useParams} from "react-router-dom";
import {
    ChipField,
    RecordContextProvider,
    SimpleForm,
    SimpleShowLayout,
    TabbedShowLayout,
    TextField,
    useDataProvider,
    useRefresh,
    useShowController
} from "react-admin";
import {useMutation, useQuery} from "@tanstack/react-query";
import ChatListActions from "./ChatListActions";
import {SchemaInputFields} from "../data/SchemaInputFields";
import {DOTGraph} from "./DOTGraph";
import {Grid} from "@mui/material";
import CreateChatForm from "./CreateChatForm";
import {DataList} from "../data/list/DataList";
import {GraphRunForm} from "./GraphRunForm";
import JobList from "./JobList";

type DagShowLayoutProps = {
    onRecord: (data: any) => void
}

type UpdateSvgRef = () => void;


export const DagShowLayout: React.FC<DagShowLayoutProps> = ({onRecord}) => {
    const [open, setOpen] = useState(false);
    const [chatCreationOpen, setChatCreationOpen] = useState(false);
    const taskStatus = useRef<StatusMap>({});
    const updateRef = useRef<undefined | UpdateSvgRef>();
    const {variant, id} = useParams();
    const refresh = useRefresh();

    const graphId = variant == '_default_' ? id : `${id}[${variant}]`
    const showController = useShowController({id: graphId});


    const dataProvider = useDataProvider();
    const {data: paramsData, mutate: setParams} = useMutation({
        mutationFn: (payload) => dataProvider.putParams(graphId, payload),
    });

    useEffect(() => {
        if (paramsData) {
            refresh()
        }
    }, [refresh, paramsData])

    const handleClickOpen = useCallback(() => {
        setOpen(true);
    }, []);

    const handleChatCreationClickOpen = useCallback(() => {
        setChatCreationOpen(true);
    }, [])

    const handleClose = useCallback(() => {
        setOpen(false);
    }, []);

    const handleChatCreationClose = useCallback(() => {
        setChatCreationOpen(false);
    }, []);

    useEffect(() => {
        onRecord(showController.record)
    }, [onRecord, showController.record]);

    const onSubmit = useCallback((data) => {
        setParams(data);
    }, [setParams]);

    const {data: graphData} = useQuery({
        queryKey: [],
        queryFn: () => dataProvider.dagGraph(showController.record.id),
        enabled: !!showController.record,
    });

    const parentId = useMemo(() => {
        if (variant != "_default_") {
            return `${id}[${variant}]`;
        }
        return id;
    }, [id, variant]);

    const chatActions = useMemo(() => {
        if (!handleChatCreationClickOpen) {
            return undefined;
        }
        return <ChatListActions handleClickOpen={handleChatCreationClickOpen} />;
    }, [handleChatCreationClickOpen]);

    const DagParams = useMemo(() => {
        if (!showController.record) {
            return null;
        }
        return (
            <RecordContextProvider value={showController.record.dagParams}>
                <SimpleForm onSubmit={onSubmit}>
                    <SchemaInputFields fields={showController.record.params} schemaMode={"default"}/>
                </SimpleForm>
            </RecordContextProvider>
        )
    }, [onSubmit, showController.record])

    const FirstTab = useMemo(() => {
        if (!showController.record?.params?.length) {
            return (
                <TabbedShowLayout.Tab label="DAG">
                    <TextField source="id"/>
                    <TextField source="label"/>
                    <TextField source="description"/>
                    <DOTGraph
                        graphData={graphData}
                        statuses={taskStatus.current}
                        updateRef={updateRef}
                    />
                </TabbedShowLayout.Tab>
            )
        }

        return (
            <TabbedShowLayout.Tab label="DAG">
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <SimpleShowLayout>
                            <TextField source="id"/>
                            <TextField source="label"/>
                            <TextField source="description"/>
                            <ChipField source="requiredWorkerTag"/>

                            <DOTGraph
                                graphData={graphData}
                                statuses={taskStatus.current}
                                updateRef={updateRef}
                                rankDir={"TB"}
                                fontSize={10}
                            />
                        </SimpleShowLayout>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        {DagParams}
                    </Grid>

                </Grid>

            </TabbedShowLayout.Tab>
        )


    }, [DagParams, graphData, showController.record])

    const ChatPart = useMemo(() => {
        if (!showController.record?.chatCompatible) {
            return (<div>This DAG/variant is not chat compatible</div>)
        }
        return (
            <>
                <CreateChatForm
                    open={chatCreationOpen}
                    handleClose={handleChatCreationClose}
                    dagVariation={showController.record?.id}
                    chatData={showController.record?.chatCompatible}/>
                <DataList
                    resource={"data/mongodb/chat"}
                    schema={"chat_from_wrapped_dag"}
                    empty={false}
                    actions={chatActions}
                    filter={{'dag_id': showController.record?.id}}/>
            </>
        )
    }, [chatActions, chatCreationOpen, handleChatCreationClose, showController.record?.chatCompatible, showController.record?.id])

    if (!showController.record || !graphId) {
        return null
    }



    return (
        <TabbedShowLayout>
            {FirstTab}
            <TabbedShowLayout.Tab label="Jobs" path={"jobs"}>
                <GraphRunForm
                    graphId={graphId}
                    open={open}
                    handleClose={handleClose}
                />
                <JobList parentId={parentId} handleClickOpen={handleClickOpen}/>
            </TabbedShowLayout.Tab>
            <TabbedShowLayout.Tab label="Chats" path={"chats"}>
                {ChatPart}
            </TabbedShowLayout.Tab>
        </TabbedShowLayout>
    )
}