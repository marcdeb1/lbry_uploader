from lbry_uploader import Uploader
import click

@click.command()
@click.option('--input', default='', help='File containing claims information.')
@click.option('--config', default='', help='Configuration file.')
def upload(input, config):
	u = Uploader(settings_name=config)
	u.upload(input)

	
if __name__ == '__main__':
    upload()