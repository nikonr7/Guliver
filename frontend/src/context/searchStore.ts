import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface TaskState {
  task_id: string | null;
  status: string;
  message: string;
}

interface SearchStore {
  task: TaskState | null;
  isDone: boolean;
}

interface SearchStoreActions {
  createTask: (newTask: TaskState) => void;
  setDone: (done: boolean) => void;
}

const defaultValues = {
  task: null,
  isDone: true,
};

const useSearchStore = create<SearchStore & SearchStoreActions>()(
  devtools((set) => ({
    ...defaultValues,
    createTask: (newTask) => set((state) => ({ ...state, task: newTask })),
    setDone: (done) => set((state) => ({ ...state, isDone: done })),
  }))
);

export default useSearchStore;
