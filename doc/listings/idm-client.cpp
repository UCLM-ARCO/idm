class SimpleClient : public Ice::Application {
public:
  int run(int argc, char* argv[]) {
    IDM::SocketPtr sock = new IDM::Socket(communicator());
    Ice::ObjectPrx obj = sock->plug(argv[1], IDM::QoS());

    Demo::HelloPrx prx = Demo::HelloPrx::uncheckedCast(obj);
    prx->sayHello("John");

    return EXIT_SUCCESS;
  }
};

int main(int argc, char* argv[]) {
  SimpleClient app;
  return app.main(argc, argv);
}
