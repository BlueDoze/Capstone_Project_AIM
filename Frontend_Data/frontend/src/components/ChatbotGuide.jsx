import React, { useState } from 'react';
import { X, MessageCircle, Map, Building2, Lightbulb } from 'lucide-react';

export default function ChatbotGuide({ onClose }) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      icon: <MessageCircle size={48} className="text-blue-500" />,
      title: "Welcome to Fanshawe Navigator",
      description: "Your AI-powered campus assistant for navigation, building info, and more.",
      tips: [
        "Ask questions in natural language",
        "Get instant answers about campus locations",
        "Receive personalized navigation directions"
      ]
    },
    {
      icon: <Map size={48} className="text-green-500" />,
      title: "Interactive Navigation",
      description: "Click 'Interactive Map' to explore the campus and find routes between buildings.",
      tips: [
        "View floor plans for all buildings",
        "Get turn-by-turn directions",
        "Visualize your route in real-time"
      ]
    },
    {
      icon: <Building2 size={48} className="text-fanshawe-red" />,
      title: "Building Information",
      description: "Ask about any building to get details like hours, facilities, and departments.",
      tips: [
        "Try: 'What's in Building A?'",
        "Ask about operating hours",
        "Find specific rooms and services"
      ]
    },
    {
      icon: <Lightbulb size={48} className="text-yellow-500" />,
      title: "Tips & Tricks",
      description: "Make the most of your campus navigation experience.",
      tips: [
        "Use dark mode for nighttime browsing",
        "Try quick action buttons below the chat",
        "Start a new chat anytime to clear history"
      ]
    }
  ];

  const step = steps[currentStep];

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-70 z-[9999] flex items-center justify-center p-5"
      onClick={onClose}
    >
      <div 
        className="bg-white dark:bg-gray-800 rounded-2xl max-w-[500px] w-full p-8 shadow-2xl relative animate-fadeIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button 
          onClick={onClose} 
          className="absolute top-4 right-4 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200"
          aria-label="Close guide"
        >
          <X size={24} className="text-gray-600 dark:text-gray-300" />
        </button>

        {/* Icon */}
        <div className="flex justify-center mb-6">
          {step.icon}
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-center mb-4 text-gray-900 dark:text-white">
          {step.title}
        </h2>

        {/* Description */}
        <p className="text-base text-center mb-6 leading-relaxed text-gray-700 dark:text-gray-300">
          {step.description}
        </p>

        {/* Tips Box */}
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
          <h4 className="text-sm font-semibold mb-2 text-gray-800 dark:text-gray-200">
            💡 {currentStep === steps.length - 1 ? 'Quick Tips:' : 'What you can do:'}
          </h4>
          <ul className="space-y-1">
            {step.tips.map((tip, idx) => (
              <li 
                key={idx} 
                className="text-sm text-gray-700 dark:text-gray-300 pl-5 relative"
              >
                <span className="absolute left-0 text-fanshawe-red font-bold">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>

        {/* Progress Dots */}
        <div className="flex justify-center gap-2 mb-6">
          {steps.map((_, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full transition-all duration-200 ${
                idx === currentStep 
                  ? 'bg-fanshawe-red w-6' 
                  : 'bg-gray-300 dark:bg-gray-600'
              }`}
            />
          ))}
        </div>

        {/* Navigation Buttons */}
        <div className="flex gap-3">
          {currentStep > 0 && (
            <button
              onClick={() => setCurrentStep(currentStep - 1)}
              className="flex-1 px-6 py-3 rounded-lg border-2 border-fanshawe-red bg-white dark:bg-gray-800 text-fanshawe-red font-medium transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Previous
            </button>
          )}
          <button
            onClick={() => {
              if (currentStep < steps.length - 1) {
                setCurrentStep(currentStep + 1);
              } else {
                onClose();
              }
            }}
            className="flex-1 px-6 py-3 rounded-lg bg-fanshawe-red text-white font-medium transition-all duration-200 hover:bg-fanshawe-red-dark"
          >
            {currentStep === steps.length - 1 ? "Get Started" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
