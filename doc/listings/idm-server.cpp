class HelloI : virtual public Demo::Hello {
public:
  void sayHello(const string& name,
                const Ice::Current& current) {
    cout << "Hello from '" << name << "'" << endl;
  }
};

class SimpleServer : public Ice::Application {
public:
  int run(int argc, char* argv[]) {

    Ice::ObjectPtr serv = new HelloI;
    IDM::AdapterPtr adapter =
      new IDM::Adapter(communicator(), "testAdapter");
    adapter->add(serv,
                 communicator()->stringToIdentity(argv[1]));
    adapter->activate();

    communicator()->waitForShutdown();
    return EXIT_SUCCESS;
  }
};

int main(int argc, char* argv[]) {
  SimpleServer app;
  return app.main(argc, argv);
}
