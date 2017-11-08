import sys

from watchdog.observers import Observer

from datisaworkreportintegrator.integrator import Handler, Integrator


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'in'
    observer = Observer()
    integrator = Integrator(path)
    event_handler = Handler(integrator)
    observer.schedule(event_handler, path)
    observer.start()
    integrator.run()


if __name__ == '__main__':
    main()
