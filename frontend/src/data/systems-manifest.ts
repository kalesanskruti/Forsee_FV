import { LucideIcon, Zap, Wind, Cog, Battery, Ruler, Activity, Server, Droplets, Workflow, Microscope } from "lucide-react";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface SensorConfig {
    id: string;
    label: string;
    unit: string;
    placeholder: string;
    defaultValue?: string;
}

export interface CognitiveEvent {
    time: string;
    description: string;
    type: "normal" | "warning" | "critical" | "inference";
    details?: string;
}

export interface DegradationDriver {
    factor: string;
    direction: "up" | "down" | "stable";
    impact: "strong" | "moderate" | "neutral";
}

export interface DecisionConfig {
    action: string;
    why: string[];
    consequences: {
        text: string;
        impact: string;
    }[];
}

export interface SystemProfile {
    id: string;
    title: string;
    icon: LucideIcon;
    description: string;
    digitalIdentity: {
        age: string;
        regime: string;
        model: string;
        lastMaintenance: string;
    };
    sensors: SensorConfig[];
    cognitiveTimeline: CognitiveEvent[];
    degradationDrivers: DegradationDriver[];
    economics: {
        potentialCost: string;
        downtimeCost: string;
    };
    defaultDecision: DecisionConfig;
}

export const systemsManifest: Record<string, SystemProfile> = {
    "power-transformers": {
        id: "power-transformers",
        title: "Power Transformer",
        icon: Zap,
        description: "Critical Grid Infrastructure",
        digitalIdentity: {
            age: "14.2 Years",
            regime: "Base Load (Continuous)",
            model: "Tx-Net-v4.2 (DGA)",
            lastMaintenance: "3 Months Ago"
        },
        sensors: [
            { id: "oilTemp", label: "Oil Temperature", unit: "°C", placeholder: "20-100", defaultValue: "85" },
            { id: "windingTemp", label: "Winding Temperature", unit: "°C", placeholder: "40-130", defaultValue: "92" },
            { id: "loadCurrent", label: "Load Current", unit: "A", placeholder: "0-2000", defaultValue: "1450" },
            { id: "hydrogen", label: "Hydrogen Gas", unit: "ppm", placeholder: "0-1000", defaultValue: "120" },
            { id: "partialDischarge", label: "Partial Discharge", unit: "pC", placeholder: "0-500", defaultValue: "45" },
        ],
        cognitiveTimeline: [
            { time: "-2h 15m", description: "Gas generation slope increased", type: "warning", details: "Rate: +18%" },
            { time: "-45m", description: "Thermal margin reduced below safe envelope", type: "inference", details: "Margin: < 5°C" },
            { time: "-12m", description: "Failure cluster shift", type: "critical", details: "Normal → Insulation Degradation" },
            { time: "Now", description: "RUL revised due to accelerated gas evolution", type: "inference", details: "-420 Cycles" },
        ],
        degradationDrivers: [
            { factor: "Hydrogen Gas", direction: "up", impact: "strong" },
            { factor: "Winding Temp", direction: "up", impact: "moderate" },
            { factor: "Partial Discharge", direction: "up", impact: "strong" },
            { factor: "Load Current", direction: "stable", impact: "neutral" },
        ],
        economics: {
            potentialCost: "$450,000",
            downtimeCost: "$42,000 / hr"
        },
        defaultDecision: {
            action: "Schedule Oil Analysis & Load Reduction",
            why: [
                "Hydrogen gas generation > 100ppm/day",
                "Insulation life impact: -14%",
                "Confirmed thermal stress pattern"
            ],
            consequences: [
                { text: "Catastrophic Dielectric Failure Probability", impact: "42%" },
                { text: "Est. Replacement Cost", impact: "$2.4M" }
            ]
        }
    },
    "wind-turbines": {
        id: "wind-turbines",
        title: "Wind Turbine",
        icon: Wind,
        description: "Renewable Energy Unit",
        digitalIdentity: {
            age: "6.5 Years",
            regime: "Variable (High Wind)",
            model: "Aero-Dyn-v9 (Vib)",
            lastMaintenance: "6 Months Ago"
        },
        sensors: [
            { id: "gearboxVib", label: "Gearbox Vibration", unit: "Hz", placeholder: "0-50", defaultValue: "28" },
            { id: "rotorSpeed", label: "Rotor Speed", unit: "RPM", placeholder: "0-20", defaultValue: "14" },
            { id: "genTemp", label: "Generator Temperature", unit: "°C", placeholder: "20-120", defaultValue: "98" },
            { id: "acoustic", label: "Acoustic Emission", unit: "dB", placeholder: "0-100", defaultValue: "72" }
        ],
        cognitiveTimeline: [
            { time: "-4h 30m", description: "Vibration spectral shift detected", type: "inference", details: "Harmonic: 3x" },
            { time: "-1h 20m", description: "Acoustic precursor probability crossed 0.7", type: "warning", details: "Threshold: 0.65" },
            { time: "-10m", description: "Failure cluster: Healthy → Gearbox Bearing Wear", type: "critical", details: "Confidence: 92%" }
        ],
        degradationDrivers: [
            { factor: "Gearbox Vibration", direction: "up", impact: "strong" },
            { factor: "Acoustic Emission", direction: "up", impact: "strong" },
            { factor: "Generator Temp", direction: "up", impact: "moderate" }
        ],
        economics: {
            potentialCost: "$120,000",
            downtimeCost: "$1,500 / hr"
        },
        defaultDecision: {
            action: "Schedule Bearing Replacement Window",
            why: [
                "Vibration RMS > ISO limit",
                "Acoustic signature matches 'Inner Race Defect'",
                "RUL < 30 days"
            ],
            consequences: [
                { text: "Gearbox Seizure Risk", impact: "High" },
                { text: "Crane Deployment Cost", impact: "+$45k" }
            ]
        }
    },
    "industrial-motors": {
        id: "industrial-motors",
        title: "Industrial Motor",
        icon: Cog,
        description: "HVAC & Manufacturing Driver",
        digitalIdentity: {
            age: "3.1 Years",
            regime: "Cyclic Start/Stop",
            model: "Induct-X-v2",
            lastMaintenance: "1 Month Ago"
        },
        sensors: [
            { id: "vibration", label: "Vibration", unit: "mm/s", placeholder: "0-25", defaultValue: "8" },
            { id: "statorCurrent", label: "Stator Current", unit: "A", placeholder: "0-500", defaultValue: "320" },
            { id: "temperature", label: "Motor Temperature", unit: "°C", placeholder: "20-100", defaultValue: "78" },
            { id: "rpm", label: "RPM", unit: "rpm", placeholder: "0-3600", defaultValue: "1750" }
        ],
        cognitiveTimeline: [
            { time: "-5h", description: "Power factor drift detected", type: "inference", details: "Delta: 0.05" },
            { time: "-2h", description: "Vibration RMS slope increased", type: "warning", details: "Slope: +5%/hr" },
            { time: "Now", description: "Failure cluster: Normal → Bearing Inner Race Wear", type: "critical", details: "Simulated" }
        ],
        degradationDrivers: [
            { factor: "Vibration", direction: "up", impact: "strong" },
            { factor: "Motor Temp", direction: "up", impact: "moderate" },
            { factor: "Stator Current", direction: "up", impact: "moderate" }
        ],
        economics: {
            potentialCost: "$15,000",
            downtimeCost: "$5,000 / hr (Line Stop)"
        },
        defaultDecision: {
            action: "Inspect Bearings & Lubrication",
            why: [
                "Vibration envelope high in 2kHz band",
                "Temperature rise correlates with load",
                "Precursor probability > 60%"
            ],
            consequences: [
                { text: "Catastrophic Seizure Probability", impact: "35%" },
                { text: "Production Halt Risk", impact: "Critical" }
            ]
        }
    },
    "icu-monitoring": {
        id: "icu-monitoring",
        title: "ICU Patient Monitor",
        icon: Activity,
        description: "Critical Care Telemetry",
        digitalIdentity: {
            age: "N/A",
            regime: "Triage: Critical",
            model: "Bio-Sense-AI-v1",
            lastMaintenance: "Daily Calib"
        },
        sensors: [
            { id: "ecg", label: "ECG Variability", unit: "ms", placeholder: "0-100", defaultValue: "45" },
            { id: "spo2", label: "SpO2", unit: "%", placeholder: "70-100", defaultValue: "94" },
            { id: "hr", label: "Heart Rate", unit: "bpm", placeholder: "40-200", defaultValue: "112" },
            { id: "resp", label: "Respiration Rate", unit: "bpm", placeholder: "10-40", defaultValue: "28" }
        ],
        cognitiveTimeline: [
            { time: "-15m", description: "Heart rate variability decreased", type: "warning", details: "Signs of stress" },
            { time: "-8m", description: "Oxygen saturation trend worsening", type: "critical", details: "Slope -2%" },
            { time: "-2m", description: "Failure cluster: Stable → Respiratory Risk", type: "critical", details: "Code Blue Risk" }
        ],
        degradationDrivers: [
            { factor: "SpO2", direction: "down", impact: "strong" },
            { factor: "Respiration Rate", direction: "up", impact: "moderate" },
            { factor: "ECG Variability", direction: "down", impact: "strong" }
        ],
        economics: {
            potentialCost: "Patient Safety Incident",
            downtimeCost: "Critical Life Risk"
        },
        defaultDecision: {
            action: "Escalate Monitoring / Clinical Intervention",
            why: [
                "Respiratory decompensation pattern detected",
                "SpO2/HR decoupling",
                "Sepsis precursor score > 0.8"
            ],
            consequences: [
                { text: "Acute Event Probability", impact: "High" },
                { text: "Response Window", impact: "< 10 min" }
            ]
        }
    },
    "servers": {
        id: "servers",
        title: "Data Center Server",
        icon: Server,
        description: "High-Performance Compute Node",
        digitalIdentity: {
            age: "1.5 Years",
            regime: "Peak Load",
            model: "Blade-X9",
            lastMaintenance: "2 Weeks Ago"
        },
        sensors: [
            { id: "cpuTemp", label: "CPU Temperature", unit: "°C", placeholder: "20-100", defaultValue: "88" },
            { id: "gpuTemp", label: "GPU Temperature", unit: "°C", placeholder: "20-100", defaultValue: "92" },
            { id: "fanSpeed", label: "Fan Speed", unit: "RPM", placeholder: "0-10000", defaultValue: "8500" },
            { id: "power", label: "Power Draw", unit: "W", placeholder: "0-2000", defaultValue: "1200" }
        ],
        cognitiveTimeline: [
            { time: "-1h", description: "Cooling efficiency dropped", type: "warning", details: "Delta T decreased" },
            { time: "-30m", description: "Thermal headroom reduced", type: "inference", details: "< 5% margin" },
            { time: "Now", description: "Failure probability increased under peak load", type: "critical", details: "Throttling imminent" }
        ],
        degradationDrivers: [
            { factor: "CPU Temp", direction: "up", impact: "strong" },
            { factor: "Fan Speed", direction: "up", impact: "moderate" },
            { factor: "Power Draw", direction: "up", impact: "moderate" }
        ],
        economics: {
            potentialCost: "$12,000 (Hardware)",
            downtimeCost: "$80,000 / hr (SLA Breach)"
        },
        defaultDecision: {
            action: "Redistribute Load & Schedule Cooling Maintenance",
            why: [
                "Junction temp nearing T-max",
                "Fan duty cycle at 100%",
                "Efficiency curve degrading"
            ],
            consequences: [
                { text: "Thermal Shutdown Probability", impact: "65%" },
                { text: "Service Degradation", impact: "Likely" }
            ]
        }
    },
    // Add placeholders for remaining systems to keep the file manageable but extensible
    "bridges": {
        id: "bridges",
        title: "Suspension Bridge",
        icon: Workflow,
        description: "Strategic Transport Link",
        digitalIdentity: { age: "42 Years", regime: "Heavy Traffic", model: "Civil-Struct-v1", lastMaintenance: "1 Year Ago" },
        sensors: [{ id: "strain", label: "Strain", unit: "µE", placeholder: "0-1000", defaultValue: "450" }, { id: "crack", label: "Crack Width", unit: "mm", placeholder: "0-5", defaultValue: "1.2" }],
        cognitiveTimeline: [{ time: "Now", description: "Crack growth acceleration", type: "warning" }],
        degradationDrivers: [{ factor: "Strain", direction: "up", impact: "strong" }],
        economics: { potentialCost: "Structural Integrity", downtimeCost: "Strategic Blockage" },
        defaultDecision: { action: "Structural Inspection & Load Restriction", why: ["Fatigue capability check failed"], consequences: [{ text: "Safety Factor", impact: "Reduced" }] }
    },
    "cnc-machines": {
        id: "cnc-machines",
        title: "CNC Machining Center",
        icon: Cog,
        description: "Precision Manufacturing",
        digitalIdentity: { age: "4 Years", regime: "24/7 Ops", model: "Precision-X", lastMaintenance: "2 Weeks Ago" },
        sensors: [{ id: "spindleVib", label: "Spindle Vib", unit: "mm/s", placeholder: "0-10", defaultValue: "4.5" }, { id: "toolWear", label: "Tool Wear", unit: "%", placeholder: "0-100", defaultValue: "85" }],
        cognitiveTimeline: [{ time: "Now", description: "Tool wear acceleration", type: "warning" }],
        degradationDrivers: [{ factor: "Tool Wear", direction: "up", impact: "strong" }],
        economics: { potentialCost: "$2,000 (Tool)", downtimeCost: "Scrap Batch Risk" },
        defaultDecision: { action: "Schedule Tool Change", why: ["Surface finish risk"], consequences: [{ text: "Quality Rejection", impact: "High" }] }
    },
    "hvac-systems": { // Mapped to Pipelines conceptually or kept separate
        id: "hvac-systems",
        title: "HVAC System",
        icon: Wind,
        description: "Building Climate Control",
        digitalIdentity: { age: "8 Years", regime: "Cyclic", model: "Cool-Master", lastMaintenance: "4 Months Ago" },
        sensors: [{ id: "pressure", label: "Compressor Pressure", unit: "PSI", placeholder: "0-500", defaultValue: "420" }],
        cognitiveTimeline: [{ time: "Now", description: "Efficiency drop detected", type: "warning" }],
        degradationDrivers: [{ factor: "Pressure", direction: "up", impact: "moderate" }],
        economics: { potentialCost: "$8,000", downtimeCost: "Comfort / Compliance" },
        defaultDecision: { action: "Filter & Coil Cleaning", why: ["Delta-T reduced"], consequences: [{ text: "Energy Cost", impact: "+15%" }] }
    },
    "pipelines": { // Explicitly adding pipelines even if route might not exist, for completeness
        id: "pipelines",
        title: "Oil & Gas Pipeline",
        icon: Droplets,
        description: "Critical Transport Infrastructure",
        digitalIdentity: { age: "22 Years", regime: "Continuous Flow", model: "Pipe-Net-v3", lastMaintenance: "6 Months Ago" },
        sensors: [{ id: "pressure", label: "Pressure", unit: "PSI", placeholder: "0-1000", defaultValue: "850" }, { id: "acoustic", label: "Acoustic Leak", unit: "dB", placeholder: "0-100", defaultValue: "20" }],
        cognitiveTimeline: [{ time: "Now", description: "Acoustic anomaly detected", type: "critical" }],
        degradationDrivers: [{ factor: "Pressure Drop", direction: "down", impact: "strong" }],
        economics: { potentialCost: "Environmental Spill", downtimeCost: "$150,000 / hr" },
        defaultDecision: { action: "Emergency Valve Shutoff & Inspection", why: ["Leak probability > 99%"], consequences: [{ text: "Spill Volume", impact: "Escalating" }] }
    },
    "semiconductor-tools": {
        id: "semiconductor-tools",
        title: "Lithography Scanner",
        icon: Microscope,
        description: "Nanofabrication Tool",
        digitalIdentity: { age: "2 Years", regime: "High Precision", model: "Nano-Lith-X", lastMaintenance: "1 Week Ago" },
        sensors: [{ id: "alignment", label: "Alignment Error", unit: "nm", placeholder: "0-20", defaultValue: "8" }, { id: "stageVib", label: "Stage Vib", unit: "nm", placeholder: "0-10", defaultValue: "3" }],
        cognitiveTimeline: [{ time: "Now", description: "Alignment drift detect", type: "warning" }],
        degradationDrivers: [{ factor: "Alignment Error", direction: "up", impact: "strong" }],
        economics: { potentialCost: "$500,000 (Yield)", downtimeCost: "$20,000 / hr" },
        defaultDecision: { action: "Recalibration & Optics Cleaning", why: ["Yield impact risk"], consequences: [{ text: "Wafer Scrap", impact: "High" }] }
    }
};

// Start logic for systems not explicitly in nav but required by manifest
// Ensure navigation/routing handles these if they are selectable
