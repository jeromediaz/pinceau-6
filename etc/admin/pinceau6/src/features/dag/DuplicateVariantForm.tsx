import React, {useCallback, useEffect, useRef} from "react";
import {Create, SimpleForm, TextInput, useDataProvider, useRefresh} from "react-admin";
import {useParams} from "react-router-dom";
import {useMutation} from "@tanstack/react-query";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import {FieldValues} from "react-hook-form";
import {useLocation, useNavigate} from "react-router";

type DuplicateVariantFormProps = {
    open: boolean;
    handleClose: () => void;
    params: any;
}

type PutParamsProps = {
    variant: string;
    params: any;
}

const DuplicateVariantForm: React.FC<DuplicateVariantFormProps> = ({open, handleClose, params}) => {
    const dataProvider = useDataProvider();
    const navigate = useNavigate();
    const location = useLocation();
    const {id, variant} = useParams()
    const refresh = useRefresh();
    const duplicateVariantName = useRef()

    const {data: paramsData, mutate: setParams} = useMutation({
        mutationFn: (payload: PutParamsProps) => {
            const {variant, params} = payload
            const graphId = variant == '_default_' ? id : `${id}[${variant}]`
            return dataProvider.putParams(graphId, params);
        }
    });

    const onSubmit = useCallback((data: FieldValues) => {
        duplicateVariantName.current = data.variant_id;
        setParams({params, variant: data.variant_id});
    }, [setParams, params])

    useEffect(() => {
        if (paramsData && variant && duplicateVariantName.current) {
            refresh();
            handleClose();

            const current = `/dag/${id}/${encodeURI(variant)}/`;
            const next = `/dag/${id}/${encodeURI(duplicateVariantName.current)}/`;

            const navigateTo = location.pathname.replace(current, next);
            navigate(navigateTo);
        }
    }, [navigate, handleClose, refresh, paramsData, id, variant, location.pathname])

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Duplicate variant</DialogTitle>
            <DialogContent>
                <Create>
                    <SimpleForm onSubmit={onSubmit}>
                        <TextInput source={"variant_id"}/>
                    </SimpleForm>
                </Create>
            </DialogContent>
        </Dialog>
    )
}

export default DuplicateVariantForm;
