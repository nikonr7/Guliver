import { Post } from "@/context/searchStore";
import ReactMarkdown from "react-markdown";

const TaskResultCard = ({ title, analysis }: Post) => {
  return (
    <div className="bg-white px-8 py-6  shadow border rounded-md mb-10">
      <h4 className="text-lg font-medium">{title}</h4>
      <div>
        <ReactMarkdown>{analysis}</ReactMarkdown>
      </div>
    </div>
  );
};
export default TaskResultCard;
