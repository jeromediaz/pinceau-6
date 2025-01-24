import {
    Admin,
    AppBar,
    BooleanField,
    CustomRoutes,
    LayoutProps,
    ListGuesser,
    Menu,
    Resource,
    ResourceContextProvider,
    ShowGuesser,
    TitlePortal,
    ToggleThemeButton,
    useGetIdentity,
} from "react-admin";
import {authProvider} from "./authProvider";
import SchemaPage from "./SchemaPage";
import {Route} from "react-router-dom";
import {DagShow} from "./features/dag/DAGShow";
import {dataProvider} from "./data-provider";
import SimpleChat from "./features/chat/SimpleChat";
import {DataList} from "./features/data/list/DataList";
import {DataEdit} from "./features/data/edit/DataEdit";
import {DataShow} from "./features/data/show/DataShow";
import {DataCreate} from "./features/data/create/DataCreate";
import React, {ChangeEvent, useCallback, useContext, useEffect, useMemo, useState,} from "react";
import {Box, IconButton, Theme, useMediaQuery,} from "@mui/material";
import {WebSocketContext} from "./context/websocket_context";
import Typography from "@mui/material/Typography";
import Badge from "@mui/material/Badge";
import {DAGList} from "./features/dag/DAGList";
import {P6Layout} from "./P6Layout";
import {TitleContextStore} from "./title_context";
import {ModelObject} from "./types";
import Popover from "@mui/material/Popover";
import NotificationsIcon from "@mui/icons-material/Notifications";
import WorkIcon from "@mui/icons-material/Work";
import TextField from "@mui/material/TextField";
import JobList from "./features/dag/JobList";
import {JobShow} from "./features/dag/JobShow";
import RunningJobs from "./features/dag/RunningJobs";
import P6MenuItem, {containsTaxonomyValue} from "./P6MenuItem";
import SensorsOffIcon from "@mui/icons-material/SensorsOff";
import SensorsIcon from "@mui/icons-material/Sensors";

const DynamicMenu = React.createContext([]);
export const ApplicationFilter = React.createContext([])

interface SocketCallback {
    (data: any): void;
}

type ResourceDefinition = {
    name: string;
    provider: string;
    label: string;
}

const extractResources = (items: any[]) => {
    const resources: ResourceDefinition[] = []

    items.forEach((value) => {
        if (value.type == 'resource-item') {
            resources.push({name: value.name, provider: value.provider, label: value.primaryText})
        } else if (value.type == 'collapse') {
            const subResources = extractResources(value.content)

            resources.push(...subResources)
        }
    })

    return resources;
}


const MyMenu = () => {
    const menu = useContext(DynamicMenu)
    const [taxonomyFilter, setTaxonomyFilter] = useContext(ApplicationFilter)

    return (
        <Menu>
            {menu.map((menuItem, index) => {
                    if ('categories' in menuItem) {
                        if (!containsTaxonomyValue(menuItem['categories'], taxonomyFilter)) {
                            return null
                        }
                    }

                    return <P6MenuItem key={index} {...menuItem} taxonomyFilter={taxonomyFilter} setTaxonomyFilter={setTaxonomyFilter}/>
                }
            )}

        </Menu>
    );
};

const MyAppBar = () => {
    const isLargeEnough = useMediaQuery<Theme>((theme) =>
        theme.breakpoints.up("sm"),
    );
    const socket = useContext(WebSocketContext);
    const [isConnected, setIsConnected] = useState(socket.connected);
    const [runCount, setRunCount] = useState(0);
    const {data: userData} = useGetIdentity();
    const [anchorEl, setAnchorEl] = React.useState<HTMLButtonElement | null>(
        null,
    );

    const connectedRecord = useMemo(() => {
        return {connected: isConnected};
    }, [isConnected]);

    const handleClick = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    }, []);

    const handleClose = useCallback(() => {
        setAnchorEl(null);
    }, []);

    useEffect(() => {
        if (runCount === 0) {
            setAnchorEl(null);
        }
    }, [runCount]);

    const open = Boolean(anchorEl);
    const id = open ? "simple-popover" : undefined;

    useEffect(() => {
        if (socket.connected && userData) {
            // TODO:
            socket.emit("subscribe_running_dag_count", {uid: userData.id});
        }

        function onRunningDagCount(count: number) {
            setRunCount(count);
        }

        function onConnect() {
            setIsConnected(true);
            if (userData) {
                socket.emit("subscribe_running_dag_count", {uid: userData.id});
            }
        }

        function onDisconnect() {
            setIsConnected(false);
        }

        socket.on("connect", onConnect);
        socket.on("disconnect", onDisconnect);
        socket.on("runningDagCount", onRunningDagCount);

        return () => {
            socket.off("connect", onConnect);
            socket.off("disconnect", onDisconnect);
            socket.off("runningDagCount", onRunningDagCount);
            if (userData) {
                socket.emit("unsubscribe_running_dag_count", {uid: userData.id});
            }
        };
    }, [socket, userData]);

    return (
        <AppBar toolbar={<ToggleThemeButton/>}>
            <TitlePortal/>
            {isLargeEnough && (
                <Typography variant="h6" component="div">
                    P6
                </Typography>
            )}
            {isLargeEnough && <Box component="span" sx={{flex: 1}}/>}
            <NotificationsIcon/>
            <BooleanField
                record={connectedRecord}
                source="connected"
                FalseIcon={SensorsOffIcon}
                TrueIcon={SensorsIcon}
            />
            <IconButton
                variant="contained"
                onClick={handleClick}
                disabled={runCount === 0}>
                <Badge badgeContent={runCount} color="secondary">
                    <WorkIcon/>
                </Badge>
            </IconButton>

            <Popover
                id={id}
                open={open}
                anchorEl={anchorEl}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "left",
                }}
            >
                <RunningJobs runCount={runCount}/>
            </Popover>
        </AppBar>
    );
};

