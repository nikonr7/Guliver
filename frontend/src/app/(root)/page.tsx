import SearchCard from "@/components/card/SearchCard";
import Container from "@/components/layout/Container";

const HomePage = () => {
  return (
    <div className="h-full">
      <Container className="pt-10 flex h-full gap-8">
        <aside className="w-96 flex-grow-0">
          <SearchCard />
        </aside>
        <div className="flex-grow bg-red-100"></div>
      </Container>
    </div>
  );
};
export default HomePage;
