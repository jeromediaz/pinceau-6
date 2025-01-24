type StatusColorMap = {
  [key: string]: string;
};

export const dagColors = {
  dark: {
    bgColor: "#182230F7",
    strokeColor: "#FFFFFF",
    status: {
      default: "#FFFFFFB3",
      idle: "#A4ABB6",
      waiting: "#FCE83A",
      running: "#56F000",
      finished: "#2DCCFF",
      warning: "#FFB302",
      error: "#FF3838",
    } as StatusColorMap,
  },
  light: {
    bgColor: "#FFFFFF",
    strokeColor: "#000000",
    status: {
      default: "#00000099",
      idle: "#A4ABB6",
      waiting: "#FCE83A",
      running: "#56F000",
      finished: "#2DCCFF",
      warning: "#FFB302",
      error: "#FF3838",
    } as StatusColorMap,
  },
};
