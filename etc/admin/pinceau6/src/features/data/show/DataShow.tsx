import {
  Show
} from "react-admin";
import {useCallback, useState,} from "react";
import {DataShowActions} from "./DataShowActions";
import {DataShowAside} from "./DataShowAside";
import {DataShowLayout} from "./DataShowLayout";


export const DataShow = () => {
    const [model, setModel] = useState();

    const onSetModel = useCallback((data) => {
        setModel(data);
    }, []);

    return (
        <Show actions={<DataShowActions />} aside={<DataShowAside model={model}/>}>
            <DataShowLayout onSetModel={onSetModel}/>
        </Show>
    );
};
