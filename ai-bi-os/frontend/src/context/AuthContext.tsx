"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on mount (once only)
    const checkAuth = async () => {
      try {
        const response = await api.get("/api/v1/auth/me");
        setUser(response as any);
      } catch (error) {
        // /me failed — user is not authenticated. 
        // Do NOT redirect here; AppLayoutWrapper handles the guard
        // after loading becomes false.
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []); // run once on mount only

  const login = (token: string, userData: User) => {
    setUser(userData);
    window.location.href = "/";
  };

  const logout = async () => {
    try {
      await api.post("/api/v1/auth/logout", {});
    } catch (e) {
      console.error("Failed to logout cleanly", e);
    }
    setUser(null);
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
