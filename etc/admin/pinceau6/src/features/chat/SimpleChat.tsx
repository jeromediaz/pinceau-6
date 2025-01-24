import {useCallback, useContext, useEffect, useRef, useState} from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import {Title, useDataProvider, useGetIdentity, UserIdentity} from "react-admin";
import "react-chat-elements/dist/main.css";
import { v4 as uuidv4 } from "uuid";
import { Button, Input, MessageList } from "react-chat-elements";
import { useParams } from "react-router-dom";
import { WebSocketContext } from "../../context/websocket_context";
import {TitleContext} from "../../title_context";
import {useLocation} from "react-router";
import Markdown from 'react-markdown'

type Character = UserIdentity & {
  avatar: string;
  display_name: string;
};

type CharacterMap = {
  [key: string]: Character;
};

let clearRef = () => {};

function useForceUpdate() {
  const [value, setValue] = useState(0);
  return () => setValue(() => value + 1);
}

type UUIDIndexMap = {
  [key: string]: number;
};

const SimpleChat = () => {
  const location = useLocation();
  const websocket = useContext(WebSocketContext);
  const agentMap = useRef<CharacterMap>({});
  const dataProvider = useDataProvider();
  const { data: userData } = useGetIdentity();
  const [isConnected, setIsConnected] = useState(websocket.connected);
  const { chat_id: chatId } = useParams();
  const [titleContext, setTitleContext] = useContext(TitleContext);

  const [messageListArray, setMessageListArray] = useState<any>([]);
  const forceUpdate = useForceUpdate();
  const inputReference = useRef<Input>();

  const uuidToIndexMap = useRef<UUIDIndexMap>({});

  useEffect(() => {
    dataProvider
        .getOne('data/mongodb/chat', { id: chatId })
        .then(response => {
            if (response && response.data) {
              const record = response.data;
              const titlePath = location.pathname;
              if (titleContext[titlePath] !== record._meta.label) {
                setTitleContext({ ...titleContext, [titlePath]: record._meta.label });
              }
            }
           // { id: 123, title: "hello, world" }
        });
  }, [chatId, dataProvider, setTitleContext, titleContext, location.pathname]);

  useEffect(() => {
    if (!userData) {
      return;
    }

    if (websocket.connected) {
      websocket.emit("enter_chat_room", {
        chat_id: chatId,
        user_id: userData.id,
      });
      setIsConnected(true);
    } else {
      console.log('websocket connect')
      websocket.connect();
    }

    function onConnect() {
      websocket.emit("enter_chat_room", {
        chat_id: chatId,
        user_id: userData.id,
      });
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onChatResponse(payload: any) {
      if ("payload" in payload) {
        payload = payload["payload"];
      }
      const { messages, agents } = payload;
      if (agents) {
        agentMap.current = agents;
      }

      setMessageListArray((currentList: any[]) => {
        const messageCount = messages.length;
        for (
          let messageIndex = 0;
          messageIndex < messageCount;
          messageIndex++
        ) {
          const message = messages[messageIndex];
          let character: UserIdentity | undefined = undefined;
          const from_user = message["from_user"];
          if (from_user && from_user.startsWith("agent:")) {
            const agent_name = from_user.substring(6);

            character = agentMap.current[agent_name] || {};
          } else if (from_user === "user") {
            // TODO: handle multiple human user
            character = userData;
          }

          let chatMessage =
            currentList[uuidToIndexMap.current[message["uuid"]]];

          if (!chatMessage) {
            chatMessage = {
              //titleColor: 'blue'
              className: ''
            };
            currentList.push(chatMessage);
            uuidToIndexMap.current[message["uuid"]] = currentList.length;
          }

          chatMessage.type = message.type;
          chatMessage.text = <Markdown>{message.text}</Markdown>;
          chatMessage.position = message.position;

          if (message.type == "photo") {
            chatMessage.data = { uri: message.uri };
          } else {
            chatMessage.data = {};
          }
          chatMessage.status = message.status || undefined;
          chatMessage.date = message.date;

          if (character) {
            chatMessage.title = character["display_name"];
            chatMessage.avatar = character["avatar"];
          }
        }

        return [...currentList];
      });
    }

    websocket.on("connect", onConnect);
    websocket.on("disconnect", onDisconnect);
    websocket.on("chatResponse", onChatResponse);

    return () => {
      websocket.off("connect", onConnect);
      websocket.off("disconnect", onDisconnect);
      websocket.off("chatResponse", onChatResponse);
      websocket.emit("leave_chat_room", { chat_id: chatId });
    };
  }, [chatId, userData, websocket]);

  const addMessage = useCallback(() => {
    console.log("addMessage", userData);
    if (!userData) {
      return;
    }

    const uuid_value = uuidv4();

    uuidToIndexMap.current[uuid_value] = messageListArray.length;

    setMessageListArray([
      ...messageListArray,
      {
        position: "right",
        type: "text",
        title: userData["display_name"],
        avatar: userData["avatar"],
        text: <Markdown>{inputReference.current?.value}</Markdown>,
        uuid: uuid_value,
        //titleColor: 'red',
      },
    ]);
    if (websocket.connected) {
      websocket.emit("chatMessage", {
        chat_id: chatId,
        user_id: userData.id,
        uuid: uuid_value,
        message: inputReference.current?.value,
      });
    }
    clearRef();
    forceUpdate();
  }, [
    chatId,
    forceUpdate,
    messageListArray,
    inputReference,
    userData,
    websocket,
  ]);

  const inputOnKeyPress = useCallback(
    (e: any) => {
      if (!isConnected) {
        // we can't send if we are not connected
        return;
      }
      if (e.shiftKey && e.charCode === 13) {
        return true;
      }
      if (e.charCode === 13) {
        addMessage();
        clearRef();
      }
    },
    [addMessage, isConnected],
  );

  return (
    <Card>
      <Title title="Chat" />
      <CardContent style={{ "flex-grow": 1 }}>
        <MessageList
          className="message-list"
          lockable={true}
          toBottomHeight={"100%"}
          dataSource={messageListArray}
        />
        <Input
          referance={inputReference}
          placeholder="Type here..."
          clear={(clear: any) => (clearRef = clear)}
          multiline={false}
          onKeyPress={inputOnKeyPress}
          rightButtons={
            <Button
              text="Submit"
              onClick={addMessage}
              disabled={!isConnected}
            />
          }
        />
      </CardContent>
    </Card>
  );
};

export default SimpleChat;
