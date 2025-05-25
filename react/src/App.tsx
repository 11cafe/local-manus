import { useEffect, useRef, useState } from "react";
import "./App.css";
import { Button } from "./components/ui/button";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ComputerIcon,
  MoonIcon,
  SettingsIcon,
  SidebarCloseIcon,
  SidebarIcon,
  SidebarOpenIcon,
  SunIcon,
} from "lucide-react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
} from "react-router-dom";
import Settings from "./Settings";
import { EAgentState, Message } from "./types/types";
import ChatInterface from "./Chat";
import { exampleMessages } from "./exampleMessages";
import { ThemeProvider } from "@/components/theme-provider";
import { useTheme } from "@/components/theme-provider";
import { toast, Toaster } from "sonner";
import LeftSidebar from "./LeftSidebar";
import { nanoid } from "nanoid";
import PostEditor from "./PostEditor";

function Home() {
  const [AISuggestion, setAISuggestion] = useState<string|null>(null);
  const [agentState, setAgentState] = useState(EAgentState.IDLE);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [maxSteps, setMaxSteps] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [sessionId, setSessionId] = useState<string>(nanoid());
  const [editorTitle, setEditorTitle] = useState("");
  const [editorContent, setEditorContent] = useState("");
  const { setTheme, theme } = useTheme();
  const [curPath, setCurPath] = useState("");
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/config/exists")
      .then((res) => res.json())
      .then((data) => {
        if (!data.exists) {
          navigate("/settings");
        }
      });
  }, []);

  return (
    <div className="flex">
      {isLeftSidebarOpen && (
        <div className="w-[16%] bg-sidebar h-screen">
          <LeftSidebar
            sessionId={sessionId}
            setSessionId={setSessionId}
            curPath={curPath}
            setCurPath={setCurPath}
            onClickWrite={() => {
              fetch("/api/create_file", {
                method: "POST",
                body: JSON.stringify({ rel_dir: "" }),
              })
                .then((res) => res.json())
                .then((data) => {
                  if (data.path) {
                    setCurPath(data.path);
                    dispatchEvent(new Event("refresh_workspace"));
                  } else {
                    throw new Error("Failed to create file");
                  }
                })
                .catch((err) => {
                  toast.error("Failed to create file");
                });
            }}
          />
        </div>
      )}
      <div className="w-[60%] h-screen px-5">
        {!!curPath && (
          <PostEditor 
            curPath={curPath} 
            setCurPath={setCurPath} 
            AISuggestion={AISuggestion} 
            setAISuggestion={setAISuggestion}
            editorContent={editorContent}
            setEditorContent={setEditorContent}
            editorTitle={editorTitle}
            setEditorTitle={setEditorTitle}
          />
        )}
      </div>
      <div className="flex-1 flex-grow relative px-4  bg-sidebar">
        <ChatInterface
          sessionId={sessionId}
          editorTitle={editorTitle}
          editorContent={editorContent}
          onClickNewChat={() => {
            setSessionId(nanoid());
          }}
          setAISuggestion={setAISuggestion}
        />

        {/* <div className="absolute top-5 right-8 flex gap-1">
          <Button
            size={"sm"}
            onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
          >
            {isRightSidebarOpen ? (
              <SidebarOpenIcon />
            ) : (
              <div className="flex">
                <ChevronLeftIcon />
                <ComputerIcon />
              </div>
            )}
          </Button>
        </div> */}
      </div>
    </div>
  );
}

function App() {
  const { theme } = useTheme();
  return (
    <BrowserRouter>
      <ThemeProvider defaultTheme={theme} storageKey="vite-ui-theme">
        <div className="app-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
        <Toaster />
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
