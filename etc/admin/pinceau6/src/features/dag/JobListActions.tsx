import React from "react";
import {TopToolbar} from "react-admin";
import {Button} from "ra-ui-materialui/src/button/Button";
import ContentAdd from "@mui/icons-material/Add";

type JobListActionsProps = {
    handleClickOpen: () => void;
};

export const JobListActions: React.FC<JobListActionsProps> = ({ handleClickOpen }) => (
    <TopToolbar>
        <Button label="ra.action.create" color="primary" onClick={handleClickOpen}>
            <ContentAdd />
        </Button>
    </TopToolbar>
);