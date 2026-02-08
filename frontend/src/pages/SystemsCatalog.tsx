import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CardStack, CardStackItem } from "@/components/ui/card-stack";
import { ZoomParallax } from "@/components/ui/zoom-parallax";
import { systemCards } from "@/components/home/SystemsSection";
import { ArrowRight } from "lucide-react";

export default function SystemsCatalog() {
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<CardStackItem>(systemCards[0]);

  // Select 7 diverse images for the parallax effect
  const parallaxImages = systemCards.slice(0, 7).map(card => ({
    src: card.imageSrc,
    alt: card.title
  }));

  return (
    <div className="min-h-screen w-full bg-background relative">
      {/* Light mode gradient background */}
      <div className="fixed inset-0 bg-gradient-to-br from-white via-purple-50 to-purple-100/50 dark:from-black dark:via-black dark:to-black pointer-events-none transition-all duration-500" />

      <ZoomParallax images={parallaxImages} />
      <div className="min-h-screen w-full relative z-10 flex flex-col items-center justify-center py-20">
        <div className="mb-12 text-center">
          <h2 className="text-3xl md:text-5xl font-semibold text-foreground tracking-tight mb-4">
            Operational Systems
          </h2>
          <p className="text-sm md:text-base text-muted-foreground max-w-lg mx-auto">
            Swipe or click cards to explore available systems.
          </p>
        </div>
        <div className="max-w-4xl w-full px-6">
          <CardStack
            items={systemCards}
            cardWidth={400}
            cardHeight={300}
            activeScale={1.1}
            overlap={0.5}
            autoAdvance={true}
            intervalMs={1500}
            onChangeIndex={(_, item) => setActiveItem(item)}
          />
        </div>

        {/* Dynamic Navigation Button */}
        <div className="mt-20">
          <button
            onClick={() => activeItem.href && navigate(activeItem.href)}
            className="group relative flex items-center gap-2 px-8 py-4 bg-[#8B4BFF] hover:bg-[#9D66FF] text-white font-bold rounded-full transition-all duration-300 shadow-[0_0_20px_rgba(139,75,255,0.3)] hover:shadow-[0_0_30px_rgba(139,75,255,0.5)] active:scale-95"
          >
            <span>Predict in {activeItem.title}</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />

            {/* Glow Effect */}
            <div className="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-10 transition-opacity" />
          </button>
        </div>
      </div>
    </div>
  );
}
