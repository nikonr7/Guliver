import { Header } from "@/components/shared/Header";

interface Props {
  children?: React.ReactNode;
}

const RootLayout = ({ children }: Props) => {
  return (
    <div className="h-full flex flex-col">
      <Header />
      <main className="flex-grow bg-slate-100">{children}</main>
    </div>
  );
};
export default RootLayout;
