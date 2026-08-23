import { motion } from 'framer-motion';

type SimulationResult = {
  year: number;
  yield: number;
  profit: number;
  co2_absorbed: number;
  water_usage: number;
};

interface LiveAnimationPanelProps {
  data: SimulationResult[];
}

export function LiveAnimationPanel({ data }: LiveAnimationPanelProps) {
  if (data.length === 0) return null;

  const latestData = data[data.length - 1];
  const progress = Math.min(latestData.yield / 15, 1); // Normalize yield to 0-1 for animation (assuming max yield is ~15)

  return (
    <div className="relative h-64 bg-gradient-to-b from-green-100 to-blue-100 rounded-lg overflow-hidden border">
      {/* Animated bar representing yield */}
      <motion.div
        className="absolute bottom-0 left-0 w-full bg-gradient-to-r from-green-400 to-blue-500 origin-bottom"
        initial={{ scaleY: 0 }}
        animate={{ scaleY: progress }}
        transition={{ duration: 1, ease: "easeInOut" }}
        style={{ height: '100%' }}
      />

      {/* Labels */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-white font-bold pointer-events-none z-10">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <p>Yield: {latestData.yield.toFixed(2)} tons</p>
          <p>Year: {latestData.year}</p>
        </motion.div>
      </div>

      {/* Optional: Animate other elements based on other data points */}
      {/* For example, a floating CO2 indicator */}
      <motion.div
        className="absolute top-4 right-4 bg-emerald-500 text-white p-2 rounded-full shadow-lg"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        CO2: {latestData.co2_absorbed.toFixed(2)}t
      </motion.div>
    </div>
  );
}