import React from "react";

import { io } from "socket.io-client";

let socketUri =
  document.location.protocol +
  "//" +
  document.location.hostname +
  ":" +
  document.location.port;

const socket = io(socketUri, { transports: ["websocket", "polling"] });

socket.on("connect_error", () => {
  // revert to classic upgrade
  console.log("socket io fallback to classic upgrade");
  socket.io.opts.transports = ["polling", "websocket"];
});

export const WebSocketContext = React.createContext(socket);
