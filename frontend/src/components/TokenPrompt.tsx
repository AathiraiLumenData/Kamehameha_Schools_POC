import { useState } from "react";
import { setToken } from "../api";

interface Props {
  onReady: () => void;
}

export default function TokenPrompt({ onReady }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    setToken(trimmed);
    onReady();
  };

  return (
    <div className="token-screen">
      <h2>Sign in to Databricks</h2>
      <p>
        Paste your Databricks personal access token. It stays in your browser
        and is sent only to your workspace.
      </p>
      <input
        type="password"
        placeholder="dapi..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
      />
      <button onClick={handleSubmit}>Continue</button>
    </div>
  );
}
