import React, { createContext, ReactNode, useState } from "react";

type TitleMap = {
  [key: string]: string;
};

type TitleMapContext = [
  TitleMap,
  React.Dispatch<React.SetStateAction<TitleMap>>,
];

type TitleContextStoreProps = {
  children: ReactNode;
};

const TitleContext = createContext<TitleMapContext>([{}, () => {}]);

export const TitleContextStore: React.FC<TitleContextStoreProps> = (props) => {
  const state = useState<TitleMap>({});
  return (
    <TitleContext.Provider value={state}>
      {props.children}
    </TitleContext.Provider>
  );
};

export { TitleContext };
