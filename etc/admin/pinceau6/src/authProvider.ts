import { AuthProvider, HttpError } from "react-admin";

type LoginParams = {
  username: string;
  password: string;
};

export const authProvider: (url: string) => AuthProvider = (
  apiBaseUrl: string,
) => {
  const provider = {
    loginCallback: (isLoggedIn: boolean) => {

    },
    setLoginCallback: (callback: (isLoggedIn: boolean) => void) => {
      provider.loginCallback = callback;

      const authString = localStorage.getItem("auth");
      if (authString && !!JSON.parse(authString)) {
        callback(true)
      } else {
        callback(false);
      }
    },
    login: async ({ username, password }: LoginParams) => {
      const request = new Request(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        body: JSON.stringify({
          login: username,
          password,
        }),
        credentials: "include",
        headers: new Headers({ "Content-Type": "application/json" }),
      });

      const response = await fetch(request);
      if (response.status < 200 || response.status >= 300) {
        throw new Error(response.statusText);
      }
      const { status, data } = await response.json();
      if (status === "OK") {
        console.log("setting localStorage");
        localStorage.setItem("auth", JSON.stringify(data));
        localStorage.setItem("user", "");
        if (provider.loginCallback) {
          provider.loginCallback(true)
        }
      }
    },
    logout: () => {
      if (provider.loginCallback) {
        provider.loginCallback(false)
      }
      localStorage.removeItem("auth");
      localStorage.removeItem("user");
      return Promise.resolve();
    },
    checkAuth: async () => {
      const authString = localStorage.getItem("auth");
      if (!authString) {
        throw new HttpError("", 401);
      }
      const auth = JSON.parse(authString);
      if (!auth) {
        throw new HttpError("", 401);
      }

      if (provider.loginCallback) {
        provider.loginCallback(true)
      }
    },
    checkError: (error) => {
      const status = error.status;
      if (status === 401 || status === 403) {
        return Promise.reject();
      }
      // other error code (404, 500, etc): no need to log out
      return Promise.resolve();
    },
    getPermissions: () => {
      return Promise.resolve(undefined);
    },
    getIdentity: async () => {
      const authString = localStorage.getItem("auth");
      if (!authString) {
        return;
      }

      const auth = JSON.parse(authString);
      if (!auth) {
        return;
      }
      const { access_token } = auth;
      const request = new Request(`${apiBaseUrl}/users/me`, {
        method: "GET",
        headers: new Headers({
          "Content-Type": "application/json",
          Authorization: "Bearer " + access_token,
        }),
      });

      const response = await fetch(request);
      if (response.status < 200 || response.status >= 300) {
        throw new Error(response.statusText);
      }
      const { status, data } = await response.json();
      if (status !== "OK") {
        throw new HttpError("KO", "KO");
      }

      localStorage.setItem("user", JSON.stringify(data));

      const persistedUser = localStorage.getItem("user");
      const user = persistedUser ? JSON.parse(persistedUser) : null;

      return Promise.resolve(user);
    },
  };

  return provider;
};

export default authProvider;
