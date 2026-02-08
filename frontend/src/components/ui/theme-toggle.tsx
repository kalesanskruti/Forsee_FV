"use client";

import { motion } from "framer-motion";
import { useTheme } from "@/context/ThemeContext";

interface ThemeToggleProps {
    className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
    const { isDark, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className={`relative w-14 h-8 rounded-full transition-colors duration-500 ${isDark
                ? "bg-gradient-to-r from-zinc-800 via-zinc-700 to-zinc-900"
                : "bg-gradient-to-r from-sky-400 via-sky-300 to-sky-400"
                } ${className}`}
            aria-label="Toggle theme"
        >
            {/* Background elements */}
            <div className="absolute inset-0 rounded-full overflow-hidden">
                {/* Stars (visible in dark mode) */}
                <motion.div
                    animate={{ opacity: isDark ? 1 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute inset-0"
                >
                    <div className="absolute top-2 left-2 w-0.5 h-0.5 bg-white rounded-full" />
                    <div className="absolute top-4 left-4 w-1 h-1 bg-white/70 rounded-full" />
                    <div className="absolute top-2.5 left-6 w-0.5 h-0.5 bg-white/50 rounded-full" />
                </motion.div>

                {/* Clouds (visible in light mode) */}
                <motion.div
                    animate={{ opacity: isDark ? 0 : 1, x: isDark ? 10 : 0 }}
                    transition={{ duration: 0.5 }}
                    className="absolute right-1 top-1/2 -translate-y-1/2"
                >
                    <div className="relative">
                        <div className="w-4 h-2 bg-white/80 rounded-full" />
                        <div className="absolute -top-1 left-1 w-3 h-2 bg-white/60 rounded-full" />
                    </div>
                </motion.div>
            </div>

            {/* Toggle circle (Sun/Moon) */}
            <motion.div
                animate={{
                    x: isDark ? 24 : 0,
                }}
                transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30,
                }}
                className={`absolute top-1 left-1 w-6 h-6 rounded-full shadow-lg flex items-center justify-center ${isDark ? "bg-zinc-200" : "bg-gradient-to-br from-yellow-300 to-yellow-500"
                    }`}
            >
                {/* Sun rays (visible in light mode) */}
                <motion.div
                    animate={{ opacity: isDark ? 0 : 1, rotate: isDark ? -90 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute inset-0 flex items-center justify-center"
                >
                    {[...Array(8)].map((_, i) => (
                        <motion.div
                            key={i}
                            className="absolute w-0.5 h-1 bg-yellow-600 rounded-full"
                            style={{
                                transformOrigin: "center 8px",
                                transform: `rotate(${i * 45}deg) translateY(-6px)`,
                            }}
                            animate={{
                                scale: isDark ? 0 : 1,
                            }}
                            transition={{ delay: i * 0.03, duration: 0.2 }}
                        />
                    ))}
                    <div className="w-3 h-3 bg-gradient-to-br from-yellow-300 to-orange-400 rounded-full" />
                </motion.div>

                {/* Moon face (visible in dark mode) */}
                <motion.div
                    animate={{ opacity: isDark ? 1 : 0, scale: isDark ? 1 : 0.5 }}
                    transition={{ duration: 0.3 }}
                    className="absolute inset-0 flex items-center justify-center"
                >
                    {/* Moon crescent effect */}
                    <div className="relative w-5 h-5">
                        <div className="absolute inset-0 bg-zinc-200 rounded-full" />
                        <motion.div
                            className="absolute top-0 right-0 w-4 h-5 bg-gradient-to-r from-transparent to-zinc-400/30 rounded-full"
                            animate={{ x: isDark ? 0 : 5 }}
                            transition={{ duration: 0.3 }}
                        />
                        {/* Craters */}
                        <div className="absolute top-1.5 left-1 w-1 h-1 bg-zinc-300 rounded-full" />
                        <div className="absolute top-2.5 left-2.5 w-0.5 h-0.5 bg-zinc-300 rounded-full" />
                        <div className="absolute top-1 left-2.5 w-0.5 h-0.5 bg-zinc-300 rounded-full" />
                    </div>
                </motion.div>
            </motion.div>
        </button>
    );
}
