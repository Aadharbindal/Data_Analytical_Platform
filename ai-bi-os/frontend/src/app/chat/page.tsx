import { ChatUI } from "@/components/ChatUI";

export default function ChatPage() {
  return (
    <div className="flex flex-col w-full">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">AI Copilot</h1>
        <p className="text-sm text-muted-foreground mt-1">Ask questions, generate charts, and get strategic insights from your data.</p>
      </div>
      <ChatUI />
    </div>
  );
}
