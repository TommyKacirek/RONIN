"use client";

import { useState } from "react";
import axios from "axios";
import { LucideUpload, LucideCheckCircle2, LucideLoader2 } from "lucide-react";
import { toast } from "sonner";

import { FileUpload } from "./FileUpload";

export function Onboarding({ onComplete }: { onComplete: () => void }) {
    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-6">
            <div className="max-w-md w-full space-y-8 text-center">
                <div className="space-y-4">
                    <div className="inline-flex p-4 bg-blue-500/10 rounded-2xl text-blue-400">
                        <LucideUpload size={40} />
                    </div>
                    <h1 className="text-4xl font-extrabold tracking-tight text-white">
                        Vítej v RONIN
                    </h1>
                    <p className="text-zinc-500 text-lg">
                        Tvůj osobní cockpit pro správu investic. Pro začátek nahraj své IBKR reporty (CSV).
                    </p>
                </div>

                <FileUpload onComplete={onComplete} />

                <p className="text-zinc-600 text-sm">
                    Tato aplikace běží lokálně. Tvoje data nikdy neopustí tvůj počítač.
                </p>
            </div>
        </div>
    );
}
