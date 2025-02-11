from backend.app.app import run_server
from dotenv import load_dotenv

def main():
  load_dotenv()
  run_server()

if __name__=="__main__":
  main()