import {
  RaRecord,
  useCreatePath,
  useRecordContext,
  useResourceContext,
} from "ra-core";
import { Button } from "ra-ui-materialui/src/button/Button";
import { Link } from "react-router-dom";
import React, { ReactElement } from "react";
import { ShowButtonProps } from "ra-ui-materialui/src/button/ShowButton";
import ImageEye from "@mui/icons-material/RemoveRedEye";
import { useBasename } from "ra-core/src/routing/useBasename";
import { removeDoubleSlashes } from "ra-core/src/routing/useCreatePath";
import { TopToolbar } from "react-admin";
import ContentAdd from "@mui/icons-material/Add";

// avoids using useMemo to get a constant value for the link state
const scrollStates = {
  true: { _scrollToTop: true },
  false: {},
};

const defaultIcon = <ImageEye />;

// useful to prevent click bubbling in a datagrid with rowClick
const stopPropagation = (e) => e.stopPropagation();

interface Props<RecordType extends RaRecord = any> {
  icon?: ReactElement;
  label?: string;
  record?: RecordType;
  resource?: string;
  scrollToTop?: boolean;
}

const DAGShowButton = <RecordType extends RaRecord = any>(
  props: ShowButtonProps<RecordType>,
) => {
  const {
    icon = defaultIcon,
    label = "ra.action.show",
    record: recordProp,
    resource: resourceProp,
    scrollToTop = true,
    ...rest
  } = props;
  const resource = useResourceContext(props);
  const record = useRecordContext(props);
  const basename = useBasename();

  if (!record) return null;

  const to = removeDoubleSlashes(
    `${basename}/${resource}/${encodeURIComponent(record.id)}/_default_/show`,
  );
  return (
    <Button
      component={Link}
      to={to}
      state={scrollStates[String(scrollToTop)]}
      label={label}
      onClick={stopPropagation}
      {...(rest as any)}
    >
      {icon}
    </Button>
  );
};

export default DAGShowButton;
