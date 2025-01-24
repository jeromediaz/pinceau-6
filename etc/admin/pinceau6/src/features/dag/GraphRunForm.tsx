import { Create, Form, SaveButton, useDataProvider } from "react-admin";
import { useMutation, useQuery } from "@tanstack/react-query";

import { SchemaInputFields } from "../data/SchemaInputFields";
import React, {useCallback, useEffect, useRef} from "react";
import { useNavigate } from "react-router";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import Stack from "@mui/material/Stack";

type GraphRunFormProps = {
  graphId: string;
  open: boolean;
  handleClose: () => void;
};
export const GraphRunForm: React.FC<GraphRunFormProps> = ({
  graphId,
  open,
  handleClose,
}) => {
  const navigate = useNavigate();
  const dataProvider = useDataProvider();
  const { data: runMutationData, mutate: runMutate } = useMutation({
    mutationFn: (payload) => dataProvider.runDAG(graphId, payload),
  });
  const { data: persistMutationData, mutate: persistMutate } = useMutation({
    mutationFn: (payload) => dataProvider.persistDAG(graphId, payload),
  });
  const requirements = useQuery({
    queryKey: ["dag", graphId, "run"],
    queryFn: () => dataProvider.graphRequirements(graphId),
  });

  const clickOrigin = useRef<string>("run");

  useEffect(() => {
    if (!runMutationData) {
      return
    }

    const { dagId } = runMutationData;

    const [rawDag, jobId] = dagId.split(":");

    const indexOfVariant = rawDag.indexOf("[");
    const dag =
      indexOfVariant > 0 ? rawDag.substring(0, indexOfVariant) : rawDag;
    const variant =
      indexOfVariant > 0
        ? rawDag.substring(indexOfVariant + 1, rawDag.length - 1)
        : "_default_";

    navigate(`/dag/${dag}/${variant}/show/jobs/${jobId}`);

  }, [navigate, runMutationData]);

  useEffect(() => {
    if (!persistMutationData) {
      return;
    }
    const { id } = persistMutationData;
    navigate(`/data/mongodb/dag_persisted/${id}`);
  }, [navigate, persistMutationData]);

  const onSubmit = useCallback((data) => {
    if (clickOrigin.current === "run") {
      runMutate(data);
    } else if (clickOrigin.current === "persist") {
      persistMutate(data);
    }
  }, [persistMutate, runMutate]);

  const runOnClick = useCallback((_: any) => {
    clickOrigin.current = "run";
  }, []);

  const persistOnClick = useCallback((_: any) => {
    clickOrigin.current = "persist";
  }, []);

  //requirements.mutate()
  console.log({requirements, success: requirements.isSuccess})
  if (!requirements.isSuccess) {
    return null;
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>Execute DAG</DialogTitle>
      <DialogContent>
        <Create>
          <Form onSubmit={onSubmit}>
            <Stack spacing={2}>
              <SchemaInputFields fields={requirements.data} />

              <Stack
                spacing={2}
                direction="row"
                justifyContent="center"
                alignItems="center"
              >
                <SaveButton
                  label="Run"
                  icon={<PlayArrowIcon />}
                  alwaysEnable={requirements.data.length <= 1}
                  onClick={runOnClick}
                />
                <SaveButton
                  label="Persist"
                  alwaysEnable={requirements.data.length <= 1}
                  onClick={persistOnClick}
                />
              </Stack>
            </Stack>
          </Form>
        </Create>
      </DialogContent>
    </Dialog>
  );
};
