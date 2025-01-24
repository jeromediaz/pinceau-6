import {styled} from "@mui/material/styles";
import {EmptyClasses, EmptyProps} from "ra-ui-materialui/src/list/Empty";
import React from "react";
import {useGetResourceLabel, useResourceContext, useTranslate} from "ra-core";
import Inbox from "@mui/icons-material/Inbox";
import Typography from "@mui/material/Typography";
import {Button} from "ra-ui-materialui/src/button/Button";
import ContentAdd from "@mui/icons-material/Add";

const PREFIX = "RaEmpty";

const Root = styled("span", {
    name: PREFIX,
    overridesResolver: (props, styles) => styles.root,
})(({ theme }) => ({
    flex: 1,
    [`& .${EmptyClasses.message}`]: {
        textAlign: "center",
        opacity: theme.palette.mode === "light" ? 0.5 : 0.8,
        margin: "0 1em",
        color:
            theme.palette.mode === "light" ? "inherit" : theme.palette.text.primary,
    },

    [`& .${EmptyClasses.icon}`]: {
        width: "9em",
        height: "9em",
    },

    [`& .${EmptyClasses.toolbar}`]: {
        textAlign: "center",
        marginTop: "2em",
    },
}));

type EmptyPropsExtended = EmptyProps & {
    handleClickOpen: () => void;
};

export const EmptyJobList: React.FC<EmptyPropsExtended> = (props) => {
    const { className } = props;
    const resource = useResourceContext(props);

    const translate = useTranslate();

    const getResourceLabel = useGetResourceLabel();
    const resourceName = translate(`resources.${resource}.forcedCaseName`, {
        smart_count: 0,
        _: getResourceLabel(resource, 0),
    });

    const emptyMessage = translate("ra.page.empty", { name: resourceName });
    const inviteMessage = translate("ra.page.invite");

    return (
        <Root className={className}>
            <div className={EmptyClasses.message}>
                <Inbox className={EmptyClasses.icon} />
                <Typography variant="h4" paragraph>
                    {translate(`resources.${resource}.empty`, {
                        _: emptyMessage,
                    })}
                </Typography>
                <Typography variant="body1">
                    {translate(`resources.${resource}.invite`, {
                        _: inviteMessage,
                    })}
                </Typography>
            </div>
            <div className={EmptyClasses.toolbar}>
                <Button
                    label="ra.action.create"
                    color="primary"
                    onClick={props["handleClickOpen"]}
                    variant="contained"
                >
                    <ContentAdd />
                </Button>
            </div>
        </Root>
    );
};