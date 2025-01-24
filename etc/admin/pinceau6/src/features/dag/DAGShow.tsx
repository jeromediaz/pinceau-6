import {
    Confirm,
    Show,
    useDataProvider,
    useRefresh,
    useShowController
} from "react-admin";
import React, {useCallback, useMemo, useState,} from "react";
import "../../task-status.module.css";
import {useMutation} from "@tanstack/react-query";
import Button from '@mui/material/Button';
import CardContent from "@mui/material/CardContent";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import ToggleButton from "@mui/material/ToggleButton";
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import {useParams} from "react-router-dom";
import Stack from '@mui/material/Stack';
import {useLocation, useNavigate} from "react-router";
import DuplicateVariantForm from "./DuplicateVariantForm";
import {DagShowLayout} from "./DAGShowLayout";


type DagObjectType = {
    params: any;
    variants: any;
    dagParams: any;
    chatCompatible: false | any
}

export const DagShow = () => {
    const showController = useShowController();
    const dataProvider = useDataProvider();
    const {variant, id} = useParams();
    const refresh = useRefresh();
    const location = useLocation();
    const [record, setRecord] = useState<DagObjectType | undefined>(undefined);
    const [open, setOpen] = useState<boolean>(false);
    const [confirmDeleteVariantOpen, setConfirmDeleteVariantOpen] = useState<boolean>(false);

    const {data: deleteData, mutate: deleteParams} = useMutation({
        mutationFn: () => {
            const graphId = variant == '_default_' ? id : `${id}[${variant}]`
            return dataProvider.deleteParams(graphId).then(() => {
                refresh()
                if (!variant) {
                    return
                }

                const current = `/dag/${id}/${encodeURI(variant)}/`;
                const next = `/dag/${id}/_default_/`;

                const navigateTo = location.pathname.replace(current, next);
                navigate(navigateTo);

                setConfirmDeleteVariantOpen(false);
            })
        }
    })



    const handleClose = useCallback(() => {
        setOpen(false);
    }, [setOpen]);

    const graphId = variant == '_default_' ? id : `${id}[${variant}]`

    const navigate = useNavigate();

    const duplicateVariant = useCallback(() => {
        setOpen(true)
    }, [setOpen])

    const deleteVariant = useCallback(() => {
        setConfirmDeleteVariantOpen(true)
        console.log('deleteVariant true')
    }, [setConfirmDeleteVariantOpen])

    const handleDialogClose = useCallback(() => {
        setConfirmDeleteVariantOpen(false);
        console.log('deleteVariant false')
    }, [setConfirmDeleteVariantOpen])

    const handleDeleteVariant = useCallback(() => {
        console.log('deleteVariant true')
        setConfirmDeleteVariantOpen(true)
        deleteParams();
    }, [deleteParams])

    const aside = useMemo(() => {
        if (record?.params?.length) {
            const handleChange = (
                event: React.MouseEvent<HTMLElement>,
                nextView: string,
            ) => {
                if (nextView && variant) {
                    const current = `/dag/${id}/${encodeURI(variant)}/`
                    const next = `/dag/${id}/${encodeURI(nextView)}/`

                    navigate(location.pathname.replace(current, next));
                }
            };

            return (
                <Card sx={{ml: 1}}>
                    <CardHeader title="Variants"/>

                    <CardContent>
                        <ToggleButtonGroup
                            orientation="vertical"
                            value={variant}
                            exclusive
                            onChange={handleChange}
                            sx={{width: "100%"}}
                        > {(record && record.variants) &&
                            record.variants.map((vari: string) => {
                                return (
                                    <ToggleButton key={vari} value={vari} aria-label={vari}>
                                        {vari}
                                    </ToggleButton>
                                )
                            })
                        }

                        </ToggleButtonGroup>

                        <DuplicateVariantForm open={open} handleClose={handleClose} params={record.dagParams}/>

                        <Stack direction="row" spacing={2} sx={{width: '100%', padding: 1}} justifyContent={"center"}>
                            <Button variant="outlined" onClick={duplicateVariant}>
                                <ContentCopyIcon/>
                            </Button>
                        </Stack>
                        <Confirm isOpen={confirmDeleteVariantOpen} title={"Delete variant?"} content={"Are you sure you want to delete this variant?"} onConfirm={handleDeleteVariant} onClose={handleDialogClose} />
                        <Stack direction="row" spacing={2} sx={{width: '100%', padding: 1}} justifyContent={"center"}>
                            <Button variant="outlined" disabled={variant == '_default_'} onClick={deleteVariant}>
                                <DeleteOutlineIcon/>
                            </Button>
                        </Stack>
                    </CardContent>
                </Card>
            );
        }
        return undefined;
    }, [record, variant, open, handleClose, duplicateVariant, confirmDeleteVariantOpen, handleDeleteVariant, handleDialogClose, deleteVariant, id, navigate, location.pathname]);


    const onRecord = useCallback((record: DagObjectType) => {
        setRecord(record)
    }, [])

    if (!showController.record) {
        return null;
    }


    // not a running dag
    return (
        <Show id={graphId} aside={aside}>
            <DagShowLayout onRecord={onRecord}/>
        </Show>
    );


};

