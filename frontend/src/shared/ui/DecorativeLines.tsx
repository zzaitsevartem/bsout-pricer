import React from 'react';

const DecorativeLines: React.FC = () => (
  <div className="fixed bottom-0 left-0 pointer-events-none z-0 select-none w-[45vw] h-[70vh] max-md:w-[60vw] max-md:h-[50vh] max-[480px]:w-[80vw] max-[480px]:h-[40vh] opacity-[0.08]">
    <svg
      viewBox="0 0 500 700"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-full"
      preserveAspectRatio="xMinYMax meet"
    >
      <path
        d="M-20 720 C60 580, 100 480, 140 380 S200 200, 260 100 S340 -20, 400 -40"
        stroke="#D97757"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M-20 650 C40 540, 80 440, 130 340 S190 180, 240 80 S300 -20, 350 -40"
        stroke="#141413"
        strokeWidth="1.2"
        fill="none"
      />
      <path
        d="M-20 580 C30 490, 70 400, 110 300 S170 160, 220 60 S280 -10, 320 -30"
        stroke="#D97757"
        strokeWidth="0.8"
        fill="none"
      />
      <path
        d="M-20 500 C25 430, 55 360, 90 270 S145 140, 190 50 S240 -10, 280 -20"
        stroke="#141413"
        strokeWidth="0.6"
        fill="none"
      />
      <circle cx="400" cy="-40" r="3" fill="#D97757" opacity="0.5" />
      <circle cx="350" cy="-40" r="2" fill="#141413" opacity="0.4" />
      <circle cx="320" cy="-30" r="1.5" fill="#D97757" opacity="0.3" />
    </svg>
  </div>
);

export default DecorativeLines;
