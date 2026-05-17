import sys

from tgcli.dash_cmd import handle_dash
from tgcli.sensor_cmd import handle_sensor


def run(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        print("Usage: tepegoz <dash|sensor> ...")
        return 2

    command = args[0]
    if command == "dash":
        return handle_dash(args[1:])
    if command == "sensor":
        return handle_sensor(args[1:])

    print(f"Unknown command: {command}")
    return 2


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
