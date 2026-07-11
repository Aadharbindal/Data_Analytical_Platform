import { ChatUI } from "@/components/ChatUI";
import { Sparkles } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] w-full p-4 md:p-6 overflow-hidden relative">
      <div className="mb-4 shrink-0 px-4 md:px-8 max-w-5xl mx-auto w-full flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            AI Copilot
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Ask questions, generate charts, and get strategic insights.</p>
        </div>
      </div>
      <ChatUI />
    </div>
  );
}
