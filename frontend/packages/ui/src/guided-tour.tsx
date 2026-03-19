import Joyride, { STATUS, type CallBackProps, type Step } from "react-joyride";

export type GuidedTourStep = Step;

interface GuidedTourProps {
  run: boolean;
  steps: GuidedTourStep[];
  onFinished: (status: "completed" | "dismissed", lastStep: number) => void;
}

export function GuidedTour({ run, steps, onFinished }: GuidedTourProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <Joyride
      run={run}
      steps={steps}
      continuous
      showSkipButton
      showProgress
      disableScrolling={false}
      callback={(data: CallBackProps) => {
        const lastStep = typeof data.index === "number" ? data.index : 0;
        if (data.status === STATUS.FINISHED) {
          onFinished("completed", lastStep);
        }
        if (data.status === STATUS.SKIPPED) {
          onFinished("dismissed", lastStep);
        }
      }}
      styles={{
        options: {
          backgroundColor: "#0f172a",
          primaryColor: "#38bdf8",
          textColor: "#e2e8f0",
          overlayColor: "rgba(2, 6, 23, 0.75)",
          arrowColor: "#0f172a",
          zIndex: 10000,
        },
        tooltip: {
          borderRadius: "14px",
        },
        buttonBack: {
          color: "#cbd5e1",
        },
        buttonSkip: {
          color: "#cbd5e1",
        },
      }}
      locale={{
        back: "Atras",
        close: "Cerrar",
        last: "Finalizar",
        next: "Siguiente",
        skip: "Omitir",
      }}
    />
  );
}
