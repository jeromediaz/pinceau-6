import { useMeasure } from "@uidotdev/usehooks";
import React, { useMemo } from "react";
import { useMediaQuery, Theme } from "@mui/material";

type SizeMap = {
  [key: string]: number;
};

type SizeObject = SizeMap & {
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
};

type AspectRatioProps = {
  ratio: number | SizeObject;
  priority: "horizontal" | "vertical";
  children: React.ReactElement;
  maxHeight?: number | SizeObject;
  maxWidth?: number | SizeObject;
};

const testValues = ["xs", "sm", "md", "lg", "xl"];

const useBreakPointValues = (): boolean[] => {
  return [
    useMediaQuery<Theme>((theme) => theme.breakpoints.down("xs")),
    useMediaQuery<Theme>((theme) => theme.breakpoints.down("sm")),
    useMediaQuery<Theme>((theme) => theme.breakpoints.down("md")),
    useMediaQuery<Theme>((theme) => theme.breakpoints.down("lg")),
    useMediaQuery<Theme>((theme) => theme.breakpoints.down("xl")),
  ];
};

export const AspectRatio: React.FC<AspectRatioProps> = ({
  ratio,
  priority = "horizontal",
  children,
  maxHeight,
  maxWidth,
}) => {
  const [ref, { width, height }] = useMeasure();

  const breakPointValues = useBreakPointValues();

  const usedRatio = useMemo(() => {
    if (typeof ratio === "number") {
      return ratio;
    }

    let lastFindValue: number = 1.0;
    let breakpointCount = testValues.length;
    for (let i = 0; i < breakpointCount; i++) {
      const breakpoint = testValues[i];
      if (breakpoint in ratio) {
        lastFindValue = ratio[breakpoint];
      }
      if (breakPointValues[i]) {
        break;
      }
    }
    return lastFindValue;
  }, [breakPointValues, ratio]);

  const usedMaxHeight = useMemo(() => {
    if (maxHeight === undefined) {
      return undefined;
    }

    if (typeof maxHeight === "number") {
      return maxHeight;
    }

    let lastFindValue: number = 1.0;
    let breakpointCount = testValues.length;
    for (let i = 0; i < breakpointCount; i++) {
      const breakpoint = testValues[i];
      if (breakpoint in maxHeight) {
        lastFindValue = maxHeight[breakpoint];
      }
      if (breakPointValues[i]) {
        break;
      }
    }
    return lastFindValue;
  }, [breakPointValues, maxHeight]);

  const usedMaxWidth = useMemo(() => {
    if (maxWidth === undefined) {
      return undefined;
    }

    if (typeof maxWidth === "number") {
      return maxWidth;
    }

    let lastFindValue: number = 1.0;
    let breakpointCount = testValues.length;
    for (let i = 0; i < breakpointCount; i++) {
      const breakpoint = testValues[i];
      if (breakpoint in maxWidth) {
        lastFindValue = maxWidth[breakpoint];
      }
      if (breakPointValues[i]) {
        break;
      }
    }
    return lastFindValue;
  }, [breakPointValues, maxWidth]);

  const [computedWidth, computedHeight] = useMemo(() => {
    const returnedHeight = height === null ? undefined : height;
    const returnedWidth = width === null ? undefined : width;

    if (priority == "horizontal") {
      if (returnedWidth === undefined) {
        return [undefined, returnedHeight];
      }

      return [returnedWidth, returnedWidth / usedRatio];
    } else if (priority == "vertical") {
      if (returnedHeight === undefined) {
        return [undefined, returnedWidth];
      }
      return [returnedHeight * usedRatio, returnedHeight];
    }

    return [undefined, undefined];
  }, [usedRatio, priority, height, width]);

  const [finalWidth, finalHeight] = useMemo(() => {
    if (usedMaxWidth === undefined && usedMaxHeight === undefined) {
      return [computedWidth, computedHeight];
    }

    let widthExceeded = 1.0;
    if (
      usedMaxWidth !== undefined &&
      computedWidth &&
      computedWidth > usedMaxWidth
    ) {
      widthExceeded = computedWidth / usedMaxWidth;
    }

    let heightExceeded = 1.0;
    if (
      usedMaxHeight !== undefined &&
      computedHeight &&
      computedHeight > usedMaxHeight
    ) {
      heightExceeded = computedHeight / usedMaxHeight;
    }

    if (widthExceeded == 1 && heightExceeded == 1) {
      return [computedWidth, computedHeight];
    }

    if (widthExceeded > heightExceeded) {
      // @ts-ignore
      return [usedMaxWidth, usedMaxWidth / usedRatio];
    } else {
      // @ts-ignore
      return [usedMaxHeight * usedRatio, usedMaxHeight];
    }
  }, [computedWidth, computedHeight, usedMaxWidth, usedMaxHeight, usedRatio]);

  return (
    <div ref={ref}>
      <div style={{ width: finalWidth, height: finalHeight }}>{children}</div>
    </div>
  );
};
