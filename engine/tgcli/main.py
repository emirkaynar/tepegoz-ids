import sys

from tgcli.dash_cmd import handle_dash
from tgcli.sensor_cmd import handle_sensor
from tgcli.shared import WELCOME_BANNER


def run(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in ("--help", "-h", "help"):
        print(WELCOME_BANNER)
        return 0

    command = args[0]
    if command == "dash":
        return handle_dash(args[1:])
    if command == "sensor":
        return handle_sensor(args[1:])

    print(f"Unknown command: {command}")
    print('Run "tepegoz --help" for usage information.')
    return 2


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
