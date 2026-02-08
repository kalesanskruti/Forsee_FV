import { useLocation, useNavigate, useParams } from "react-router-dom";
import { motion, Variants } from "framer-motion";
import {
    ArrowLeft, Download, FileText, RotateCcw,
    CheckCircle2, AlertTriangle, AlertOctagon,
    Activity, Zap, Clock, TrendingUp, Cpu
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import NeuralBackground from "@/components/ui/flow-field-background";
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";
import { useEffect, useState } from "react";
import { systemsManifest } from "@/data/systems-manifest";
import { AssetIdentity } from "@/components/dashboard/AssetIdentity";

export default function SystemResultPage() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const result = location.state?.result;
    const inputValues = location.state?.inputs || {}; // Passed from input page
    const systemProfile = systemsManifest[slug || ""] || systemsManifest["wind-turbines"];

    // Animation States
    const [chartsLoaded, setChartsLoaded] = useState(false);

    // Simulate chart drawing delay
    useEffect(() => {
        const timer = setTimeout(() => setChartsLoaded(true), 600);
        return () => clearTimeout(timer);
    }, []);

    // Redirect if no result logic (optional, for safety)
    useEffect(() => {
        if (!result) {
            // In a real app, redirect back. specific for dev, we might mock.
            // navigate(`/system/${slug}`);
        }
    }, [result, navigate, slug]);


    // Mock Data Generators for Charts
    const generateTrendData = () => {
        return Array.from({ length: 40 }, (_, i) => ({
            time: i,
            value: 100 - (i * 0.8) + (Math.random() * 5 - 2.5),
            confidenceUpper: 100 - (i * 0.8) + 10,
            confidenceLower: 100 - (i * 0.8) - 10,
        }));
    };
    const [trendData] = useState(generateTrendData());


    if (!systemProfile) return null;

    const containerVariants: Variants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1, delayChildren: 0.2 }
        }
    };

    const itemVariants: Variants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { type: "spring", stiffness: 100, damping: 15 }
        }
    };

    return (
        <div className="min-h-screen bg-[#0B0B0B] text-white overflow-hidden relative font-inter selection:bg-[#8B4BFF]/30">
            {/* Background - Continuous Particle Flow */}
            <div className="fixed inset-0 z-0 opacity-40 mix-blend-screen pointer-events-none">
                <NeuralBackground color="#8B4BFF" speed={0.5} particleCount={400} />
            </div>

            {/* Top Navbar (Compact) */}
            <header className="relative z-20 h-16 border-b border-white/5 bg-[#0B0B0B]/80 backdrop-blur-md flex items-center justify-between px-6">
                <div className="flex items-center gap-6">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/system/${slug}`)} // Back to Input
                        className="text-slate-400 hover:text-white hover:bg-white/5"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back
                    </Button>
                    <div className="h-6 w-px bg-white/10" />
                    <AssetIdentity systemName={systemProfile.title} className="scale-90 origin-left" />

                    {/* Input Summary Row */}
                    <div className="hidden lg:flex items-center gap-4 ml-6">
                        {systemProfile.sensors.slice(0, 4).map((sensor, idx) => (
                            <div key={sensor.id} className="flex items-center gap-2 text-xs bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
                                <span className="text-slate-400 uppercase tracking-wider text-[10px]">{sensor.label}</span>
                                <span className="font-mono text-[#8B4BFF] font-medium">
                                    {inputValues[sensor.id] || sensor.defaultValue || "--"}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <span className="flex items-center gap-2 text-xs text-slate-400">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        Live Connection
                    </span>
                </div>
            </header>


            {/* Main Content Grid */}
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="relative z-10 grid grid-cols-12 gap-10 p-20 h-[calc(100vh-64px)] overflow-y-auto"
            >

                {/* COLUMN 1: Health Forecast (Interactive Timeline) - 50% */}
                <motion.div variants={itemVariants} className="col-span-12 lg:col-span-6 flex flex-col gap-6">
                    <Card className="flex-1 bg-white/[0.03] border-white/10 backdrop-blur-xl p-6 relative overflow-hidden group hover:border-[#8B4BFF]/30 transition-colors duration-500 rounded-2xl">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-[#8B4BFF]" /> Health Forecast
                                </h3>
                                <p className="text-sm text-slate-400 mt-1">Real-time degradation projection model v4.2</p>
                            </div>
                            <div className="flex gap-2">
                                {['1H', '24H', '7D', '30D'].map(range => (
                                    <button key={range} className="text-xs font-medium px-3 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-300 border border-transparent hover:border-white/10 transition-all">
                                        {range}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1 min-h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={trendData}>
                                    <defs>
                                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8B4BFF" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#8B4BFF" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} vertical={false} />
                                    <XAxis dataKey="time" hide />
                                    <YAxis domain={[0, 110]} hide />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }}
                                        itemStyle={{ color: "#e2e8f0" }}
                                        cursor={{ stroke: "#8B4BFF", strokeWidth: 1, strokeDasharray: "4 4" }}
                                    />
                                    <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "Critical Threshold", fill: "#ef4444", fontSize: 10, position: "insideBottomRight" }} />

                                    {chartsLoaded && (
                                        <>
                                            <Area
                                                type="monotone"
                                                dataKey="confidenceUpper"
                                                stroke="none"
                                                fill="#8B4BFF"
                                                fillOpacity={0.05}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="value"
                                                stroke="#8B4BFF"
                                                strokeWidth={3}
                                                fill="url(#colorValue)"
                                                animationDuration={1500}
                                            />
                                        </>
                                    )}
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </Card>
                </motion.div>


                {/* COLUMN 2: KPI Stack - 30% */}
                <motion.div variants={itemVariants} className="col-span-12 lg:col-span-3 flex flex-col gap-4">

                    {/* Severity Meter */}
                    <Card className="flex-[2] bg-white/[0.03] border-white/10 backdrop-blur-xl p-6 flex flex-col items-center justify-center relative rounded-2xl hover:bg-white/[0.04] transition-colors">
                        <div className="relative w-48 h-48 flex items-center justify-center">
                            {/* Custom Radial Gauge using SVG */}
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="96" cy="96" r="88" fill="none" stroke="#1e293b" strokeWidth="12" />
                                <motion.circle
                                    cx="96" cy="96" r="88" fill="none"
                                    stroke={result?.healthIndex < 50 ? "#ef4444" : result?.healthIndex < 75 ? "#f59e0b" : "#10b981"}
                                    strokeWidth="12" strokeLinecap="round" strokeDasharray="552"
                                    initial={{ strokeDashoffset: 552 }}
                                    animate={{ strokeDashoffset: 552 - (552 * ((result?.healthIndex || 0) / 100)) }}
                                    transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-5xl font-bold font-tinos tracking-tight">{result?.healthIndex || "--"}</span>
                                <span className="text-xs uppercase tracking-widest text-slate-400 mt-1">Health Score</span>
                            </div>
                        </div>
                        <div className="mt-4 flex flex-col items-center">
                            <div className={`px-4 py-1.5 rounded-full text-xs font-bold border ${result?.riskLevel === "CRITICAL" ? "bg-red-500/10 border-red-500/30 text-red-500" :
                                result?.riskLevel === "HIGH" ? "bg-orange-500/10 border-orange-500/30 text-orange-500" :
                                    "bg-green-500/10 border-green-500/30 text-green-500"
                                }`}>
                                {result?.riskLevel || "UNKNOWN"} SEVERITY
                            </div>
                        </div>
                    </Card>

                    {/* Secondary KPIs */}
                    <div className="flex-1 grid grid-cols-2 gap-4">
                        <Card className="bg-white/[0.03] border-white/10 p-4 flex flex-col justify-between rounded-xl hover:-translate-y-1 transition-transform duration-300">
                            <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
                                <Clock className="w-4 h-4 text-[#8B4BFF]" /> RUL
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-white">{result?.rul}</div>
                                <div className="text-[10px] text-slate-500">Predicted Cycles</div>
                            </div>
                        </Card>
                        <Card className="bg-white/[0.03] border-white/10 p-4 flex flex-col justify-between rounded-xl hover:-translate-y-1 transition-transform duration-300">
                            <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
                                <Zap className="w-4 h-4 text-amber-400" /> Conf.
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-white">{((result?.confidence || 0) * 100).toFixed(0)}%</div>
                                <div className="text-[10px] text-slate-500">Model Certainty</div>
                            </div>
                        </Card>
                    </div>
                </motion.div>


                {/* COLUMN 3: Actions & Insights - 20% */}
                <motion.div variants={itemVariants} className="col-span-12 lg:col-span-3 flex flex-col gap-4">

                    {/* Primary Recommendation */}
                    <Card className="bg-gradient-to-br from-[#8B4BFF]/10 to-transparent border-[#8B4BFF]/20 p-6 rounded-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-[#8B4BFF]/20 blur-[50px] rounded-full pointer-events-none" />
                        <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Cpu className="w-5 h-5 text-[#8B4BFF]" /> AI Recommendation
                        </h4>
                        <p className="text-sm text-slate-200 leading-relaxed font-medium">
                            {result?.action || "No immediate action required. Monitor sensor 3 for drift."}
                        </p>
                        <div className="mt-6 pt-4 border-t border-white/10">
                            <Button className="w-full bg-[#8B4BFF] hover:bg-[#7e42e5] text-white font-semibold shadow-[0_0_20px_rgba(139,75,255,0.2)]">
                                Initiate Workflow
                            </Button>
                        </div>
                    </Card>

                    {/* Maintenance Window */}
                    <Card className="bg-white/[0.03] border-white/10 p-5 rounded-2xl">
                        <h5 className="text-xs uppercase tracking-widest text-slate-400 mb-3">Next Window</h5>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 font-bold text-slate-300">
                                    14
                                </div>
                                <div>
                                    <div className="text-sm font-semibold text-white">Oct, 08:30</div>
                                    <div className="text-xs text-slate-500">Friday (Standard)</div>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white">
                                <ArrowLeft className="w-4 h-4 rotate-180" />
                            </Button>
                        </div>
                    </Card>

                    {/* Downloads / Footer Links */}
                    <div className="mt-auto pt-6 flex flex-col gap-3">
                        <div className="grid grid-cols-2 gap-3">
                            <Button variant="outline" className="border-white/10 bg-white/[0.02] hover:bg-white/5 text-slate-300 text-xs h-9">
                                <Download className="w-3 h-3 mr-2" /> Export PDF
                            </Button>
                            <Button variant="outline" className="border-white/10 bg-white/[0.02] hover:bg-white/5 text-slate-300 text-xs h-9">
                                <FileText className="w-3 h-3 mr-2" /> Raw Logs
                            </Button>
                        </div>
                        <Button
                            variant="ghost"
                            className="text-slate-500 hover:text-white text-xs h-8"
                            onClick={() => navigate(`/system/${slug}`)}
                        >
                            <RotateCcw className="w-3 h-3 mr-2" />
                            Re-run Prediction
                        </Button>
                    </div>

                </motion.div>

            </motion.div>
        </div>
    );
}
