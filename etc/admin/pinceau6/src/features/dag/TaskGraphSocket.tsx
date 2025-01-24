import React from "react";
import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { WebSocketContext } from "../../context/websocket_context";
import { BooleanField } from "react-admin";
import Stack from "@mui/material/Stack";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import SensorsIcon from "@mui/icons-material/Sensors";
import SensorsOffIcon from "@mui/icons-material/SensorsOff";
import { schemaFieldFunction } from "../data/SchemaField";
import { DataMap } from "./types";
import { ConcreteField } from "../data/types";

type TaskGraphSocketProps = {
  graphId: string;
  onDagStatusUpdate: (status: string, progress: number | undefined) => void;
  onTaskStatusUpdate: (task: string, status: string) => void;
  ui: ConcreteField[];
};

const TaskGraphSocket: React.FC<TaskGraphSocketProps> = ({
  graphId,
  onDagStatusUpdate,
  onTaskStatusUpdate,
  ui,
}) => {
  const socket = useContext(WebSocketContext);
  const status = useRef<string>("IDLE");
  const progress = useRef<number | undefined>(undefined);
  const [isConnected, setIsConnected] = useState(socket.connected);

  const valuesMap = useRef<DataMap>({});
  const [streamIndex, setStreamIndex] = useState(0);

  const [uiElements, setUiElements] = useState(ui);

  useEffect(() => {
    if (socket.connected) {
      // socket already connected
      console.log("subscribe_dag", graphId);
      socket.emit("subscribe_dag", { dag: graphId });
    }

    function onError(error: any) {
      console.log({ error });
    }

    function onConnect() {
      setIsConnected(true);
      console.log("subscribe_dag", graphId);
      socket.emit("subscribe_dag", { dag: graphId });
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onMessage(data: DataMap) {
      const value = data["payload"];
      const graphIdPrefix = `${graphId}::`;
      const graphIdPrefixLength = graphIdPrefix.length;
      let callStatusProgressCallback = false;
      if ("dagStatus" in value) {
        if (graphId in value["dagStatus"]) {
          status.current = value["dagStatus"][graphId];
          callStatusProgressCallback = true;
        }
      }

      if ("dagProgress" in value && graphId in value["dagProgress"]) {
        progress.current = Math.round(value["dagProgress"][graphId] * 100);
        callStatusProgressCallback = true;
      }

      if (callStatusProgressCallback) {
        onDagStatusUpdate(status.current, progress.current);
      }

      if ("taskStatus" in value) {
        for (const [taskId, taskStatus] of Object.entries(
          value["taskStatus"],
        )) {
          if (taskId.startsWith(graphIdPrefix)) {
            const shortTaskId = taskId.substring(graphIdPrefixLength);
            onTaskStatusUpdate(shortTaskId, taskStatus);
          }
        }
      }
      if ("uiElements" in value) {
        const elements = value["uiElements"];
        setUiElements(elements);
      }

      if ("values" in value) {
        const values = value["values"];

        values.forEach((local_val: any) => {
          const task = local_val["task"];
          const id = local_val["id"];
          const stream = local_val["stream"];
          const data = local_val["data"];
          const reset = local_val["reset"];

          const valueID = `${task}::${id}`;
          if (stream) {
            if (Array.isArray(stream)) {
              const oldValue = reset
                ? stream
                : valuesMap.current[valueID] || [];
              oldValue.push(...stream);
              valuesMap.current[valueID] = oldValue;
            } else {
              const newValue = reset
                ? stream
                : (valuesMap.current[valueID] || "") + stream;
              valuesMap.current[valueID] = newValue;
            }
          } else if (data) {
            valuesMap.current[valueID] = data;
          }
          setStreamIndex((index) => index + 1);
        });
      }
    }

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("message", onMessage);
    socket.on("error", onError);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("message", onMessage);
      socket.off("error", onError);
      socket.emit("unsubscribe_dag", { dag: graphId });
    };
  }, [socket, graphId, onDagStatusUpdate, onTaskStatusUpdate]);

  const valuesRecord = useMemo(() => {
    return { ...valuesMap.current };
  }, [streamIndex]);

  const connectedRecord = useMemo(() => {
    return { connected: isConnected };
  }, [isConnected]);

  return (
    <Card>
      <CardHeader
        title={"Live DATA"}
        avatar={
          <BooleanField
            record={connectedRecord}
            source="connected"
            FalseIcon={SensorsOffIcon}
            TrueIcon={SensorsIcon}
          />
        }
      />
      <CardContent>
        <Stack spacing={2}>
          {schemaFieldFunction(uiElements, "show", false, valuesRecord, 'show')}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default TaskGraphSocket;
