import React from "react";
import {useRecordContext} from "react-admin";
import {useParams} from "react-router-dom";
import {useResourceContext} from "ra-core";
import {useBasename} from "ra-core/src/routing/useBasename";
import {PageButton} from "../PageButton";
import ChatIcon from "@mui/icons-material/Chat";
import Typography from "@mui/material/Typography";
import {GraphRunForm} from "../GraphRunForm";

type DataShowAsideProps = {
    model: any;
}

export const DataShowAside: React.FC<DataShowAsideProps> = (props) => {
    const {model} = props;
    const record = useRecordContext();
    const {id} = useParams();

    const resource = useResourceContext(props);
    const basename = useBasename();
    const prefixUrl = `${basename}/${resource}/${id}/chat`

    if (!model) {
        return null;
    }
    const hasActions = !!model.dagActions.length;
    const hasChatActions = !!model.chatActions.length;

    // FIXME: find a better way
    const isChat = resource === "data/mongodb/chat"

    if (!record || (!hasActions && !hasChatActions && !isChat)) {
        return null;
    }

    return (
        <div style={{width: 200, margin: "1em"}}>
            {isChat &&
                <PageButton
                    label="Chat Room"
                    pathHandler={(record) => `/chat/${record.id}`}
                    icon={<ChatIcon/>}
                />
            }

            {hasActions && (
                <>
                    <Typography variant="h6">Actions</Typography>
                    {model.dagActions.map((action, i) => {
                        return (
                            <GraphRunForm key={i} objectId={record.id} dagAction={action}/>
                        );
                    })}
                </>
            )}

            {hasChatActions && (
                <>
                    <Typography variant="h6">Chat</Typography>
                    {model.chatActions.map((action, i) => {
                        return (
                            <PageButton
                                key={i}
                                label={action.name}
                                pathHandler={(record) => `${prefixUrl}/${action.name}`}
                                icon={<ChatIcon/>}
                            />
                        )
                    })}
                </>
            )}
        </div>
    );
};
