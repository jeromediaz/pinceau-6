import React from "react";
import {Button, TopToolbar} from "react-admin";
import ContentAdd from "@mui/icons-material/Add";

type DAGListActionsProps = {
    handleClickOpen: () => void;
};

export const DAGListActions: React.FC<DAGListActionsProps> = ({ handleClickOpen }) => (
    <TopToolbar>
        <Button label="ra.action.create" color="primary" onClick={handleClickOpen}>
            <ContentAdd />
        </Button>
    </TopToolbar>
);
