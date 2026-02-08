import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { systemDomains } from "@/components/home/SystemsSection";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SensorInput } from "@/components/dashboard/SensorInput";
import { RiskLevel } from "@/components/dashboard/RiskBadge";
import NeuralBackground from "@/components/ui/flow-field-background";
import { MachineThinking } from "@/components/ui/machine-thinking";
import { systemsManifest } from "@/data/systems-manifest";
import { AssetIdentity } from "@/components/dashboard/AssetIdentity";

interface PredictionResult {
  rul: number;
  healthIndex: number;
  riskLevel: RiskLevel;
  precursorProb: number;
  confidence: number;
  failureMode: string;
  topSensors: { name: string; weight: number }[];
  action: string;
  driftDetected: boolean;
}

export default function SystemPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  // Load system profile from manifest
  const systemProfile = systemsManifest[slug || ""] || systemsManifest["wind-turbines"];
  const [sensorValues, setSensorValues] = useState<Record<string, string>>({});

  // Initialize default sensor values
  if (Object.keys(sensorValues).length === 0 && systemProfile) {
    const defaults: Record<string, string> = {};
    systemProfile.sensors.forEach(s => defaults[s.id] = s.defaultValue || "");
    setSensorValues(defaults);
  }

  if (!systemProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center text-white">
        <p className="text-muted-foreground">System profile not found.</p>
      </div>
    );
  }

  const handleRunPrediction = async () => {
    setIsLoading(true);
    // Simulate initial delay for "System Handshake"
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Wait for MachineThinking animation (simulated here, but the component does its own timeline)
    // We navigate AFTER a delay to let the animation play out a bit
    setTimeout(() => {
      // Mock prediction based on first sensor value
      const firstValue = parseFloat(Object.values(sensorValues)[0] || "0");
      const healthIndex = Math.max(0, Math.min(100, 85 - firstValue * 1.5));
      const riskLevel: RiskLevel =
        healthIndex >= 70 ? "LOW" :
          healthIndex >= 50 ? "MEDIUM" :
            healthIndex >= 30 ? "HIGH" : "CRITICAL";

      const result: PredictionResult = {
        rul: Math.round(healthIndex * 1.2),
        healthIndex: Math.round(healthIndex),
        riskLevel,
        precursorProb: Math.round((100 - healthIndex) / 100 * 100) / 100,
        confidence: 0.87,
        failureMode: healthIndex < 50 ? "Degradation Detected" : "Normal Operation",
        topSensors: systemProfile.sensors.slice(0, 4).map((s, i) => ({
          name: s.label,
          weight: Math.max(10, 40 - i * 8 + Math.random() * 10),
        })),
        action: healthIndex < 50
          ? systemProfile.defaultDecision.action
          : `Continue normal operation. Next scheduled maintenance in ${Math.round(healthIndex / 2)} days.`,
        driftDetected: healthIndex < 40,
      };

      setIsLoading(false);
      navigate("/output-preview", {
        state: {
          result,
          inputs: sensorValues,
          systemInfo: {
            id: slug,
            name: systemProfile.title,
            // You might want to pass an icon name or type here if needed for the dashboard
          }
        }
      });
    }, 2500); // 2.5s total thinking time
  };

  return (
    <div id={`system-page-${slug}`} className="min-h-screen relative overflow-hidden bg-background">
      <MachineThinking isThinking={isLoading} />

      {/* Light mode gradient background */}
      <div className="fixed inset-0 bg-gradient-to-br from-white via-purple-50 to-purple-100/50 dark:from-black dark:via-black dark:to-black pointer-events-none transition-all duration-500" />

      {/* Background - Purple Currents (highly vibrant in dark, adjusted for light) */}
      <div className="fixed inset-0 z-0 dark:opacity-100 opacity-40 transition-opacity duration-500">
        <NeuralBackground
          color="#9d4edd" // More vibrant purple
          speed={0.5}
          trailOpacity={0.2}
          particleCount={600}
        />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header - Shifted down to avoid navbar overlap */}
        <div className="pt-32 px-6 sm:px-12 relative">
          <button
            onClick={() => navigate("/systems")}
            className="absolute left-6 sm:left-12 top-32 flex items-center justify-center w-10 h-10 rounded-full bg-card/50 border border-border text-foreground/70 hover:text-foreground hover:bg-card shadow-lg transition-all"
            aria-label="Back to Systems"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>

          <div className="flex justify-center">
            <AssetIdentity systemName={systemProfile.title} className="items-center text-center" />
          </div>
        </div>

        {/* Centered Input Card */}
        <div className="flex-1 flex items-center justify-center px-6 sm:px-12 pb-20 w-full">

          <div className="w-full max-w-xl">
            <Card className="border-border bg-card/50 backdrop-blur-xl shadow-2xl relative overflow-hidden group">
              {/* Subtle gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-foreground/[0.05] to-transparent pointer-events-none" />

              <CardHeader className="relative z-10 pb-4">
                <CardTitle className="text-2xl font-semibold text-foreground tracking-tight">System Input</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Configure {systemProfile.title.toLowerCase()} parameters for analysis
                </CardDescription>
              </CardHeader>

              <CardContent className="relative z-10 space-y-6">
                <div className="grid gap-5">
                  {systemProfile.sensors.map((sensor) => (
                    <SensorInput
                      key={sensor.id}
                      id={sensor.id}
                      label={sensor.label}
                      unit={sensor.unit}
                      value={sensorValues[sensor.id] || ""}
                      onChange={(value) =>
                        setSensorValues((prev) => ({ ...prev, [sensor.id]: value }))
                      }
                      placeholder={sensor.placeholder}
                    />
                  ))}
                </div>

                <Button
                  id="runPredictBtn"
                  onClick={handleRunPrediction}
                  disabled={isLoading}
                  className="mt-8 w-full bg-[#8B4BFF] hover:bg-[#7a3ee3] text-white font-semibold h-12 text-lg shadow-[0_0_20px_rgba(139,75,255,0.15)] transition-all duration-300 hover:shadow-[0_0_30px_rgba(139,75,255,0.3)] hover:-translate-y-0.5 active:scale-98 active:translate-y-0"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Initializing...
                    </>
                  ) : (
                    "Run Health Prediction"
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

        </div>
      </div>
    </div>
  );
}
