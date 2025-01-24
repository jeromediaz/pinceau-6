import {useLocation} from "react-router";
import React, {useContext, useEffect, useMemo, useRef, useState} from "react";
import {WebSocketContext} from "../../../context/websocket_context";
import {TitleContext} from "../../../title_context";
import {useDataProvider, useEditContext, useRefresh} from "react-admin";
import {useQuery} from "@tanstack/react-query";
import SimpleEditForm from "../SimpleEditForm";
import TabbedEditForm from "../TabbedEditForm";

export const DataEditForm = () => {
    const location = useLocation();
    const websocket = useContext(WebSocketContext);
    const [titleContext, setTitleContext] = useContext(TitleContext);
    const {resource, record, isLoading} = useEditContext();
    const [fields, setFields] = useState([]);
    const [layout, setLayout] = useState("");
    const exitRef = useRef({})
    const dataProvider = useDataProvider();
    const collection = resource.replace("data/mongodb/", "").replace("data/elastic/", "").split("/")[0];
    const [isLocked, setLocked] = useState<undefined | boolean>(undefined);
    const refresh = useRefresh();

    const lockId = useMemo(() => {
        if (resource && record) {
            return `${resource}/${record.id}`;
        }
        return undefined;
    }, [resource, record])

    useEffect(() => {
        return () => {
            console.log('unmount')
            const {isLocked, websocket, lockId} = exitRef.current;
            if (isLocked && websocket && lockId) {
                console.log('emit release_lock')
                websocket.emit('release_lock', {lockId});
            }
        }
    }, []);

    useEffect(() => {

        function onLockChange(data) {
            const currentExitRef = exitRef.current
            console.log('onLockChange', data, currentExitRef.lockId);

            if (currentExitRef.lockId in data && data[currentExitRef.lockId] === 'released') {
                console.log('try acquire lock')
                refresh()
                currentExitRef.websocket.emit('acquire_lock', {lockId: currentExitRef.lockId}, (val) => {
                    console.log('callback val onLockChange', {val})
                    setLocked(val)
                })
            }
        }

        if (websocket.connected) {
            websocket.on('lockChange', onLockChange)
        }

        return () => {
            if (websocket.connected) {
                websocket.off("lockChange", onLockChange)
            }
        }
    }, [websocket, websocket.connected]);

    useEffect(() => {
        exitRef.current = {isLocked, websocket, lockId};
        console.log('current', exitRef.current)
        if (websocket.connected && isLocked === undefined && lockId) {
            console.log('acquire_lock')
            websocket.emit('acquire_lock', {lockId}, (val) => {
                console.log('callback val', {val})
                setLocked(val)
            })
        }

    }, [lockId, websocket, websocket.connected, isLocked]);

    const model = useMemo(() => {
        if (record) {
            const pathName = location.pathname;
            setTitleContext({
                ...titleContext.current,
                [pathName]: record._meta.label,
            });
            return record._meta.model;
        }
        return collection;
    }, [location.pathname, record, collection]);

    const {data} = useQuery({
        queryKey: ["data", "schema", model, 'edit'],
        queryFn: () => dataProvider.collectionSchema(model, 'edit'),
        enabled: !isLoading && !!record,
    });

    useEffect(() => {
        if (data) {
            const fields = structuredClone(data.fields);

            if (isLocked) {
                setFields(fields);
            } else {
                setFields(fields.map((field) => {
                    const fieldOpts = field.opts || []
                    fieldOpts.push('readOnly')
                    field.opts = fieldOpts
                    return field
                }))
            }
            setLayout(data.layout);
        }
    }, [data, isLocked]);

    return (
        <>
            {layout == "simple" && <SimpleEditForm fields={fields} readOnly={!isLocked} schemaMode={"edit"}/>}
            {layout == "tabbed" && <TabbedEditForm fields={fields} readOnly={!isLocked} schemaMode={"edit"}/>}
        </>
    );
};