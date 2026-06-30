"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { Eye, EyeOff, Save, CheckCircle2 } from "lucide-react";
import type { AppSettings } from "@/types";

export default function SettingsPage() {
  const [geminiKey, setGeminiKey] = useState("");
  const [grokKey, setGrokKey] = useState("");
  const [showGemini, setShowGemini] = useState(false);
  const [showGrok, setShowGrok] = useState(false);
  const [saved, setSaved] = useState(false);

  const { data: settings } = useQuery<AppSettings>({
    queryKey: ["settings"],
    queryFn: () => api.get("/settings").then((r) => r.data),
  });

  useEffect(() => {
    if (settings) {
      setGeminiKey(settings.gemini_api_key || "");
      setGrokKey(settings.grok_api_key || "");
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.put("/settings", {
        gemini_api_key: geminiKey || null,
        grok_api_key: grokKey || null,
      }),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-2xl font-semibold">Settings</h2>

      <div className="rounded-lg border border-border bg-card p-6 space-y-6">
        <h3 className="text-sm font-medium text-muted-foreground">API Keys</h3>

        {/* Gemini */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Google Gemini API Key
          </label>
          <div className="relative">
            <input
              type={showGemini ? "text" : "password"}
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="Enter your Gemini API key"
              className="w-full rounded-lg border border-input bg-background px-4 py-2.5 pr-10 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              onClick={() => setShowGemini(!showGemini)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            >
              {showGemini ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            Get a free key at{" "}
            <a href="https://aistudio.google.com/app/apikey" target="_blank" className="underline">
              aistudio.google.com
            </a>
          </p>
        </div>

        {/* Groq */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Groq API Key
          </label>
          <div className="relative">
            <input
              type={showGrok ? "text" : "password"}
              value={grokKey}
              onChange={(e) => setGrokKey(e.target.value)}
              placeholder="Enter your Groq API key"
              className="w-full rounded-lg border border-input bg-background px-4 py-2.5 pr-10 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              onClick={() => setShowGrok(!showGrok)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            >
              {showGrok ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            Get a free key at{" "}
            <a href="https://console.groq.com/keys" target="_blank" className="underline">
              console.groq.com
            </a>
          </p>
        </div>

        {/* Save */}
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {saved ? (
            <>
              <CheckCircle2 className="h-4 w-4" /> Saved
            </>
          ) : (
            <>
              <Save className="h-4 w-4" /> Save Settings
            </>
          )}
        </button>
      </div>

      {/* Database Status */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Database</h3>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span className="text-sm text-foreground">Connected (PostgreSQL)</span>
        </div>
      </div>
    </div>
  );
}
