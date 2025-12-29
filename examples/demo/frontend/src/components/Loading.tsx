interface LoadingProps {
  className?: string;
  size?: "xs" | "sm" | "md" | "lg";
  text?: string;
}

export function Loading({ className = "", size = "md", text }: LoadingProps) {
  const sizeClass = {
    xs: "loading-xs",
    sm: "loading-sm",
    md: "loading-md",
    lg: "loading-lg",
  }[size];

  return (
    <div className={`flex flex-col items-center justify-center gap-2 p-8 ${className}`}>
      <span className={`loading loading-spinner ${sizeClass} text-primary`}></span>
      {text && <span className="text-sm text-base-content/60">{text}</span>}
    </div>
  );
}
