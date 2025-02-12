import ApiClient from "@/service/apiClient";
import { useMutation } from "@tanstack/react-query";

interface ProblemSearch {
  subreddit: string;
  timeframe: string;
}

const useProblemSearch = () => {
  const api = new ApiClient<ProblemSearch>("/analyze-problems");

  return useMutation({
    mutationKey: ["new problem search"],
    mutationFn: api.post,
  });
};

export default useProblemSearch;
