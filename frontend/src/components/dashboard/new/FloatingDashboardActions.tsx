import { Play, FileText, Activity, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export function FloatingDashboardActions() {
    return (
        <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
            <TooltipProvider delayDuration={0}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button size="icon" className="h-12 w-12 rounded-full bg-white/10 backdrop-blur-md border border-white/20 hover:bg-purple-500 hover:text-white hover:border-purple-500 transition-all shadow-lg text-white">
                            <FileText className="w-5 h-5" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="bg-black border-white/10 text-white font-inter">Generate Report</TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    );
}
