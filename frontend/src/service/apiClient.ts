import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://localhost:8000/api",
});

class ApiClient<T> {
  private path: string;

  constructor(path: string) {
    this.path = path;
  }

  get = () => {
    return axiosInstance.get<T>(this.path);
  };

  post = (data: T) => {
    return axiosInstance.post(this.path, data);
  };
}
