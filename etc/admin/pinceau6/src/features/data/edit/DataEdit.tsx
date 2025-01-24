import {
  Edit
} from "react-admin";
import {DataEditForm} from "./DataEditForm";

export const DataEdit = () => (
  <Edit mutationMode={"pessimistic"}>
    <DataEditForm />
  </Edit>
);
