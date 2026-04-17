#!/usr/bin/env python3
import sys
import click
from engine import ClockworkEngine, ClockworkResult

@click.command()
@click.option('-c', '--code', 'code_path', required=True,
              help='Path to the JSON file containing the program code')
@click.option('-t', '--tests', 'test_path', required=True,
              help='Path to the JSON file containing test cases')
@click.option('-d', '--debug', is_flag=True,
              help='Enable debug output')
@click.option('-v', '--verbose', is_flag=True,
              help='Enable verbose test-by-test output')
def main(code_path: str, test_path: str, debug: bool, verbose: bool):
    engine = ClockworkEngine()

    # if visualize:
    #     from visualizer import Visualizer
    #     try:
    #         tests = engine._parse_tests(test_path)
    #     except Exception as e:
    #         click.echo(f"Error reading tests: {e}", err=True)
    #         sys.exit(1)
    #     if not tests:
    #         click.echo("No tests to visualize", err=True)
    #         sys.exit(1)
    #     visualizer = Visualizer(code_path, tests[0]['input'])
    #     visualizer.run()
    #     sys.exit(0)

    try:
        result: ClockworkResult = engine.grade(
            code_path=code_path,
            test_path=test_path,
            debug=debug,
            verbose=verbose
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    passed = result.num_pass_tests
    total = result.num_tests

    click.echo(f"Passed {passed} out of {total} cases.")
    sys.exit(0 if passed == total else 1)

if __name__ == '__main__':
    main()
