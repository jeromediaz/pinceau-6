export type GridItemConfig = {
    xs?: number;
    sm?: number;
};

export type SourceType =
    | "bool"
    | "select"
    | "group"
    | "text"
    | "url"
    | "email"
    | "float"
    | "int"
    | "reference"
    | "time"
    | "datetime"
    | "date"
    | "model"
    | "graphviz_dot"
    | "secretstr";

export enum FieldOpts {
    fullWidth = "fullWidth",
    multiline = "multiline",
    inline = "inline",
    grid = "grid",
}

export type NoSourceConcreteField = {
    label?: string;
    type: SourceType;
    grid?: GridItemConfig;
    opts: Array<FieldOpts>;
    fields?: Array<ConcreteField>;
    multiple?: boolean;
    optional?: boolean;
    condition?: any;
    defaultValue?: any;
    reference?: string;
    model?: string;
};

export type NamedSubField = NoSourceConcreteField & {
    name: string;
    multiline?: boolean;
    fullWidth?: boolean;
    type?: SourceType;
    label?: string;
    helperText?: string;
    readOnly?: boolean;
    disabled?: boolean;
    step?: number;
    min?: number;
    max?: number;
    filter?: object;
};

export type ConcreteField = NoSourceConcreteField & {
    source: string;
};
