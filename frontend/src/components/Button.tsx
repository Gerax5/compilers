import React from "react";

type ButtonProps = {
  label: string;
  onClick?: () => void;
  variant?: "primary" | "ghost";
  disabled?: boolean;
  style?: React.CSSProperties;
};

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  variant = "primary",
  disabled,
  style,
}) => {
  const base =
    "px-4 py-2 rounded-lg text-sm font-medium transition-colors border";
  const styles =
    variant === "primary"
      ? "bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
      : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50";

  return (
    <button
      style={{
        paddingLeft: "2vh",
        paddingRight: "2vh",
        justifyContent: "center",
        alignContent: "center",
        alignItems: "center",
        textAlign: "center",
        ...style,
      }}
      className={`${base} ${styles} ${
        disabled ? "opacity-60 cursor-not-allowed" : ""
      }`}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
};
