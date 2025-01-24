import useBreadcrumbs from "use-react-router-breadcrumbs";
import React, {useContext, useMemo} from "react";
import {Link as RouterLink} from "react-router-dom";
import Typography from "@mui/material/Typography";
import {TitleContext} from "./title_context";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import Link, {LinkProps} from "@mui/material/Link";

interface LinkRouterProps extends LinkProps {
    to: string;
    replace?: boolean;
}

function LinkRouter(props: LinkRouterProps) {
    return <Link {...props} component={RouterLink as any}/>;
}

const P6Breadcrumbs = () => {
    const breadcrumbs = useBreadcrumbs(undefined, {
        excludePaths: ["data/", "data/mongodb", "data/elastic"],
    });
    const [titleContext] = useContext(TitleContext);

    const breadcrumbList = useMemo(() => {
        const results: React.ReactNode[] = []

        let lastWasDagList = false
        let lastWasDag = false
        let lastWasVariation = false
        let lastWasDagShow = false

        breadcrumbs.forEach(({match, breadcrumb, key}, index, array) => {
            if (!breadcrumb || !("props" in breadcrumb)) {
                return
            }

            const isLast = index == array.length - 1

            let isTextOnly = lastWasDagList || isLast
            let isIgnored = lastWasDag || lastWasVariation


            if (lastWasVariation) {
                const {breadcrumb: previousBreadcrumb} = array[index - 1]

                if (isLast) {

                    results.push(
                        <Typography color="inherit">
                            {titleContext[breadcrumb.key]
                                ? titleContext[breadcrumb.key]
                                : previousBreadcrumb.props.children}
                        </Typography>
                    )
                } else {
                    results.push(
                        <LinkRouter
                            underline="hover"
                            color="inherit"
                            to={match.pathname}
                            key={match.pathname}
                        >
                            {titleContext[key] ? titleContext[key] : previousBreadcrumb.props.children}
                        </LinkRouter>
                    )
                }
            }

            if (!isIgnored) {
                if (isTextOnly) {
                    results.push(
                        <Typography color="inherit">
                            {titleContext[breadcrumb.key]
                                ? titleContext[breadcrumb.key]
                                : breadcrumb.props.children}
                        </Typography>
                    )
                } else {
                    results.push(
                        <LinkRouter
                            underline="hover"
                            color="inherit"
                            to={match.pathname}
                            key={match.pathname}
                        >
                            {titleContext[key] ? titleContext[key] : breadcrumb.props.children}
                        </LinkRouter>
                    )
                }
            }

            lastWasDagShow = lastWasVariation
            lastWasVariation = lastWasDag
            lastWasDag = lastWasDagList
            lastWasDagList = match.pathname == '/dag'

        })

        return results


    }, [breadcrumbs, titleContext])

    return (
        <Breadcrumbs aria-label="breadcrumb" sx={{padding: "8px"}}>
            {breadcrumbList}
        </Breadcrumbs>
    );
};

export default P6Breadcrumbs;
