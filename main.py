import sys

from watchdog.observers import Observer

from datisaworkreportintegrator.integrator import Handler


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'in'
    observer = Observer()
    event_handler = Handler()
    observer.schedule(event_handler, path)
    observer.start()
    observer.join()


if __name__ == '__main__':
    main()
