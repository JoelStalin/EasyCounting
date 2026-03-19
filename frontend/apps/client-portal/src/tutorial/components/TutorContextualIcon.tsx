import React, { useState } from "react";
import { FieldHelpInfo } from "../types";

export const TutorContextualIcon: React.FC<{ info: FieldHelpInfo }> = ({ info }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block ml-2 align-middle">
      <button 
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-slate-300 hover:bg-primary hover:text-white transition-colors"
        aria-label={`Ayuda para ${info.label}`}
      >
        ?
      </button>

      {isOpen && (
        <div className="absolute left-1/2 bottom-full mb-3 -translate-x-1/2 w-72 rounded-lg bg-slate-900 border border-slate-700 shadow-elevated p-4 z-50 text-left cursor-default">
          {/* Triángulo del tooltip */}
          <div className="absolute left-1/2 top-full -translate-x-1/2 -mt-px border-4 border-transparent border-t-slate-700"></div>
          
          <h4 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
            <span>{info.label}</span>
            {info.isRequired ? (
              <span className="text-[10px] uppercase font-bold text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">Requerido</span>
            ) : (
              <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">Opcional</span>
            )}
          </h4>
          
          <p className="text-xs text-slate-300 mb-3">{info.description}</p>
          
          <div className="space-y-2 text-[11px]">
            {info.expectedFormat && (
              <div className="flex flex-col">
                <span className="text-slate-500 font-semibold px-2">Formato</span>
                <span className="text-slate-200 border-l border-slate-700 ml-2 pl-2 mt-0.5">{info.expectedFormat}</span>
              </div>
            )}
            {info.exampleValue && (
              <div className="flex flex-col">
                <span className="text-slate-500 font-semibold px-2">Ejemplo</span>
                <span className="font-mono text-emerald-400 border-l border-slate-700 ml-2 pl-2 mt-0.5">"{info.exampleValue}"</span>
              </div>
            )}
            {info.businessImpact && (
              <div className="bg-primary/10 border border-primary/20 rounded p-2 mt-2">
                <span className="font-bold text-primary block mb-0.5">💡 Impacto Técnico:</span>
                <span className="text-slate-300">{info.businessImpact}</span>
              </div>
            )}
            {info.recommendation && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded p-2 mt-2">
                <span className="font-bold text-amber-500 block mb-0.5">⚠️ Recomendación:</span>
                <span className="text-slate-300">{info.recommendation}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
