"use client";
import React from 'react';
import { 
  LayoutDashboard, 
  BarChart2, 
  FileText, 
  Lightbulb,
  TrendingUp,
  Users,
  LineChart,
  Settings,
  Puzzle,
  HelpCircle
} from 'lucide-react';

export const Sidebar: React.FC<{ activeView: string, setActiveView: (v: string) => void }> = ({ activeView, setActiveView }) => {
  return (
    <aside className="w-64 h-screen bg-[#111111] border-r border-[#2a2a2a] flex flex-col text-sm fixed left-0 top-0">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-lg">
          IX
        </div>
        <span className="text-white font-semibold text-lg">InsightX</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 space-y-6">
        <div>
          <h4 className="text-gray-500 font-medium mb-2 px-2 text-xs uppercase tracking-wider">Main</h4>
          <ul className="space-y-1">
            <SidebarItem 
              icon={<LayoutDashboard size={18} />} 
              label="Dashboard" 
              active={activeView === 'dashboard'} 
              onClick={() => setActiveView('dashboard')} 
            />
            <SidebarItem 
              icon={<BarChart2 size={18} />} 
              label="Chatbot" 
              active={activeView === 'chatbot'} 
              onClick={() => setActiveView('chatbot')} 
            />
            <SidebarItem icon={<FileText size={18} />} label="Reports" />
            <SidebarItem icon={<Lightbulb size={18} />} label="Insights" />
          </ul>
        </div>

        <div>
          <h4 className="text-gray-500 font-medium mb-2 px-2 text-xs uppercase tracking-wider">Performance</h4>
          <ul className="space-y-1">
            <SidebarItem icon={<TrendingUp size={18} />} label="Sales Performance" />
            <SidebarItem icon={<Users size={18} />} label="User / Customer Metrics" />
            <SidebarItem icon={<LineChart size={18} />} label="Growth Trends" />
          </ul>
        </div>

        <div>
          <h4 className="text-gray-500 font-medium mb-2 px-2 text-xs uppercase tracking-wider">System</h4>
          <ul className="space-y-1">
            <SidebarItem icon={<Settings size={18} />} label="Settings" />
            <SidebarItem icon={<Puzzle size={18} />} label="Integrations" />
            <SidebarItem icon={<HelpCircle size={18} />} label="Help & Support" />
          </ul>
        </div>
      </nav>

      <div className="p-4 border-t border-[#2a2a2a]">
        <div className="flex items-center gap-3 p-2 hover:bg-[#1a1a1a] rounded-lg cursor-pointer">
          <div className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
            WW
          </div>
          <div>
            <p className="text-white font-medium text-sm">Wade Warren</p>
            <p className="text-gray-500 text-xs">#OWN-9f6d40d9</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

const SidebarItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) => {
  return (
    <li>
      <button 
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${active ? 'bg-white text-black shadow-lg shadow-white/10' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
      >
        <span className={active ? "text-neon-green" : ""}>{icon}</span>
        <span className="font-medium">{label}</span>
      </button>
    </li>
  );
};
