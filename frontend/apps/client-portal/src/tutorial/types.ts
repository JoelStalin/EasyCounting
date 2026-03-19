export type FieldHelpInfo = {
  fieldId: string;
  label: string;
  description: string;
  expectedFormat?: string;
  exampleValue?: string;
  isRequired: boolean;
  validationRules?: string;
  businessImpact?: string;
  recommendation?: string;
};

export type FormTutorialConfig = {
  formId: string;
  title: string;
  description: string;
  fields: Record<string, FieldHelpInfo>;
};
