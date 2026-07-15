"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedLogoProps {
  className?: string;
  size?: number; // default 32
}

export const AnimatedLogo = ({ className, size = 32 }: AnimatedLogoProps) => {
  const scale = size / 32;

  return (
    <div 
      className={cn("relative shrink-0 flex items-center justify-center rounded-full bg-[radial-gradient(circle_at_50%_45%,_#141c2e_0%,_#0a0e1a_75%)] border border-[#ffffff0f] shadow-[0_0_15px_rgba(59,130,246,0.35)]", className)}
      style={{ width: size, height: size }}
    >
      <div style={{ transform: `scale(${scale})`, width: 32, height: 32 }} className="relative flex items-center justify-center">
        {/* Pulsing Rings */}
        <motion.div 
          animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
          transition={{ duration: 1.4, ease: "easeOut", repeat: Infinity, repeatDelay: 2.6, delay: 0.75 }}
          className="absolute inset-0 rounded-full border-[1.5px] border-[#6b9cf6] pointer-events-none"
        />
        <motion.div 
          animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
          transition={{ duration: 1.4, ease: "easeOut", repeat: Infinity, repeatDelay: 2.6, delay: 1.55 }}
          className="absolute inset-0 rounded-full border-[1.5px] border-[#6b9cf6] pointer-events-none"
        />

        {/* Orbiting Dot */}
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 3.5, ease: "linear", repeat: Infinity }}
          className="absolute inset-0 pointer-events-none"
        >
          <div className="absolute top-[2px] left-1/2 -translate-x-1/2 w-[3.5px] h-[3.5px] bg-[#6b9cf6] rounded-full shadow-[0_0_6px_1.5px_rgba(107,156,246,0.9)]" />
        </motion.div>

        {/* Stacked Diamonds (Isometric) */}
        <motion.div 
          className="relative w-full h-full pointer-events-none"
          animate={{ y: [0, -3, 0] }}
          transition={{ duration: 4, ease: "easeInOut", repeat: Infinity }}
        >
          {/* Bottom Layer */}
          <div className="absolute left-1/2 top-1/2" style={{ transform: "translate(-50%, -50%)" }}>
            <motion.div 
              animate={{ y: [-15, 6, 6, -15], scale: [0.5, 1, 1, 0.5], opacity: [0, 1, 1, 0] }}
              transition={{ duration: 4, ease: "backOut", repeat: Infinity, times: [0, 0.15, 0.95, 1], delay: 0.3 }}
            >
              <div className="w-[12px] h-[12px] border-[1.5px] border-[#1e40af] rounded-[2px]" style={{ transform: "scaleY(0.42) rotate(45deg)" }} />
            </motion.div>
          </div>

          {/* Middle Layer */}
          <div className="absolute left-1/2 top-1/2" style={{ transform: "translate(-50%, -50%)" }}>
            <motion.div 
              animate={{ y: [-15, 1, 1, -15], scale: [0.5, 1, 1, 0.5], opacity: [0, 1, 1, 0] }}
              transition={{ duration: 4, ease: "backOut", repeat: Infinity, times: [0, 0.15, 0.95, 1], delay: 0.15 }}
            >
              <div className="w-[12px] h-[12px] border-[1.5px] border-[#3b82f6] rounded-[2px]" style={{ transform: "scaleY(0.42) rotate(45deg)" }} />
            </motion.div>
          </div>

          {/* Top Layer */}
          <div className="absolute left-1/2 top-1/2" style={{ transform: "translate(-50%, -50%)" }}>
            <motion.div 
              animate={{ y: [-15, -4, -4, -15], scale: [0.5, 1, 1, 0.5], opacity: [0, 1, 1, 0] }}
              transition={{ duration: 4, ease: "backOut", repeat: Infinity, times: [0, 0.15, 0.95, 1], delay: 0 }}
            >
              <div className="w-[12px] h-[12px] bg-[#6b9cf6] shadow-[0_0_8px_rgba(107,156,246,0.8)] rounded-[2px]" style={{ transform: "scaleY(0.42) rotate(45deg)" }} />
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
