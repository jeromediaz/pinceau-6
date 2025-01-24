import React, { useMemo } from "react";
import {
  ArrayField,
  ChipField,
  Datagrid,
  DateField,
  FunctionField,
  List,
  SingleFieldList,
  TextField,
} from "react-admin";
import { StringToLabelObject } from "../data/SchemaField";
import JobShowButton from "./JobShowButton";
import {JobListActions} from "./JobListActions";
import {EmptyJobList} from "./EmptyJobList";


type JobListProps = {
  parentId?: string;
  handleClickOpen?: () => void;
};

const renderDAG = (record: any) => {
  const recordId = record.id as string;
  const [rawDag] = recordId.split(":");

  const indexOfVariation = rawDag.indexOf("[");
  const dag =
    indexOfVariation > 0 ? rawDag.substring(0, indexOfVariation) : rawDag;

  return dag;
};

const renderVariation = (record: any) => {
  const recordId = record.id as string;
  const [rawDag] = recordId.split(":");

  const indexOfVariant = rawDag.indexOf("[");
  const variant =
    indexOfVariant > 0
      ? rawDag.substring(indexOfVariant + 1, rawDag.length - 1)
      : "_default_";

  return variant;
};

const renderJobId = (record: any) => {
  const recordId = record.id as string;
  const [rawDag, jobId] = recordId.split(":");

  return jobId;
};


function DagListEmptyJobList(props: { handleClickOpen: () => void }) {
  return null;
}

const JobList: React.FC<JobListProps> = ({ parentId, handleClickOpen }) => {
  const filter = useMemo(() => {
    if (parentId) {
      return { parent_id: parentId, "-job_id": null };
    }
    return { "-parent_id": null, "-job_id": null };
  }, [parentId]);

  const actions = useMemo(() => {
    if (!handleClickOpen) {
      return undefined;
    }
    return <JobListActions handleClickOpen={handleClickOpen} />;
  }, [handleClickOpen]);

  const empty = useMemo(() => {
    if (!handleClickOpen) {
      return undefined;
    }
    if (!parentId) {
      return <DagListEmptyJobList handleClickOpen={handleClickOpen} />;
    }
    return <EmptyJobList handleClickOpen={handleClickOpen} />;
  }, [parentId, handleClickOpen]);

  return (
    <List
      actions={actions}
      filter={filter}
      empty={empty}
      exporter={false}
      resource="dag"
      storeKey={false}
    >
      <Datagrid>
        {!parentId && <FunctionField label="DAG" render={renderDAG} />}
        {!parentId && (
          <FunctionField label="Variation" render={renderVariation} />
        )}
        <FunctionField label="Job Id" render={renderJobId} />
        <TextField source="label" />
        <TextField source="description" sortable={false} />
        <TextField source="status" sortable={false} />
        <DateField source="run.start" showTime={true} sortable={false} />
        <DateField source="run.end" showTime={true} sortable={false} />
        <ChipField source="requiredWorkerTag" />
        <ArrayField source="tags">
          <SingleFieldList linkType={false}>
            <StringToLabelObject>
              <ChipField source="label" size="small" />
            </StringToLabelObject>
          </SingleFieldList>
        </ArrayField>
        <JobShowButton />
      </Datagrid>
    </List>
  );
};

export default JobList;
