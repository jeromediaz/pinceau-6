import simpleRestProvider from "ra-data-simple-rest";
import { fetchUtils } from "react-admin";
import {stringify} from "query-string";

const baseURL =
  document.location.protocol +
  "//" +
  document.location.hostname +
  ":" +
  document.location.port +
  "/api/1.0";

const fetchJson = (url: string, options = {}) => {
  const auth = localStorage.getItem("auth");
  if (auth) {
    const jsonAuth = JSON.parse(auth);
    if (jsonAuth) {
      options.user = {
        authenticated: true,
        token: "Bearer " + jsonAuth["access_token"],
      };
    }
  }

  return fetchUtils.fetchJson(url, options);
};

const baseDataProvider = simpleRestProvider(baseURL, fetchJson);

export const dataProvider = {
  ...baseDataProvider,
  models: (category: string) => {
    return fetchJson(`${baseURL}/models?category=${encodeURIComponent(category)}`).then((res) => res["json"]);
  },
  menu: () => {
    return fetchJson(`${baseURL}/menu`).then((res) => res["json"]);
  },
  resources: () => {
    return fetchJson(`${baseURL}/resources`).then((res) => res["json"]);
  },
  tasksGraph: (graphId: string) => {
    return fetchJson(`${baseURL}/dag/${graphId}/tasks`).then(
      (res) => res["json"],
    );
  },
  dagGraph: (graphId: string) => {
    return fetchJson(`${baseURL}/dag/${graphId}/graph`).then(
      (res) => res["json"],
    );
  },
  graphRequirements: (graphId: string) => {
    return fetchJson(`${baseURL}/dag/${graphId}/run`, {
      method: "GET",
    }).then((res) => res["json"]);
  },
  collectionSchema: (schema: string, mode: string = "default") => {
    let url = `${baseURL}/data/schema/${schema}`
    if (mode != "default") {
      url += '?mode=' + mode
    }

    return fetchJson(url, {
      method: "GET",
    }).then((res) => res["json"]);
  },
  putParams: (graphId: string, payload: object) => {
    const auth = localStorage.getItem("auth");
    const jsonAuth = JSON.parse(auth);
    return fetch(`${baseURL}/dag/${graphId}/parameters`, {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer " + jsonAuth["access_token"],
      },
      body: JSON.stringify(payload),
    }).then((response) => response.json());
  },
  deleteParams: (graphId: string) => {
    const auth = localStorage.getItem("auth");
    const jsonAuth = JSON.parse(auth);
    return fetch(`${baseURL}/dag/${graphId}/parameters`, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer " + jsonAuth["access_token"],
      }
    }).then((response) => response.json());
  },
  runDAG: (graphId: string, payload: object) => {
    const auth = localStorage.getItem("auth");
    const jsonAuth = JSON.parse(auth);
    return fetch(`${baseURL}/dag/${graphId}/run`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer " + jsonAuth["access_token"],
      },
      body: JSON.stringify(payload),
    }).then((response) => response.json());
  },
  createChat: (graphId: string, payload: object) => {
    const auth = localStorage.getItem("auth");
    const jsonAuth = JSON.parse(auth);
    return fetch(`${baseURL}/dag/${graphId}/chats`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer " + jsonAuth["access_token"],
      },
      body: JSON.stringify(payload),
    }).then((response) => response.json())
  },
  persistDAG: (graphId: string, payload: object) => {
    const auth = localStorage.getItem("auth");
    const jsonAuth = JSON.parse(auth);
    return fetch(`${baseURL}/dag/${graphId}/persist`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer " + jsonAuth["access_token"],
      },
      body: JSON.stringify(payload),
    }).then((response) => response.json());
  },
  getMany: (resource, params) => {
    console.log('getMany', {resource, params})

    const hasIdField = params['meta'] && params['meta']['idField']

    const filterObject = hasIdField ? {[params['meta']['idField']]: params.ids} : { 'id': params.ids };

    const query = {
      filter: JSON.stringify(filterObject),
    };
    const url = `${baseURL}/${resource}?${stringify(query)}`;
    return fetchJson(url, { signal: params?.signal }).then(({ json }) => ({
      data: json,
    }));
  },
};
