import { useState } from "react";
import { SendIcon } from "./Icons";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function Composer({ onSend, disabled, placeholder }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <div className="composer-wrap">
      <div className={`composer ${disabled ? "disabled" : ""}`}>
        <label htmlFor="composer-input" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>
          Ask a question about your data
        </label>
        <input
          id="composer-input"
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          disabled={disabled}
          placeholder={placeholder || "Ask a question about your data"}
        />
        <button
          className="send-btn"
          aria-label="Send"
          disabled={disabled || !text.trim()}
          onClick={handleSubmit}
        >
          <SendIcon color={disabled ? "#5A606A" : "#FFFFFF"} />
        </button>
      </div>
      <span className="composer-note">
        Genie writes the SQL, so check the query before you rely on a number.
      </span>
    </div>
  );
}
