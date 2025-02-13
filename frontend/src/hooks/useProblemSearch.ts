import useSearchStore from "@/context/searchStore";
import ApiClient from "@/service/apiClient";
import { useMutation } from "@tanstack/react-query";

interface AnalysisResponce {
  message: string;
  success: string;
  task_id: string;
}

const useProblemSearch = () => {
  const { createTask, setDone } = useSearchStore();
  const api = new ApiClient<AnalysisResponce>("/analyze-problems");

  return useMutation({
    mutationKey: ["new problem search"],
    mutationFn: api.post,
    onSuccess: (res) => {
      const data = res.data;
      createTask({
        message: data.message,
        status: data.success,
        task_id: data.task_id,
      });
      setDone(false);
    },
  });
};

export default useProblemSearch;
