import {
  Show
} from "react-admin";
import React from "react";
import "../../task-status.module.css";
import { useParams } from "react-router-dom";
import {JobShowLayout} from "./JobShowLayout";

export const JobShow = () => {
  const { variant, jobId, id } = useParams();

  let graphId = id;
  if (variant != "_default_") {
    graphId += `[${variant}]`;
  }
  graphId += `:${jobId}`;

  return (
    <Show id={graphId} resource={"dag"}>
      <JobShowLayout />
    </Show>
  );
};
