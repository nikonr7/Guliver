"use client";

import useSearchStore, { EventResponce } from "@/context/searchStore";
import { useEffect } from "react";
import TaskResultCard from "../card/TaskResultCard";

interface StatusResponce {
  status: string;
  task_id: string;
}

const ResultsPanel = () => {
  const { task, setTaskResults, setDone, isDone, taskResults } =
    useSearchStore();

  useEffect(() => {
    if (task?.task_id) {
      const eventSource = new EventSource(
        `http://localhost:8000/events/${task.task_id}`
      );

      eventSource.onmessage = (event) => {
        const res: EventResponce | StatusResponce = JSON.parse(event.data);
        if (res.status == "in process") {
          setTaskResults(null);
          return;
        }
        eventSource.close();
        setTaskResults(res as EventResponce);
        setDone(true);
      };
    }
  }, [task]);
  return (
    <div>
      {isDone &&
        taskResults?.data.map((post) => (
          <TaskResultCard key={post.id} {...post} />
        ))}
    </div>
  );
};

export default ResultsPanel;