const MyLayout = (props: LayoutProps) => (
    <P6Layout {...props} menu={MyMenu} appBar={MyAppBar}/>
);

let apiUrl =
    document.location.protocol +
    "//" +
    document.location.hostname +
    ":" +
    document.location.port;
const myAuthProvider = authProvider(`${apiUrl}/api/1.0`);

export const App = () => {
    const websocket = useContext(WebSocketContext);
    const [menu, setMenu] = useState([]);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [taxonomyFilter, setTaxonomyFilter] = useState('/');

    useEffect(() => {
        myAuthProvider.setLoginCallback(setIsLoggedIn)
    }, []);

    useEffect(() => {
        if (!isLoggedIn) {
            return
        }
        dataProvider.menu().then(setMenu)
    }, [isLoggedIn])

    const resources = useMemo(() => {
        return extractResources(menu)
    }, [menu]);

    useEffect(() => {
        if (websocket.connected) {
            // socket already connected
            console.log("websocket already connected");
        } else {
            websocket.connect()
            console.log("websocket not connected");
        }

        function onConnect() {
            console.log("App OnConnect");
        }

        function onAuthChallenge(cbk: SocketCallback) {
            console.log("onAuthChallenge");
            const authValue = localStorage.getItem("auth");
            let cbkCalled = false;
            if (authValue) {
                const authToken = JSON.parse(authValue);
                if (authToken && "access_token" in authToken) {
                    cbk(authToken["access_token"]);
                    cbkCalled = true;
                }
            }
            if (!cbkCalled) {
                cbk("");
            }
            console.log("-----");
        }

        websocket.on("connect", onConnect);
        websocket.on("authChallenge", onAuthChallenge);

        return () => {
            websocket.off("connect", onConnect);
            websocket.off("authChallenge", onAuthChallenge);
        };
    }, [websocket]);

    const recordRepresentation = useCallback((record: ModelObject) => {
        const record_meta = record._meta;
        if (record_meta && record_meta.label) return record_meta.label;
        if (record_meta && record_meta.model) return `${record_meta.model}#${record.id}`;
        return record.id;
    }, []);

    return (
        <DynamicMenu.Provider value={menu}>
            <ApplicationFilter.Provider value={[taxonomyFilter, setTaxonomyFilter]}>
                <TitleContextStore>
                    <Admin
                        disableTelemetry
                        title="Pinceau6"
                        dashboard={SchemaPage}
                        dataProvider={dataProvider}
                        authProvider={myAuthProvider}
                        layout={MyLayout}
                        darkTheme={{palette: {mode: "dark"}}}
                    >
                        <Resource name="jobs" list={JobList} show={DagShow}/>

                        {resources.map(({name, label, provider}) => {
                            if (provider == 'elastic') {
                                return (
                                    <Resource
                                        key={name}
                                        name={`data/${provider}/${name}`}
                                        list={ListGuesser}
                                        show={ShowGuesser}
                                        options={{label}}
                                        recordRepresentation={recordRepresentation}
                                    />
                                )
                            }

                            return (
                                <Resource
                                    key={name}
                                    name={`data/${provider}/${name}`}
                                    list={DataList}
                                    edit={DataEdit}
                                    show={DataShow}
                                    create={DataCreate}
                                    options={{label}}
                                    recordRepresentation={recordRepresentation}
                                >
                                    <Route path=":id/chat/:dag_id"
                                           element={<DataList schema={"chat_dag_for_object"}/>}/>
                                    <Route path=":id/chat/:dag_id/create" element={<DataCreate/>}/>
                                    <Route path=":id/chat/:dag_id/chat/:chat_id" element={<SimpleChat/>}/>
                                </Resource>
                            );
                        })}
                        <CustomRoutes>
                            <Route path="/chat/:chat_id" element={<SimpleChat/>}/>
                            <Route
                                path="/dag"
                                element={
                                    <ResourceContextProvider value={"dag"}>
                                        <DAGList/>
                                    </ResourceContextProvider>
                                }
                            />
                            <Route
                                path="/dag/:id/:variant/show/*"
                                element={
                                    <ResourceContextProvider value={"dag"}>
                                        <DagShow/>
                                    </ResourceContextProvider>
                                }
                            />
                            <Route
                                path="/dag/:id/:variant/show/jobs/:jobId"
                                element={<JobShow/>}
                            />
                        </CustomRoutes>
                    </Admin>
                </TitleContextStore>
            </ApplicationFilter.Provider>
        </DynamicMenu.Provider>
    );
};
