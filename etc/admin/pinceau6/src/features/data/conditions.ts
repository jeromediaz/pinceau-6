import { useWatch } from "react-hook-form";

function useProcessFieldValidation(
  parentSource: string,
  path: string,
  data: unknown,
) {
  const workPath = parentSource ? `${parentSource}.${path}` : path;
  const workValue = useWatch({ name: workPath });
  let comparison = "$eq";
  let value = data;
  if (typeof data === "object" && !Array.isArray(value)) {
    const valueKeys = Object.keys(value);
    if (valueKeys.length == 1) {
      comparison = valueKeys[0];
      value = data[comparison];
    }
  }

  if (comparison === "$eq") {
    return workValue === value;
  } else if (comparison === "$gt") {
    return workValue > value;
  } else if (comparison === "$gte") {
    return workValue >= value;
  } else if (comparison === "$in") {
    return value.indexOf(workValue) !== -1;
  } else if (comparison === "$lt") {
    return workValue < value;
  } else if (comparison === "$lte") {
    return workValue < value;
  } else if (comparison === "$ne") {
    return workValue !== value;
  } else if (comparison === "$nin") {
    return value.indexOf(workValue) === -1;
  } else if (comparison === "$exists") {
    if (value) {
      return workValue !== undefined;
    }
    return workValue === undefined;
  } else if (comparison === "$include") {
    return (workValue || []).indexOf(value) !== -1;
  } else if (comparison === "$exclude") {
    return (workValue || []).indexOf(value) === -1;
  }
}

export const useProcessValidation = (
  parentSource: string,
  condition: object | undefined,
  mode: "$or" | "$and" = "$and",
): boolean => {
  if (!condition) {
    return true;
  }

  if (typeof condition !== "object") {
    return false;
  }

  if ("$and" in condition) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return useProcessValidation(parentSource, condition["$and"], "$AND");
  } else if ("$or" in condition) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return useProcessValidation(parentSource, condition["$or"], "$OR");
  }

  if (mode === "$and") {
    let result = true;
    for (const [key, value] of Object.entries(condition)) {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      if (!useProcessFieldValidation(parentSource, key, value)) {
        result = false;
      }
    }
    return result;
  } else {
    let result = false;
    for (const [key, value] of Object.entries(condition)) {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      if (useProcessFieldValidation(parentSource, key, value)) {
        result = true;
      }
    }
    return result;
  }
};
