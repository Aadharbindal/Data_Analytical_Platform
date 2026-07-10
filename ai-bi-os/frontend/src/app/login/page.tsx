"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { Layers, Mail, Lock, Eye, EyeOff, Activity, ShieldCheck, Users } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await api.post("/api/v1/auth/login", {
        email,
        password
      });
      
      const user = await api.get("/api/v1/auth/me");
      login("cookie-auth", user as any);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred during login. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-background text-foreground overflow-hidden relative selection:bg-primary/30">
      
      {/* Background Effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-primary/5 blur-[150px] pointer-events-none" />

      <div className="w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 min-h-screen z-10">
        
        {/* Left Column - Branding & Features */}
        <div className="hidden lg:flex flex-col justify-center px-16 py-12 relative">
          
          {/* Logo */}
          <div className="absolute top-12 left-16 flex items-center gap-2">
            <div className="flex items-center justify-center bg-primary/10 p-2 rounded-xl border border-primary/20">
              <Layers className="h-6 w-6 text-primary" />
            </div>
            <span className="text-xl font-bold tracking-tight text-foreground">DataMind</span>
          </div>

          <div className="max-w-lg mt-12">
            {/* Tag */}
            <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary mb-8 shadow-[0_0_15px_rgba(0,112,243,0.1)]">
              <span>Smart Analytics. Better Decisions.</span>
            </div>

            {/* Heading */}
            <h1 className="text-5xl font-bold tracking-tight mb-6 leading-[1.1]">
              Welcome back <br /> to <span className="bg-gradient-to-r from-primary to-blue-400 text-transparent bg-clip-text">DataMind</span>
            </h1>

            <p className="text-lg text-muted-foreground leading-relaxed mb-16 max-w-md">
              Access your analytics workspace and turn data into meaningful insights.
            </p>

            {/* Features Row */}
            <div className="grid grid-cols-3 gap-6">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Activity className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-foreground mb-1">Real-time Analytics</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pr-2">Track metrics and KPIs as they happen.</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <ShieldCheck className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-foreground mb-1">Secure & Reliable</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pr-2">Enterprise-grade security to protect your data.</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-foreground mb-1">Collaborate Easily</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pr-2">Work with your team and share insights.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Auth Card */}
        <div className="flex items-center justify-center p-6 lg:p-12 relative">
          
          {/* Mobile Logo */}
          <div className="absolute top-8 left-8 flex lg:hidden items-center gap-2">
            <div className="flex items-center justify-center bg-primary/10 p-1.5 rounded-lg border border-primary/20">
              <Layers className="h-5 w-5 text-primary" />
            </div>
            <span className="text-lg font-bold tracking-tight text-foreground">DataMind</span>
          </div>

          {/* Glassmorphic Card */}
          <div className="w-full max-w-[440px] p-10 rounded-[32px] bg-surface/60 backdrop-blur-2xl border border-border shadow-2xl relative overflow-hidden">
            {/* Card inner glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            
            <div className="mb-10">
              <h2 className="text-[28px] font-bold text-foreground tracking-tight mb-2">Sign in</h2>
              <p className="text-muted-foreground text-sm">Enter your credentials to continue</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="email" className="text-xs font-semibold text-muted-foreground">Email address</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-11 h-12 bg-background/50 border-border focus-visible:border-primary/50 focus-visible:ring-1 focus-visible:ring-primary/50 text-foreground placeholder:text-muted-foreground rounded-xl transition-all"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-xs font-semibold text-muted-foreground">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full pl-11 pr-11 h-12 bg-background/50 border-border focus-visible:border-primary/50 focus-visible:ring-1 focus-visible:ring-primary/50 text-foreground placeholder:text-muted-foreground rounded-xl transition-all"
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {error && <div className="text-sm text-destructive font-medium bg-destructive/10 p-3 rounded-lg border border-destructive/20">{error}</div>}

              <Button 
                type="submit" 
                className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-[15px] rounded-xl shadow-[0_4px_14px_rgba(0,112,243,0.3)] transition-all hover:shadow-[0_6px_20px_rgba(0,112,243,0.4)]" 
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign in"}
              </Button>
            </form>

            <div className="mt-8 text-center text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link href="/signup" className="text-primary hover:text-primary/80 font-medium hover:underline transition-colors">
                Sign up
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
