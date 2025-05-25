import React, { useEffect, useRef, useState } from "react";
import {
  EAgentState,
  Message,
  MessageContent,
  MessageGroup,
  ToolCall,
} from "./types/types";
import { Button } from "./components/ui/button";
import {
  ChevronDownIcon,
  ChevronUpIcon,
  Link,
  MoonIcon,
  PlusIcon,
  SendIcon,
  SettingsIcon,
  SidebarIcon,
  SquareIcon,
  StopCircleIcon,
  SunIcon,
} from "lucide-react";
import { Badge } from "./components/ui/badge";
import { Textarea } from "./components/ui/textarea";
import { nanoid } from "nanoid";
import { Markdown } from "./components/Markdown";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import MultiChoicePrompt from "./MultiChoicePrompt";
import SingleChoicePrompt from "./SingleChoicePrompt";
import Spinner from "./components/ui/Spinner";
import { useTheme } from "./components/theme-provider";
import { PLATFORMS_CONFIG } from "./platformsConfig";

const FOOTER_HEIGHT = 100; // Keep this as minimum height
const MAX_INPUT_HEIGHT = 300; // Add this for maximum input height

const ChatInterface = ({
  sessionId,
  onClickNewChat,
  editorContent,
  editorTitle,
  setAISuggestion,
}: {
  sessionId: string;
  editorTitle: string;
  editorContent: string;
  onClickNewChat: () => void;
  setAISuggestion: (suggestion: string | null) => void;
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [disableStop, setDisableStop] = useState(false);
  const [pending, setPending] = useState(false);
  const { setTheme, theme } = useTheme();
  const [model, setModel] = useState<{
    provider: string;
    model: string;
    url: string;
  }>();
  const [modelList, setModelList] = useState<
    {
      provider: string;
      model: string;
      url: string;
    }[]
  >([]);
  const webSocketRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>(nanoid());
  const [expandingToolCalls, setExpandingToolCalls] = useState<string[]>([]);

  useEffect(() => {
    sessionIdRef.current = sessionId;

    fetch("/api/chat_session/" + sessionId)
      .then((resp) => resp.json())
      .then((data) => {
        if (data?.length) {
          setMessages(data);
        } else {
          setMessages([]);
        }
        console.log("👇messages", data);
      });
  }, [sessionId]);

  useEffect(() => {
    fetch("/api/list_models")
      .then((resp) => resp.json())
      .then(
        (
          data: {
            provider: string;
            model: string;
            url: string;
          }[]
        ) => {
          if (data.length > 0) {
            const model = localStorage.getItem("model");
            if (
              model &&
              data.find((m) => m.provider + ":" + m.model == model)
            ) {
              setModel(data.find((m) => m.provider + ":" + m.model == model));
            } else {
              setModel(data[0]);
            }
            setModelList(data);
          }
        }
      );
    const socket = new WebSocket(`/ws?session_id=${sessionIdRef.current}`);
    webSocketRef.current = socket;

    socket.addEventListener("open", (event) => {
      console.log("Connected to WebSocket server");
    });

    socket.addEventListener("message", (event) => {
      console.log("📨 WebSocket message received:", event.data);
      try {
        const data = JSON.parse(event.data);
        console.log("📦 Parsed WebSocket data:", data);
        if (data.type == "log") {
          console.log(data);
        }
        if (data.type == "error") {
          setPending(false);
          toast.error("Error: " + data.error, {
            closeButton: true,
            duration: 3600 * 1000, // set super large duration to make it not auto dismiss
            style: {
              color: "red",
            },
          });
        } else if (data.type == "done") {
          setPending(false);
        } else if (data.type == "info") {
          toast.info(data.info, {
            closeButton: true,
            duration: 10 * 1000,
          });
        } else {
          setMessages((prev) => {
            if (data.type == "delta") {
              console.log("📝 Delta message:", data);
              if (prev.at(-1)?.role == "assistant") {
                const lastMessage = structuredClone(prev.at(-1));
                if (lastMessage) {
                  if (typeof lastMessage.content == "string") {
                    lastMessage.content += data.text;
                  } else if (
                    lastMessage.content &&
                    lastMessage.content.at(-1) &&
                    lastMessage.content.at(-1)!.type === "text"
                  ) {
                    (lastMessage.content.at(-1) as { text: string }).text +=
                      data.text;
                  }
                  // TODO: handle other response type
                }
                return [...prev.slice(0, -1), lastMessage];
              } else {
                return [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.text,
                  },
                ];
              }
            } else if (data.type == "tool_call") {
              setExpandingToolCalls([...expandingToolCalls, data.id]);
              return prev.concat({
                role: "assistant",
                tool_calls: [
                  {
                    type: "function",
                    function: {
                      name: data.name,
                      arguments: "",
                    },
                    id: data.id,
                  },
                ],
              });
            } else if (data.type == "tool_call_arguments") {
              const lastMessage = structuredClone(prev.at(-1));

              if (
                lastMessage?.role === "assistant" &&
                lastMessage.tool_calls &&
                lastMessage.tool_calls.at(-1) &&
                lastMessage.tool_calls.at(-1)!.id == data.id
              ) {
                lastMessage.tool_calls.at(-1)!.function.arguments += data.text;
                return prev.slice(0, -1).concat(lastMessage);
              }
            } else if (data.type == "tool_call_result") {
              const res: {
                id: string;
                content: {
                  text: string;
                }[];
              } = data;
              console.log("res.content", res.content);
              const resultText = res.content.map((c) => c.text).join("\n");
              setAISuggestion(resultText);
              console.log("resultText:", resultText);
            } else if (data.type == "all_messages") {
              console.log("👇all_messages", data.messages);
              return data.messages;
            }
            return prev;
          });
        }
      } catch (error) {
        console.error("Error parsing JSON:", error);
      }
    });

    socket.addEventListener("close", (event) => {
      console.log("Disconnected from WebSocket server");
    });

    socket.addEventListener("error", (event) => {
      console.error("WebSocket error:", event);
    });

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, []);
  const onSendPrompt = (promptStr: string) => {
    if (pending) {
      return;
    }
    // if (!model) {
    //   toast.error(
    //     "Please select a model! Go to Settings to set your API keys if you haven't done so."
    //   );
    //   return;
    // }
    // if (!model.url || model.url == "") {
    //   toast.error("Please set the model URL in Settings");
    //   return;
    // }
    if (!promptStr || promptStr == "") {
      return;
    }

    const newMessages = messages.concat([
      {
        role: "user",
        //old
        //content: promptStr + "\n\n # " + editorTitle + "\n\n" + editorContent,
        //new
        content: `Please provide inline text suggestions by replacing words or phrases.
Use the format:
(original text) [suggested text]
Only wrap specific phrases you want to revise.
---

Content:
${editorContent}

---`,
      },
    ]);
    setMessages(newMessages);
    setPrompt("");
    setPending(true);
    fetch("/api/chat", {
      method: "Post",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: newMessages,
        session_id: sessionIdRef.current,
        // model: model.model,
        // provider: model.provider,
        // url: model.url,
      }),
    }).then((resp) => resp.json());
  };

  return (
    <div className="flex flex-col h-screen relative">
      {/* Chat messages */}
      <div
        className="flex-1 overflow-y-auto text-left"
        style={{ paddingBottom: FOOTER_HEIGHT }}
      >
        <div className="space-y-6 max-w-3xl mx-auto">
          <header className="flex space-x-2 mt-2">
            {/* <Button
              size={"sm"}
              variant={"ghost"}
              // onClick={() => setIsLeftSidebarOpen(!isLeftSidebarOpen)}
            >
              <SidebarIcon size={30} />
            </Button> */}
            <Select
              value={model?.provider + ":" + model?.model}
              onValueChange={(value) => {
                localStorage.setItem("model", value);
                setModel(
                  modelList.find((m) => m.provider + ":" + m.model == value)
                );
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Theme" />
              </SelectTrigger>
              <SelectContent>
                {modelList.map((model) => (
                  <SelectItem
                    key={model.provider + ":" + model.model}
                    value={model.provider + ":" + model.model}
                  >
                    {model.model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              size={"sm"}
              variant={"secondary"}
              onClick={() => (window.location.href = "/settings")}
            >
              <SettingsIcon size={30} />
            </Button>

            <Button
              size={"sm"}
              variant={"ghost"}
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <SunIcon size={30} />
              ) : (
                <MoonIcon size={30} />
              )}
            </Button>
            <Button size={"sm"} variant={"outline"} onClick={onClickNewChat}>
              <PlusIcon /> New Chat
            </Button>
          </header>
          {/* quick buttons */}
          {messages.length == 0 && (
            <div className="flex flex-col gap-2">
              <span className="text-muted-foreground">✨ Try asking:</span>
              <div className="flex space-x-2 flex-wrap gap-3 px-3">
                <Button
                  size={"sm"}
                  variant={"outline"}
                  onClick={() => {
                    onSendPrompt(`Improve my content:`);
                  }}
                >
                  🪄 Improve my writing
                </Button>
                <Button
                  size={"sm"}
                  variant={"outline"}
                  onClick={() => {
                    onSendPrompt(`Continue writing for my content:`);
                  }}
                >
                  ✍️ Continue writing
                </Button>
                <Button
                  size={"sm"}
                  variant={"outline"}
                  onClick={() => {
                    onSendPrompt(`Generate hashtags for my content:`);
                  }}
                >
                  🔥 Generate hashtags #
                </Button>
                <Button
                  size={"sm"}
                  variant={"outline"}
                  onClick={() => {
                    onSendPrompt(`Generate hashtags for my content:`);
                  }}
                >
                  📸 Generate cover photo
                </Button>
                {/* <Button
                  size={"sm"}
                  variant={"outline"}
                  onClick={() => {
                    onSendPrompt(`Generate hashtags for my content:`);
                  }}
                >
                  🚀 生成爆款标题
                </Button> */}
                {PLATFORMS_CONFIG.slice(0, 5).map((platform) => (
                  <Button
                    size={"sm"}
                    variant={"outline"}
                    onClick={() => {
                      onSendPrompt(
                        `Write below content to ${platform.name} style.`
                      );
                    }}
                  >
                    <img
                      src={platform.icon}
                      alt={platform.name}
                      className="w-4 h-4"
                    />
                    Write in {platform.name} style
                  </Button>
                ))}
              </div>
            </div>
          )}
          {/* Messages */}
          {messages.map((message, idx) => (
            <div key={`${idx}`}>
              {/* Regular message content */}
              {typeof message.content == "string" &&
                message.role !== "tool" && (
                  <div
                    className={`${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground rounded-2xl p-3 text-left ml-auto"
                        : "text-gray-800 dark:text-gray-200 text-left items-start"
                    } space-y-3 flex flex-col w-fit`}
                  >
                    <Markdown>{message.content}</Markdown>
                  </div>
                )}
              {typeof message.content == "string" &&
                message.role == "tool" &&
                expandingToolCalls.includes(message.tool_call_id) && (
                  <div>
                    <Markdown>{message.content}</Markdown>
                  </div>
                )}
              {Array.isArray(message.content) &&
                message.content.map((content, i) => {
                  if (content.type == "text") {
                    return (
                      <div
                        key={i}
                        className={`${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground rounded-2xl p-3 text-left ml-auto"
                            : "text-gray-800 dark:text-gray-200 text-left items-start"
                        } space-y-3 flex flex-col w-fit`}
                      >
                        <Markdown>{content.text}</Markdown>
                      </div>
                    );
                  } else if (content.type == "image_url") {
                    return (
                      <div key={i}>
                        <img src={content.image_url.url} alt="Image" />
                      </div>
                    );
                  }
                })}
              {message.role === "assistant" &&
                message.tool_calls &&
                message.tool_calls.at(-1)?.function.name != "finish" &&
                message.tool_calls.map((toolCall, i) => {
                  return (
                    <ToolCallTag
                      key={toolCall.id}
                      toolCall={toolCall}
                      isExpanded={expandingToolCalls.includes(toolCall.id)}
                      onToggleExpand={() => {
                        if (expandingToolCalls.includes(toolCall.id)) {
                          setExpandingToolCalls(
                            expandingToolCalls.filter(
                              (id) => id !== toolCall.id
                            )
                          );
                        } else {
                          setExpandingToolCalls([
                            ...expandingToolCalls,
                            toolCall.id,
                          ]);
                        }
                      }}
                    />
                  );
                })}
            </div>
          ))}
          {pending && messages.at(-1)?.role == "user" && (
            <div className="flex items-start text-left">{<Spinner />}</div>
          )}
        </div>
      </div>

      {/* Chat input */}
      <div
        className="p-4 gap-2 sticky bottom-0 border-t"
        style={{ minHeight: FOOTER_HEIGHT }}
      >
        {/* Input area */}
        <div className="flex flex-col relative flex-grow w-full space-x-2 max-w-3xl mx-auto">
          <div className="flex flex-grow w-full items-end space-x-2">
            <Textarea
              className="flex flex-1 flex-grow resize-none"
              placeholder="您想根据当前文章问什么？"
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
              }}
              style={{
                maxHeight: MAX_INPUT_HEIGHT,
                minHeight: FOOTER_HEIGHT,
                overflowY: "auto",
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault(); // Prevents adding a new line
                  onSendPrompt(prompt);
                }
              }}
            />
            {!pending && (
              <Button
                onClick={() => onSendPrompt(prompt)}
                disabled={pending}
                className="mb-1"
              >
                <SendIcon />
              </Button>
            )}
            {pending && (
              <Button
                disabled={disableStop}
                onClick={() => {
                  fetch("/api/cancel/" + sessionIdRef.current, {
                    method: "POST",
                  })
                    .then((resp) => resp.json())
                    .finally(() => {
                      setPending(false);
                    });
                }}
                className="mb-1"
              >
                <StopCircleIcon />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Component to render tool call tag
const ToolCallTag = ({
  toolCall,
  isExpanded,
  onToggleExpand,
}: {
  toolCall: ToolCall;
  isExpanded: boolean;
  onToggleExpand: () => void;
}) => {
  const { name, arguments: inputs } = toolCall.function;
  let parsedArgs: Record<string, any> | null = null;
  try {
    parsedArgs = JSON.parse(inputs);
  } catch (error) {}

  if (name == "prompt_user_multi_choice") {
    return <MultiChoicePrompt />;
  }
  if (name == "prompt_user_single_choice") {
    return <SingleChoicePrompt />;
  }

  return (
    <div className="w-full border rounded-md overflow-hidden">
      <Button
        variant={"secondary"}
        onClick={onToggleExpand}
        className={"w-full justify-start text-left"}
      >
        {isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
        <span
          style={{
            maxWidth: "80%",
            display: "inline-block",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          <span className="font-semibold text-muted-foreground">{name}</span>

          {parsedArgs &&
            Object.entries(parsedArgs).map(([key, value], i) => (
              <span key={i} className="ml-1">
                <span className="text-muted-foreground">{key}</span>=
                <span className="text-muted-foreground">
                  {String(value).slice(0, 100)}
                </span>
              </span>
            ))}
          {!parsedArgs && (
            <span className="text-muted-foreground">
              {String(inputs).slice(0, 100)}
            </span>
          )}
        </span>
      </Button>
      {isExpanded && (
        <div className="p-2">
          <Markdown>{inputs}</Markdown>
        </div>
      )}
    </div>
  );
};
export default ChatInterface;
