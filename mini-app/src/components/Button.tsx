import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "soft" | "ghost";
  children: ReactNode;
};

export const Button = ({
  variant = "primary",
  children,
  className = "",
  ...props
}: ButtonProps) => (
  <button className={`zr-button zr-button-${variant} ${className}`} {...props}>
    {children}
  </button>
);
