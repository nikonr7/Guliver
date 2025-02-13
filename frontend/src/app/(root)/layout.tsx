import { Header } from "@/components/shared/Header";
import ReactQueryProvider from "@/components/ReactQueryProvider";

interface Props {
  children?: React.ReactNode;
}

const RootLayout = ({ children }: Props) => {
  return (
    <div className="h-full flex flex-col">
      <Header />
      <ReactQueryProvider>
        <main className="flex-grow bg-slate-100">{children}</main>
      </ReactQueryProvider>
    </div>
  );
};
export default RootLayout;
