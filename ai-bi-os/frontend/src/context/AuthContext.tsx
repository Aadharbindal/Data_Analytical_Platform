"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  has_avatar?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  avatarVersion: number;
  login: (token: string, userData: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  // Bumped on every refreshUser() call so <img> tags relying on user.id alone
  // (a stable URL) actually re-fetch instead of showing a browser-cached
  // stale avatar after it's changed or removed.
  const [avatarVersion, setAvatarVersion] = useState(() => Date.now());

  const fetchUser = async () => {
    try {
      const response = await api.get("/api/v1/auth/me");
      setUser(response as any);
      return true;
    } catch (error) {
      setUser(null);
      return false;
    }
  };

  useEffect(() => {
    // Check if user is logged in on mount (once only)
    const checkAuth = async () => {
      await fetchUser();
      setLoading(false);
    };

    checkAuth();
  }, []); // run once on mount only

  const refreshUser = async () => {
    await fetchUser();
    setAvatarVersion(Date.now());
  };

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
    <AuthContext.Provider value={{ user, loading, avatarVersion, login, logout, refreshUser }}>
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
