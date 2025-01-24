import React, {useCallback, useEffect} from "react";
import {Create, SimpleForm, TextInput, useDataProvider, useRefresh} from "react-admin";
import {useMutation} from "@tanstack/react-query";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";

type CreateChatFormProps = {
    open: boolean;
    handleClose: () => void;
    dagVariation: string
    chatData: any
}

type ChatFormData = {
    chat_name: string;
}

const CreateChatForm: React.FC<CreateChatFormProps> = ({open, handleClose, chatData, dagVariation}) => {
    const dataProvider = useDataProvider();
    const refresh = useRefresh();
    const { data: persistMutationData, mutate: persistMutate } = useMutation({
        mutationFn: (payload) => dataProvider.createChat(dagVariation, payload),
    });

    const onSubmit = useCallback((data: ChatFormData) => {
        const finalData = {
            ...data,
            'dag_id': dagVariation,
            'input_field': chatData['input'][0],
            'input_type': chatData['input'][1],
            'output_field': chatData['output'][0],
            'output_type': chatData['output'][1]
        }

        persistMutate(finalData);
    }, [chatData, dagVariation, persistMutate])

    useEffect(() => {
        if (persistMutationData && persistMutationData.id) {
            refresh()
            handleClose()
        }
    }, [handleClose, refresh, persistMutationData])

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Create chat room</DialogTitle>
            <DialogContent>
                <Create>
                    <SimpleForm onSubmit={onSubmit}>
                        <TextInput source={"chat_name"}/>
                    </SimpleForm>
                </Create>
            </DialogContent>
        </Dialog>
    )
}

export default CreateChatForm;
