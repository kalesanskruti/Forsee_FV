import { useLocation, useNavigate } from "react-router-dom";
import { LampContainer } from "@/components/ui/lamp";
import { SpotlightCard } from "@/components/ui/spotlight-card";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/context/DashboardContext";
import { Plus, Activity, AlertTriangle, AlertOctagon, CheckCircle, ChevronLeft, LayoutGrid } from "lucide-react";
import { toast } from "sonner";
import { TypingText } from "@/components/ui/TypingText";
import { motion } from "framer-motion";
import { useEffect } from "react";
import { renderCanvas, cleanupCanvas } from "@/components/ui/hero-designali";

export default function OutputPreview() {
    const location = useLocation();
    const navigate = useNavigate();
    const { addDevice } = useDashboard();
    const state = location.state as { result: any; inputs: any; systemInfo: any } | undefined;

    useEffect(() => {
        renderCanvas();
        return () => cleanupCanvas();
    }, []);

    const riskColors = {
        LOW: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
        MEDIUM: "text-yellow-600 dark:text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
        HIGH: "text-orange-600 dark:text-orange-500 bg-orange-500/10 border-orange-500/20",
        CRITICAL: "text-red-600 dark:text-red-500 bg-red-500/10 border-red-500/20",
    };

    const dummyState = {
        result: {
            healthIndex: 92,
            riskLevel: "LOW",
            failureMode: "Normal Operation",
            rul: 342,
            confidence: 0.98,
            action: "Maintain current monitoring schedule. No immediate action required."
        },
        systemInfo: {
            id: "demo-system",
            name: "Demo Jet Engine (HTS-400)"
        }
    };

    const isDemo = !state;
    const { result, systemInfo } = state || dummyState;

    const handleAddToDashboard = () => {
        if (isDemo) {
            toast.info("Demo System", {
                description: "This is a preview. To add real systems, run a prediction first."
            });
            return;
        }
        addDevice({
            id: `${systemInfo.id}-${Date.now()}`,
            name: systemInfo.name,
            icon: Activity
        });
        toast.success(`${systemInfo.name} added to Dashboard`, {
            description: "You can now monitor this system in real-time."
        });
        navigate("/dashboard");
    };

    const RiskIcon = {
        LOW: CheckCircle,
        MEDIUM: AlertTriangle,
        HIGH: AlertTriangle,
        CRITICAL: AlertOctagon,
    }[result.riskLevel as keyof typeof riskColors] || Activity;

    return (
        <div className="relative min-h-screen">
            <canvas
                className="fixed inset-0 z-0 pointer-events-none w-full h-full opacity-80 dark:mix-blend-screen transition-opacity duration-500"
                id="canvas"
            />
            <LampContainer className="bg-gradient-to-br from-white via-purple-50 to-purple-200 dark:from-black dark:via-black dark:to-purple-900 min-h-screen pt-48 pb-12">
                <SpotlightCard size={400} color="#9d4edd" className="opacity-50 dark:opacity-100" />
                <div className="container mx-auto px-4 relative z-10 max-w-5xl">
                    {/* Top Level Navigation */}
                    <div className="mb-8 flex items-center justify-between">
                        <Button
                            onClick={() => navigate("/systems")}
                            variant="ghost"
                            className="text-muted-foreground hover:text-foreground hover:bg-foreground/5 -ml-4"
                        >
                            <ChevronLeft className="w-4 h-4 mr-1" />
                            Go to Systems
                        </Button>
                    </div>

                    {/* Demo Note */}
                    {isDemo && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="mb-8 p-6 rounded-2xl bg-zinc-900 dark:bg-white border border-[#9d4edd]/30 dark:border-zinc-200 backdrop-blur-xl flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left shadow-[0_0_30px_rgba(157,78,221,0.1)]"
                        >
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2 text-[#9d4edd] justify-center md:justify-start">
                                    <AlertTriangle className="w-5 h-5" />
                                    <span className="font-bold uppercase tracking-widest text-xs">Preview Mode</span>
                                </div>
                                <p className="text-zinc-100 dark:text-zinc-900 text-lg font-medium">
                                    This is based on <strong>fake data</strong> for demonstration purposes.
                                </p>
                            </div>
                            <Button
                                onClick={() => navigate("/systems")}
                                className="bg-[#9d4edd] hover:bg-[#8b3dc7] text-white font-bold px-10 py-6 rounded-xl shadow-[0_0_20px_rgba(157,78,221,0.4)] transition-all hover:scale-105 active:scale-95 whitespace-nowrap"
                            >
                                Go to Systems
                            </Button>
                        </motion.div>
                    )}

                    {/* Header Section */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-foreground/5 border border-foreground/10 text-sm text-muted-foreground mb-4">
                            <Activity className="w-4 h-4 text-primary" />
                            <span>{isDemo ? "Demo Preview Result" : "Live Prediction Result"}</span>
                        </div>
                        <div className="text-4xl md:text-5xl font-bold text-foreground mb-4 flex justify-center gap-3">
                            <span className="text-muted-foreground font-normal">System:</span>
                            <TypingText text={systemInfo.name} className="text-foreground" />
                        </div>
                    </div>

                    {/* Main Results Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

                        {/* Primary Health Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="lg:col-span-2 bg-foreground/5 dark:bg-black/40 backdrop-blur-xl border border-foreground/10 dark:border-white/10 rounded-2xl p-8 relative overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />

                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
                                <div>
                                    <h3 className="text-lg font-medium text-muted-foreground">Health Index</h3>
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-6xl font-bold text-foreground tracking-tighter">
                                            {result.healthIndex}
                                        </span>
                                        <span className="text-xl text-muted-foreground">/ 100</span>
                                    </div>
                                </div>

                                <div className={`px-6 py-3 rounded-xl border flex items-center gap-3 ${riskColors[result.riskLevel as keyof typeof riskColors]}`}>
                                    <RiskIcon className="w-6 h-6" />
                                    <div className="flex flex-col">
                                        <span className="text-xs font-semibold uppercase opacity-80">Risk Level</span>
                                        <span className="text-xl font-bold">{result.riskLevel}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="h-4 bg-foreground/5 rounded-full overflow-hidden mb-8">
                                <div
                                    className="h-full bg-gradient-to-r from-primary to-primary/60 transition-all duration-1000 ease-out"
                                    style={{ width: `${result.healthIndex}%` }}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-8">
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Predicted Failure Mode</p>
                                    <p className="text-lg font-medium text-foreground">{result.failureMode}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">RUL Estimate</p>
                                    <p className="text-lg font-medium text-foreground">{result.rul} Days</p>
                                </div>
                            </div>
                        </motion.div>

                        {/* Quick Stats & Action */}
                        <div className="space-y-6">
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.1 }}
                                className="bg-foreground/5 dark:bg-black/40 backdrop-blur-xl border border-foreground/10 dark:border-white/10 rounded-2xl p-6"
                            >
                                <h3 className="text-sm font-medium text-muted-foreground mb-4">Analysis Confidence</h3>
                                <div className="flex items-center gap-4">
                                    <div className="relative w-16 h-16 flex items-center justify-center">
                                        <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" className="text-muted/20" strokeWidth="3" />
                                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" className="text-primary" strokeWidth="3" strokeDasharray={`${result.confidence * 100}, 100`} />
                                        </svg>
                                        <span className="absolute text-sm font-bold text-foreground">{(result.confidence * 100).toFixed(0)}%</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground leading-snug">
                                        Based on multi-sensor pattern matching and historical failure data.
                                    </p>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.2 }}
                                className="bg-foreground/5 dark:bg-black/40 backdrop-blur-xl border border-foreground/10 dark:border-white/10 rounded-2xl p-6"
                            >
                                <h3 className="text-sm font-medium text-muted-foreground mb-2">Recommended Action</h3>
                                <p className="text-foreground font-medium leading-relaxed">
                                    {result.action}
                                </p>
                            </motion.div>
                        </div>
                    </div>

                    {/* Bottom Action Bar */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="flex flex-col md:flex-row items-center justify-between bg-foreground/5 dark:bg-white/[0.03] backdrop-blur-md border border-foreground/10 dark:border-white/10 rounded-2xl p-6 gap-6"
                    >
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-primary/20 rounded-full text-primary">
                                <Activity className="w-6 h-6" />
                            </div>
                            <div>
                                <h4 className="text-foreground font-bold">Monitor this System</h4>
                                <p className="text-sm text-muted-foreground">Add to your live dashboard for continuous real-time tracking.</p>
                            </div>
                        </div>

                        <div className="flex gap-4 w-full md:w-auto">
                            <Button
                                onClick={() => navigate("/systems")}
                                variant="outline"
                                className="flex-1 md:flex-none border-foreground/10 hover:bg-foreground/5 text-muted-foreground"
                            >
                                <LayoutGrid className="w-4 h-4 mr-2" />
                                Go to Systems
                            </Button>
                            <Button
                                onClick={handleAddToDashboard}
                                className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-[0_0_20px_rgba(139,75,255,0.2)] flex-1 md:flex-none"
                            >
                                <Plus className="w-4 h-4 mr-2" />
                                Add to Dashboard
                            </Button>
                        </div>
                    </motion.div>

                </div>
            </LampContainer>
        </div>
    );
}
