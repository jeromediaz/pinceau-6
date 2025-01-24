import React, { useEffect, useState } from "react";
import {
  ListContextProvider,
  ResourceContextProvider,
  useDataProvider,
  useList,
  WithListContext,
} from "react-admin";
import { useBasename } from "ra-core/src/routing/useBasename";

import { ListItem, ListItemButton, ListItemText } from "@mui/material";
import { Link } from "react-router-dom";
import { removeDoubleSlashes } from "ra-core/src/routing/useCreatePath";

type RunningJobsProps = {
  runCount: number;
};

const RunningJobs: React.FC<RunningJobsProps> = ({ runCount }) => {
  const [dagList, setDagList] = useState([]);
  const dataProvider = useDataProvider();
  console.log({ runCount });
  useEffect(() => {
    dataProvider
      .getList("dag", {
        pagination: { page: 1, perPage: runCount + 2 },
        filter: { status: "RUNNING" },
        sort: { field: "id", order: "ASC" },
      })
      .then(({ data }) => {
        console.log("dag", data);
        setDagList(data);
      });
  }, [runCount]);

  const baseName = useBasename();

  const listContext = useList({
    resource: "dag",
    data: dagList,
    isPending: false,
    perPage: runCount + 2,
    sort: { field: "id", order: "ASC" },
  });

  return (
    <ResourceContextProvider value="dag">
      <ListContextProvider value={listContext}>
        <WithListContext
          render={({ isPending, data }) => {
            if (isPending || !data) {
              return null;
            }

            return data.map((record) => {
              const recordId = record.id as string;
              const [rawDag, jobId] = recordId.split(":");

              const indexOfVariant = rawDag.indexOf("[");
              const dag =
                  indexOfVariant > 0
                      ? rawDag.substring(0, indexOfVariant)
                      : rawDag;
              const variant =
                  indexOfVariant > 0
                      ? rawDag.substring(indexOfVariant + 1, rawDag.length - 1)
                      : "_default_";

              const to = removeDoubleSlashes(
                  `${baseName}/dag/${encodeURIComponent(dag)}/${variant}/show/jobs/${encodeURIComponent(jobId)}`,
              );
              let runDateDisplay = "-"

              if (record && record.run && record.run.start) {
                const runDate = new Date(record.run.start);
                runDateDisplay =
                    runDate.toLocaleDateString() +
                    " " +
                    runDate.toLocaleTimeString();
              }

              return (
                <ListItem disablePadding key={record.id}>
                  <ListItemButton component={Link} to={to}>
                    <ListItemText
                      primary={<div>{record.label}</div>}
                      secondary={runDateDisplay}
                    />
                  </ListItemButton>
                </ListItem>
              );
            });
          }}
        />
      </ListContextProvider>
    </ResourceContextProvider>
  );
};

export default RunningJobs;
