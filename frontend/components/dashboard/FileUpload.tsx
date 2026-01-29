"use client";

import { useState } from "react";
import axios from "axios";
import { LucideUpload, LucideCheckCircle2, LucideLoader2 } from "lucide-react";
import { toast } from "sonner";

export function FileUpload({ onComplete, compact = false }: { onComplete: () => void, compact?: boolean }) {
    const [files, setFiles] = useState<FileList | null>(null);
    const [uploading, setUploading] = useState(false);

    const handleUpload = async () => {
        if (!files || files.length === 0) return;

        setUploading(true);
        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append("files", file);
        });

        try {
            await axios.post("http://localhost:8000/api/upload", formData);
            toast.success("Files uploaded successfully!");
            onComplete();
        } catch (e) {
            toast.error("Upload failed. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className={compact ? "" : "bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 space-y-6"}>
            <div className="relative group cursor-pointer">
                <input
                    type="file"
                    multiple
                    accept=".csv"
                    onChange={(e) => setFiles(e.target.files)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className={`border-2 border-dashed border-zinc-800 group-hover:border-blue-500/50 transition-colors rounded-2xl ${compact ? "p-4" : "p-8"} space-y-2`}>
                    <div className="text-zinc-400 flex justify-center">
                        {files ? <LucideCheckCircle2 className="text-green-500" /> : <LucideUpload size={compact ? 18 : 24} />}
                    </div>
                    <p className={`${compact ? "text-xs" : "text-sm"} font-medium text-white text-center`}>
                        {files ? `${files.length} souborů vybráno` : "Klikni nebo přetáhni CSV soubory"}
                    </p>
                    {!compact && <p className="text-xs text-zinc-600 text-center">Podporováno: IBKR Activity Statement (.csv)</p>}
                </div>
            </div>

            <button
                onClick={handleUpload}
                disabled={!files || uploading}
                className={`w-full ${compact ? "py-2 text-sm" : "py-3"} bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-xl font-bold transition-all flex items-center justify-center gap-2`}
            >
                {uploading ? <LucideLoader2 className="animate-spin" size={compact ? 16 : 20} /> : "Nahrát a analyzovat"}
            </button>
        </div>
    );
}
