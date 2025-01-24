import React, {useCallback, useContext, useMemo, useState} from "react";
import Icon from "@mui/material/Icon";
import {Menu} from "react-admin";
import MenuItem from "@mui/material/MenuItem";
import {List, ListItemButton, ListItemIcon, ListItemText} from "@mui/material";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import Collapse from "@mui/material/Collapse";
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import {ApplicationFilter} from "./App";

type MenuItemProps = {
  type: string
  to?: string
  primaryText?: string
  leftIcon?: string
  rightIcon?: string[]
  content?: any[]
  provider?: string
  name?: string
  taxonomyFilter: string;
  setTaxonomyFilter?: (value: string) => void;
  categories?: string[];
  choices?: any
}

export const containsTaxonomyValue = (categories, taxonomyFilter) => {
  for (const resourceCategory of categories) {
    if (resourceCategory && resourceCategory.startsWith(taxonomyFilter)) {
      return true;
    }
  }

  return false;
}

const P6MenuItem: React.FC<MenuItemProps> = (props) => {
  const {choices, categories, taxonomyFilter, setTaxonomyFilter, type, to, primaryText, leftIcon, rightIcon, content, provider, name} = props;
  const [displayContent, setDisplayContent] = useState(false);


  const LeftIcon = useMemo(() => {
    if (!leftIcon) {
      return undefined;
    }
    return <Icon>{leftIcon}</Icon>
  }, [leftIcon]);

  const handleCollapseMenu = useCallback(() => {
    setDisplayContent(prevState => !prevState)
  }, [])

  const endIcon = useMemo(() => {
    if (!rightIcon) {
      return undefined;
    }
    const usedIcon = displayContent ? rightIcon[1] : rightIcon[0]
    return <Icon>{usedIcon}</Icon>

  }, [rightIcon, displayContent])

  const onApplicationChange = useCallback((event) => {
    if (setTaxonomyFilter) {
      setTaxonomyFilter(event.target.value);
    }
  }, [setTaxonomyFilter])

  if (type == 'application_selector') {
    return (
      <FormControl fullWidth>
        <InputLabel id="application-select-label">Application</InputLabel>
        <Select
            labelId="application-select-label"
            id="application-select"
            value={taxonomyFilter}
            label="Application"
            onChange={onApplicationChange}
        >
          <MenuItem value={"/"}>-</MenuItem>

          {Object.entries(choices).map(([key, name]) => {
            return (<MenuItem value={key} key={key}>{name}</MenuItem>)
          })}

        </Select>
      </FormControl>
    )
  }
  else if (type == 'dashboard') {
    return <Menu.DashboardItem/>
  } else if (type == 'item') {
      return <Menu.Item to={to} primaryText={primaryText} leftIcon={LeftIcon}/>

  } else if (type == 'resource-item') {
    const to = `/data/${provider}/${name}`

    return <Menu.Item to={to} primaryText={primaryText} leftIcon={LeftIcon}/>

  } else if (type == 'collapse') {
    return (
        <>
          <MenuItem onClick={handleCollapseMenu}>
              <ListItemIcon sx={{ minWidth: "40px !important" }}>
                <FormatListBulletedIcon />
              </ListItemIcon>
              <ListItemText sx={{ color: "text.secondary" }}>{primaryText}</ListItemText>
              {endIcon}
            </MenuItem>

            <List disablePadding={true} className={"MuiMenuItem-root"}>
              <Collapse in={displayContent} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {displayContent &&
                    content.map(( contentProps ) => {
                      if (contentProps.categories && !containsTaxonomyValue(contentProps.categories, taxonomyFilter)) {
                        return null;
                      }

                      return (
                        <ListItemButton key={contentProps['name']} sx={{ pl: 4 }} dense={true}>
                          <P6MenuItem {...contentProps} />
                        </ListItemButton>
                      );
                    })}
                </List>
              </Collapse>
            </List>
        </>
      )
  }

  return null;

}

export default P6MenuItem
