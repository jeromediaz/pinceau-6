import React from "react";
import {TopToolbar} from "react-admin";
import ContentAdd from "@mui/icons-material/Add";
import {Button} from "react-admin"

type ChatListActionsProps = {
    handleClickOpen: () => void;
};

const ChatListActions: React.FC<ChatListActionsProps> = ({ handleClickOpen }) => (
    <TopToolbar>
        <Button label="ra.action.create" color="primary" onClick={handleClickOpen}>
            <ContentAdd />
        </Button>
    </TopToolbar>
);

export default ChatListActions;
