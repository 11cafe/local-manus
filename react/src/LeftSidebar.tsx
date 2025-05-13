import {
  CheckCheckIcon,
  CheckIcon,
  CircleCheckIcon,
  PencilIcon,
  PlusIcon,
} from "lucide-react";
import { Button } from "./components/ui/button";
import Spinner from "./components/ui/Spinner";
import { IconCircleCheckFilled } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { ChatSession } from "./types/types";

export default function RightSidebar() {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  useEffect(() => {
    const fetchChatSessions = async () => {
      const sessions = await fetch("/api/list_chat_sessions", {
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await sessions.json();
      setChatSessions(data);
    };
    fetchChatSessions();
  }, []);
  return (
    <div className="flex flex-col gap-4 p-3">
      <Button size={"sm"} variant={"outline"} className="w-full">
        <PlusIcon /> New Chat
      </Button>
      <Button
        size={"sm"}
        variant={"outline"}
        className="w-full"
        onClick={() => {
          alert(
            "AI content writing Copilot is coming soon! We're working on it as fast as we can!"
          );
        }}
      >
        <PencilIcon className="w-4 h-4 text-xs size-4" /> Write
      </Button>

      <div className="flex flex-col text-left justify-start">
        {chatSessions.map((session) => (
          <Button variant={"ghost"} className="justify-start text-left px-2">
            {/* <Spinner /> */}
            {!!session.title ? session.title : "Untitled"}
          </Button>
        ))}
      </div>
    </div>
  );
}
