import { useRecordContext } from "react-admin";
import { Button } from "ra-ui-materialui";
import { Link } from "react-router-dom";
import React, { ReactElement } from "react";
import CallMadeIcon from "@mui/icons-material/CallMade";

// eslint-disable-next-line no-unused-vars
type PathHandlerCallbackType = (arg0: any) => string;

const defaultIcon = <CallMadeIcon />;

type PageButtonProps = {
  label: string;
  pathHandler: PathHandlerCallbackType;
  icon?: ReactElement;
};
const stopPropagation = (e) => e.stopPropagation();

export const PageButton: React.FC<PageButtonProps> = (props) => {
  const { label, pathHandler, icon = defaultIcon } = props;
  const record = useRecordContext();

  return (
    <Button
      component={Link}
      to={{ pathname: pathHandler(record) }}
      onClick={stopPropagation}
      label={label}
    >
      {icon}
    </Button>
  );
};
