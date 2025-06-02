import { useState, useEffect } from "react";
import { Input } from "./components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Label } from "./components/ui/label";
import { ArrowLeftIcon, Save } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Checkbox } from "./components/ui/checkbox";

type LLMConfig = {
  models: Record<string, { type?: "text" | "image" | "video" }>;
  url: string;
  api_key: string;
  max_tokens?: number;
};

const PROVIDER_NAME_MAPPING: { [key: string]: { name: string; icon: string } } =
  {
    anthropic: {
      name: "Claude",
      icon: "https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/dark/claude-color.png",
    },
    openai: { name: "OpenAI", icon: "https://openai.com/favicon.ico" },
    replicate: {
      name: "Replicate",
      icon: "https://images.seeklogo.com/logo-png/61/1/replicate-icon-logo-png_seeklogo-611690.png",
    },
    ollama: {
      name: "Ollama",
      icon: "https://images.seeklogo.com/logo-png/59/1/ollama-logo-png_seeklogo-593420.png",
    },
    huggingface: {
      name: "Hugging Face",
      icon: "https://huggingface.co/favicon.ico",
    },
  };
const DEFAULT_CONFIG: { [key: string]: LLMConfig } = {
  anthropic: {
    models: {
      "claude-3-7-sonnet-latest": { type: "text" },
    },
    url: "https://api.anthropic.com/v1/",
    api_key: "",
    max_tokens: 8192,
  },
  openai: {
    models: {
      "gpt-4o": { type: "text" },
      "gpt-4o-mini": { type: "text" },
    },
    url: "https://api.openai.com/v1/",
    api_key: "",
    max_tokens: 8192,
  },
  replicate: {
    models: {
      "google/imagen-4": { type: "image" },
      "black-forest-labs/flux-1.1-pro": { type: "image" },
      "black-forest-labs/flux-kontext-pro": { type: "image" },
      "black-forest-labs/flux-kontext-max": { type: "image" },
      "recraft-ai/recraft-v3": { type: "image" },
      "stability-ai/sdxl": { type: "image" },
    },
    url: "https://api.replicate.com/v1/",
    api_key: "",
    max_tokens: 8192,
  },
  // huggingface: {
  //   models: {
  //     "dreamlike-art/dreamlike-photoreal-2.0": { type: "image" },
  //   },
  //   url: "https://api.replicate.com/v1/",
  //   api_key: "",
  // },
  ollama: {
    models: {},
    url: "http://localhost:11434",
    api_key: "",
    max_tokens: 8192,
  },
};

export default function Settings() {
  const [provider, setProvider] = useState("anthropic");
  const [config, setConfig] = useState<{
    [key: string]: LLMConfig;
  }>(DEFAULT_CONFIG);
  const [isApiKeyDirty, setIsApiKeyDirty] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch("/api/config");
        const config: { [key: string]: LLMConfig } = await response.json();
        setConfig((curConfig) => {
          const res: { [key: string]: LLMConfig } = {};
          for (const provider in DEFAULT_CONFIG) {
            if (config[provider] && typeof config[provider] === "object") {
              res[provider] = {
                ...DEFAULT_CONFIG[provider],
                ...config[provider],
              };
            } else {
              res[provider] = DEFAULT_CONFIG[provider];
            }
          }
          return res;
        });
      } catch (error) {
        console.error("Error loading configuration:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadConfig();
  }, []);

  const handleSave = async () => {
    try {
      setErrorMessage("");

      const response = await fetch("/api/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error("Failed to save configuration");
      }

      const result = await response.json();
      if (result.status === "success") {
        navigate("/");
      } else {
        throw new Error(result.message || "Failed to save configuration");
      }
    } catch (error) {
      console.error("Error saving settings:", error);
      setErrorMessage("Failed to save settings");
      // You might want to show an error message to the user here
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <Button
        onClick={() => navigate("/")}
        className="fixed top-4 left-4"
        size={"icon"}
      >
        <ArrowLeftIcon />
      </Button>
      <Card className="w-full max-w-[800px] shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 pb-26">
          {isLoading && (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-zinc-500"></div>
            </div>
          )}
          {Object.keys(config).map((key, index) => (
            <>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <img
                    src={PROVIDER_NAME_MAPPING[key].icon}
                    alt={PROVIDER_NAME_MAPPING[key].name}
                    className="w-10 h-10 rounded-full"
                  />
                  <p className="font-bold text-2xl w-fit">
                    {PROVIDER_NAME_MAPPING[key].name}
                  </p>
                  {key === "replicate" && <span>🎨 Image Generation</span>}
                </div>
                <Input
                  placeholder="Enter your API URL"
                  value={config[key]?.url ?? ""}
                  onChange={(e) => {
                    setConfig({
                      ...config,
                      [key]: {
                        ...config[key],
                        url: e.target.value,
                      },
                    });
                  }}
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`${key}-apiKey`}>API Key</Label>
                <Input
                  id={`${key}-apiKey`}
                  type="password"
                  placeholder="Enter your API key"
                  value={config[key]?.api_key ?? ""}
                  onChange={(e) => {
                    setConfig({
                      ...config,
                      [key]: { ...config[key], api_key: e.target.value },
                    });
                    setIsApiKeyDirty(true);
                  }}
                  className="w-full"
                />
                <p className="text-xs text-gray-500">
                  Your API key will be stored securely
                </p>
              </div>
              {key !== "replicate" && key !== "huggingface" && (
                <div className="space-y-2">
                  <Label htmlFor={`${key}-maxTokens`}>Max Tokens</Label>
                  <Input
                    id={`${key}-maxTokens`}
                    type="number"
                    placeholder="Enter your max tokens"
                    value={config[key]?.max_tokens ?? 8192}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        [key]: {
                          ...config[key],
                          max_tokens: parseInt(e.target.value),
                        },
                      })
                    }
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500">
                    The maximum number of tokens in the response
                  </p>
                </div>
              )}
              <p>
                Models ({Object.keys(config[key]?.models ?? {}).length ?? 0})
              </p>
              <div className="space-y-2 ml-4">
                {Object.keys({
                  ...DEFAULT_CONFIG[key]?.models,
                  ...config[key]?.models,
                }).map((model) => (
                  <div className="flex items-center gap-3">
                    <Checkbox
                      key={model}
                      id={model}
                      checked={!!config[key]?.models[model]?.type}
                      onCheckedChange={(checked) => {
                        setConfig((prevConfig) => {
                          const newConfig = {
                            ...prevConfig,
                            [key]: structuredClone(prevConfig[key]),
                          };
                          if (checked) {
                            newConfig[key].models[model] =
                              DEFAULT_CONFIG[key].models[model] ??
                              newConfig[key].models[model];
                          } else {
                            delete newConfig[key]?.models[model];
                          }
                          return newConfig;
                        });
                      }}
                    />
                    <Label htmlFor={model}>
                      {model}
                      {config[key]?.models[model]?.type === "image" && (
                        <span>🎨</span>
                      )}
                    </Label>
                  </div>
                ))}
              </div>
              {index !== Object.keys(config).length - 1 && (
                <div className="my-6 border-t bg-border" />
              )}
            </>
          ))}
          <div className="flex justify-center fixed bottom-4 left-1/2 -translate-x-1/2">
            <Button onClick={handleSave} className="w-[400px]" size={"lg"}>
              <Save className="mr-2 h-4 w-4" /> Save Settings
            </Button>
          </div>

          {successMessage && (
            <div className="text-green-500 text-center mb-4">
              {successMessage}
            </div>
          )}
          {errorMessage && (
            <div className="text-red-500 text-center mb-4">{errorMessage}</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
