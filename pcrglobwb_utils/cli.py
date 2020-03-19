"""Console script for pcrglobwb_utils."""
import sys
import click


@click.command()
@click.argument('cfg',)

# @click.option('-s', '--single-file', default='', help='only single nc-file to be analysed')
# @click.option('-m', '--multi-file', default='', help='multiple nc-files to be analysed')

def main(cfg):
    """Console script for pcrglobwb_utils."""
    click.echo("Replace this message by putting your code into "
               "pcrglobwb_utils.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")

    click.echo("Hello main, {}".format(cfg))

    test = cfg
    print(str(test))

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
