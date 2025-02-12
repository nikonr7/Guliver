"use client";
import { SubmitHandler, useForm } from "react-hook-form";

interface FormData {
  subreddit: string;
  timeframe: string;
}

const SearchForm = () => {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isValid },
  } = useForm<FormData>();

  const onSubmit: SubmitHandler<FormData> = (data) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col mb-4">
        <label htmlFor="subbreddit" className="text-gray-600 mb-1">
          <span className="text-red-500 font-bold">*</span> Subreddit
        </label>
        <input
          id="subbreddit"
          className="w-full px-3 py-1.5 border border-gray-300 rounded shadow-sm focus:outline-none  focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-gray-900 placeholder-gray-400"
          type="text"
          {...register("subreddit", { required: "Subreddit name is required" })}
          onChange={(e) => setValue("subreddit", e.target.value.trim())}
          placeholder="Enter a subreddit without /r"
        />
        {errors.subreddit && (
          <p className="text-red-500 text-sm mt-1">
            {errors.subreddit.message}
          </p>
        )}
      </div>

      <div className="flex flex-col">
        <label htmlFor="timeframe" className="text-gray-600 mb-1">
          <span className="text-red-500 font-bold">*</span> Time Frame
        </label>

        <select
          {...register("timeframe")}
          id="timeframe"
          className="w-full px-3 py-1.5 border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-300 focus:border-blue-300 text-gray-900"
        >
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="year">Last Year</option>
        </select>

        {errors.timeframe && (
          <p className="text-red-500">{errors.timeframe.message}</p>
        )}
      </div>

      <button
        type="submit"
        className="w-full mt-4 py-2 px-4 rounded text-sm font-medium text-white bg-blue-500 hover:bg-blue-600 focus:outline-none transition-colors"
      >
        Find Problems
      </button>
    </form>
  );
};
export default SearchForm;
