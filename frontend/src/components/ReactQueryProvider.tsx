"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

interface Props {
  children?: React.ReactNode;
}

const ReactQueryProvider = ({ children }: Props) => {
  const queryClient = new QueryClient();

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};
export default ReactQueryProvider;
