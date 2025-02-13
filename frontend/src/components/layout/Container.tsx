import clsx from "clsx";

interface Props {
  children?: React.ReactNode;
  className?: string;
}
const Container = ({ children, className }: Props) => {
  return <div className={clsx("container mx-auto", className)}>{children}</div>;
};
export default Container;
