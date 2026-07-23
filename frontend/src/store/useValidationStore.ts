import { create } from 'zustand';
import axios from 'axios';
import { ValidationReport } from '../types';
import { useChatStore } from './useChatStore';

interface ValidationStore {
  isValidating: boolean;
  isSubmitting: boolean;
  validationReport: ValidationReport | null;
  submitSuccessMessage: string | null;
  setValidationReport: (report: ValidationReport) => void;
  triggerValidation: () => Promise<void>;
  submitFinalTree: () => Promise<void>;
  clearSubmitStatus: () => void;
}

export const useValidationStore = create<ValidationStore>((set, get) => ({
  isValidating: false,
  isSubmitting: false,
  validationReport: null,
  submitSuccessMessage: null,

  setValidationReport: (report: ValidationReport) => set({ validationReport: report }),

  triggerValidation: async () => {
    const convId = useChatStore.getState().conversationId;
    if (!convId) return;

    set({ isValidating: true });
    try {
      const resp = await axios.post(`/api/conversations/${convId}/validate`);
      set({
        validationReport: resp.data.validation_report,
        isValidating: false,
      });
    } catch (e) {
      console.error('Validation request failed:', e);
      set({ isValidating: false });
    }
  },

  submitFinalTree: async () => {
    const convId = useChatStore.getState().conversationId;
    if (!convId) return;

    set({ isSubmitting: true, submitSuccessMessage: null });
    try {
      const resp = await axios.post(`/api/conversations/${convId}/submit`);
      set({
        isSubmitting: false,
        submitSuccessMessage: `Successfully exported final_tree.json and validation_report.json to project root!`,
        validationReport: resp.data.validation_report,
      });
    } catch (e: any) {
      console.error('Submission failed:', e);
      const detail = e.response?.data?.detail;
      const report = detail?.report;
      set({
        isSubmitting: false,
        validationReport: report || { ok: false, errors: [{ path: '#', code: 'SUBMIT_FAILED', message: detail?.message || e.message }] },
      });
    }
  },

  clearSubmitStatus: () => set({ submitSuccessMessage: null }),
}));
