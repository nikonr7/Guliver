import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface EventResponce {
  data: Post[];
  subreddit: string;
  timeframe: string;
  status: string;
}

interface Post {
  id: string;
  created_at: string;
  title: string;
  selftext: string;
  analysis: string;
  url: string;
  score: number;
  similarity?: number;
}

interface TaskState {
  task_id: string | null;
  status: string;
  message: string;
}

interface SearchStore {
  task: TaskState | null;
  taskResults: EventResponce | null;
  isDone: boolean;
}

interface SearchStoreActions {
  createTask: (newTask: TaskState) => void;
  setTaskResults: (eventResponce: EventResponce | null) => void;
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
    setTaskResults: (results) =>
      set((state) => ({ ...state, taskResults: results })),
    setDone: (done) => set((state) => ({ ...state, isDone: done })),
  }))
);

export type { EventResponce, Post };
export default useSearchStore;
