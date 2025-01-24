import { ErrorInfo, Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import clsx from "clsx";
import { styled } from "@mui/material/styles";
import { LayoutProps } from "react-admin";

import { AppBar as DefaultAppBar } from "ra-ui-materialui";
import { Sidebar as DefaultSidebar } from "ra-ui-materialui";
import { Menu as DefaultMenu } from "ra-ui-materialui";
import { Error as MUIError } from "ra-ui-materialui";
import { SkipNavigationButton } from "ra-ui-materialui";
import { Inspector } from "ra-ui-materialui";
import { Loading } from "ra-ui-materialui";
import P6Breadcrumbs from "./P6Breadcrumbs";

export const P6Layout = (props: LayoutProps) => {
  const {
    appBar: AppBar = DefaultAppBar,
    appBarAlwaysOn,
    children,
    className,
    error: errorComponent,
    menu: Menu = DefaultMenu,
    sidebar: Sidebar = DefaultSidebar,
    ...rest
  } = props;

  const [errorInfo, setErrorInfo] = useState<ErrorInfo | undefined>(undefined);

  const handleError = (error: Error, info: ErrorInfo) => {
    setErrorInfo(info);
  };

  return (
    <Core className={clsx("layout", className)} {...rest}>
      <SkipNavigationButton />
      <div className={LayoutClasses.appFrame}>
        <AppBar alwaysOn={appBarAlwaysOn} />
        <main className={LayoutClasses.contentWithSidebar}>
          <Sidebar appBarAlwaysOn={appBarAlwaysOn}>
            <Menu />
          </Sidebar>
          <div id="main-content" className={LayoutClasses.content}>
            <ErrorBoundary
              onError={handleError}
              fallbackRender={({ error, resetErrorBoundary }) => (
                <MUIError
                  error={error}
                  errorComponent={errorComponent}
                  errorInfo={errorInfo}
                  resetErrorBoundary={resetErrorBoundary}
                />
              )}
            >
              <P6Breadcrumbs />
              <Suspense fallback={<Loading />}>{children}</Suspense>
            </ErrorBoundary>
          </div>
        </main>
        <Inspector />
      </div>
    </Core>
  );
};

export interface LayoutState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

const PREFIX = "RaLayout";
export const LayoutClasses = {
  appFrame: `${PREFIX}-appFrame`,
  contentWithSidebar: `${PREFIX}-contentWithSidebar`,
  content: `${PREFIX}-content`,
};

const Core = styled("div", {
  name: PREFIX,
  overridesResolver: (props, styles) => styles.root,
})(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  zIndex: 1,
  minHeight: "100vh",
  backgroundColor: theme.palette.background.default,
  position: "relative",
  minWidth: "fit-content",
  width: "100%",
  color: theme.palette.getContrastText(theme.palette.background.default),

  [`& .${LayoutClasses.appFrame}`]: {
    display: "flex",
    flexDirection: "column",
    flexGrow: 1,
    marginTop: theme.spacing(6),
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing(7),
    },
  },
  [`& .${LayoutClasses.contentWithSidebar}`]: {
    display: "flex",
    flexGrow: 1,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  [`& .${LayoutClasses.content}`]: {
    backgroundColor: theme.palette.background.default,
    zIndex: 2,
    display: "flex",
    flexDirection: "column",
    flexGrow: 1,
    flexBasis: 0,
    padding: 0,
    [theme.breakpoints.up("xs")]: {
      paddingRight: theme.spacing(1),
      paddingLeft: theme.spacing(1),
    },
  },
}));
