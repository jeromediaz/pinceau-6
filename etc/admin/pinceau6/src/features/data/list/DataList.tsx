import {
    List,
    ListActions,
    TextInput,
} from "react-admin";
import React, {ReactElement, useMemo} from "react";
import {useParams} from "react-router-dom";
import {useResourceContext} from "ra-core";
import {Empty} from "ra-ui-materialui/src/list/Empty";
import {DataListDatagrid} from "./DataListDatagrid";


const listFilter = [
    <TextInput key="query-filter" label="Search" source="q" alwaysOn/>,
];

type DataListProps = {
    schema?: string
    resource?: string
    filter?: any
    empty?: any
    hasCreate?: boolean
    aside?: ReactElement
    actions?: any
}

export const DataList: React.FC<DataListProps> = (props) => {
    const {schema, filter = {}, resource, empty, hasCreate = true, aside, actions} = props;
    const params = useParams();

    const resourceContext = useResourceContext(props);

    const emptyValue = useMemo(() => {
        if (empty === undefined) {
            return (<Empty/>)
        }
        return empty
    }, [empty])

    const resourceParam = useMemo(() => {
        if (resource) {
            return resource
        }
        let resource_prefix = resourceContext;
        const star_params = params['*']
        if (star_params) {
            resource_prefix += '/';
            resource_prefix += star_params;
        }
        return resource_prefix;
    }, [resource, resourceContext, params])

    const finalActions = useMemo(() => {
        if (actions) {
            return actions;
        }
        return <ListActions hasCreate={hasCreate}/>
    }, [actions, hasCreate])

    return (
        <List
            filters={listFilter}
            filter={filter}
            resource={resourceParam}
            empty={emptyValue}
            actions={finalActions}
            aside={aside}
        >
            <DataListDatagrid schema={schema}/>
        </List>
    );
};
