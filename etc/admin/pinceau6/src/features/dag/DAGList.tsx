import {
  ArrayField,
  ChipField,
  Datagrid,
  List,
  SingleFieldList,
  TextField,
  TextInput,
} from "react-admin";
import { StringToLabelObject } from "../data/SchemaField";
import React, { useMemo } from "react";
import DAGShowButton from "./DAGShowButton";
import {DAGListActions} from "./DAGListActions";
import {EmptyDAGList} from "./EmptyDAGList";

const listFilter = [
  <TextInput key="list-filter-search" label="Search" source="q" alwaysOn />,
];

type DAGListProps = {
  parent_id?: string;
  handleClickOpen?: () => void;
};

export const DAGList: React.FC<DAGListProps> = (props) => {
  const { parent_id = null, handleClickOpen } = props;

  const actions = useMemo(() => {
    if (!handleClickOpen || !parent_id) {
      return undefined;
    }

    return <DAGListActions handleClickOpen={handleClickOpen} />;
  }, [handleClickOpen, parent_id]);

  return (
    <List
      actions={actions}
      filters={listFilter}
      empty={<EmptyDAGList handleClickOpen={props["handleClickOpen"]} />}
      filter={{ parent_id: parent_id }}
      exporter={false}
    >
      <Datagrid>
        <TextField source="id" label={"ID"} />
        <TextField source="label" />
        <TextField source="description" sortable={false} />

        <ChipField source="requiredWorkerTag" />
        <ArrayField source="tags">
          <SingleFieldList linkType={false}>
            <StringToLabelObject>
              <ChipField source="label" size="small" />
            </StringToLabelObject>
          </SingleFieldList>
        </ArrayField>
        <DAGShowButton />
      </Datagrid>
    </List>
  );
};
