import React from "react";
import Editor from "@monaco-editor/react";

type Props = {
  value: string;
  onChange: (code: string) => void;
};

export const EditorPanel: React.FC<Props> = ({ value, onChange }) => {
  return (
    <Editor
      height="100%"
      defaultLanguage="java"
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      options={{
        minimap: { enabled: true, showSlider: "mouseover" },
        fontSize: 14,
        tabSize: 2,
        automaticLayout: true,
        scrollBeyondLastLine: false,
      }}
    />
  );
};
