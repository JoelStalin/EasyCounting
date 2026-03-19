import { useState, useCallback } from "react";
export function useFormTutor(config) {
    const [isActive, setIsActive] = useState(() => {
        // Revisar persistencia de si se omitió permanentemente el tutorial
        return localStorage.getItem(`tutor_dismissed_${config.formId}`) !== "true";
    });
    const dismissTutor = useCallback((permanently = false) => {
        setIsActive(false);
        if (permanently) {
            localStorage.setItem(`tutor_dismissed_${config.formId}`, "true");
        }
    }, [config.formId]);
    const restartTutor = useCallback(() => {
        setIsActive(true);
        localStorage.removeItem(`tutor_dismissed_${config.formId}`);
    }, [config.formId]);
    // Retorna la info para inyectar en el componente Icono de un campo específico
    const getFieldHelper = (fieldKey) => {
        return config.fields[fieldKey] || null;
    };
    return {
        isActive,
        config,
        dismissTutor,
        restartTutor,
        getFieldHelper
    };
}
