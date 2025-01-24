import {FunctionField, SimpleShowLayout, TextField, useShowController} from "react-admin";
import React, {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {StatusMap} from "./types";
import {useParams} from "react-router-dom";
import {useQuery} from "@tanstack/react-query";
import {dataProvider} from "../../data-provider";
import CircularProgressWithLabel from "./CircularProgressWithLabel";
import CircularProgress from "@mui/material/CircularProgress";
import TaskGraphSocket from "./TaskGraphSocket";
import {DOTGraph} from "./DOTGraph";

type UpdateSvgRef = () => void;

export const JobShowLayout = () => {
    const showController = useShowController();
    const [dagStatus, setDagStatus] = useState<string>("-");
    const [dagProgress, setDagProgress] = useState<number | undefined>(undefined);
    const taskStatus = useRef<StatusMap>({});
    const updateRef = useRef<undefined | UpdateSvgRef>();
    const { variant, jobId, id } = useParams();

    useEffect(() => {
        if (showController.record) {
            setDagStatus(showController.record.status);
        }
    }, [showController.record]);

    const dagStatusCB = useCallback((status: string, progress: number | undefined) => {
        setDagStatus(status);
        setDagProgress(progress);
    }, []);

    const taskStatusCB = useCallback((taskId: string, status: string) => {
        taskStatus.current[taskId] = status;
        if (updateRef.current) {
            updateRef.current();
        }
    }, []);

    useEffect(() => {
        console.log("showController updated");
    }, [showController]);

    useEffect(() => {
        console.log("dagStatusCB");
    }, [dagStatusCB]);

    useEffect(() => {
        console.log("taskStatusCB");
    }, [taskStatusCB]);

    useEffect(() => {
        console.log("showController.record.ui");
    }, [showController.record?.ui]);

    const progressIndicatorMode = useMemo(() => {
        if (dagStatus != "RUNNING") {
            return "";
        }
        if (dagProgress !== undefined) {
            return "determinate";
        } else {
            return "indeterminate";
        }
    }, [dagStatus, dagProgress]);

    let graphId = id as string;
    if (variant != "_default_") {
        graphId += `[${variant}]`;
    }
    graphId += `:${jobId}`;

    const { data: graphData } = useQuery({
        queryKey: ["dag", graphId, "graph"],
        queryFn: () => dataProvider.dagGraph(graphId),
        enabled: !!showController.record,
    });

    const progressIndicator = useMemo(() => {
        if (progressIndicatorMode === "indeterminate" || dagProgress === undefined) {
            return <CircularProgress />
        }
        if (progressIndicatorMode === "determinate") {
            return <CircularProgressWithLabel value={dagProgress} />
        }

        return null

    }, [progressIndicatorMode, dagProgress])

    if (!showController.record) {
        return null;
    }

    return (
        <SimpleShowLayout>
            <TextField source="id" />
            <TextField source="label" />
            <TextField source="description" />
            <FunctionField label="Status" render={() => dagStatus} />
            {progressIndicator}
            <FunctionField
                render={(record) => (
                    <TaskGraphSocket
                        graphId={graphId}
                        onDagStatusUpdate={dagStatusCB}
                        onTaskStatusUpdate={taskStatusCB}
                        ui={record.ui}
                    />
                )}
            />

            <DOTGraph
                graphData={graphData}
                statuses={taskStatus.current}
                updateRef={updateRef}
            />
        </SimpleShowLayout>
    );
};
