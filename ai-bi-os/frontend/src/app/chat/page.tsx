"use client";
import { motion } from "framer-motion";
import { ChatUI } from "@/components/ChatUI";

export default function ChatPage() {
  return (
    <motion.div
      className="flex flex-col h-full w-full overflow-hidden relative"
      initial={{ opacity: 0, scale: 0.98, filter: "blur(4px)" }}
      animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      <ChatUI />
    </motion.div>
  );
}
