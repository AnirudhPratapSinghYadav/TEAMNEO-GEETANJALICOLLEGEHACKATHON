"use client";

import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
}

export function Button({
  children,
  className,
  variant = "default",
  size = "md",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:opacity-50 disabled:pointer-events-none",
        {
          "bg-indigo-600 text-white hover:bg-indigo-500": variant === "default",
          "border border-[#1e1e2e] bg-transparent text-slate-300 hover:bg-[#1e1e2e]": variant === "outline",
          "bg-transparent text-slate-400 hover:bg-[#1e1e2e] hover:text-slate-300": variant === "ghost",
          "bg-red-600 text-white hover:bg-red-500": variant === "destructive",
        },
        {
          "h-8 px-3 text-xs": size === "sm",
          "h-9 px-4 text-sm": size === "md",
          "h-11 px-6 text-base": size === "lg",
        },
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
