import { ChatUI } from "@/components/ChatUI";
import { Sparkles } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-full w-full overflow-hidden relative">
      <div className="shrink-0 pt-6 pb-2 px-6 max-w-5xl mx-auto w-full flex items-center justify-between z-10">
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
