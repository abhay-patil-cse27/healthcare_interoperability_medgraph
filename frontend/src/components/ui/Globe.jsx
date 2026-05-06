import createGlobe from "cobe";
import { useEffect, useRef } from "react";

export default function Globe({ className }) {
  const canvasRef = useRef();

  useEffect(() => {
    let phi = 0;
    
    // RGB calculations for #9FE870 (Fast Green) and #163300 (Forest Green)
    // #9FE870 -> 159, 232, 112 -> [0.623, 0.909, 0.439]
    // #163300 -> 22, 51, 0 -> [0.086, 0.2, 0]

    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: 1000,
      height: 1000,
      phi: 0,
      theta: 0.3,
      dark: 0, 
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.95, 0.98, 0.93], // Soft tint #f2f9ed
      markerColor: [0.623, 0.909, 0.439], // Fast green
      glowColor: [0.8, 0.95, 0.7], 
      markers: [
        { location: [28.6139, 77.2090], size: 0.1 }, // New Delhi
        { location: [37.7749, -122.4194], size: 0.05 }, // SF
        { location: [51.5074, -0.1278], size: 0.07 }, // London
        { location: [35.6762, 139.6503], size: 0.05 }, // Tokyo
      ],
      onRender: (state) => {
        // Rotate globe
        state.phi = phi;
        phi += 0.003;
      },
    });

    return () => {
      globe.destroy();
    };
  }, []);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%", aspectRatio: 1 }}
      />
    </div>
  );
}
