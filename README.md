# LBRY Uploader
An uploading tool for LBRY written in Python. For more information on the LBRY project, visit https://lbry.tech/.

## Installation

- If it is not published on pypi.org yet, install package pybry by following instructions at https://github.com/osilkin98/PyBRY.
- Clone or download lbry_uploader repository : `git clone https://github.com/marcdeb1/lbry_uploader.git`.
- Run `pip install .` in cloned folder.

## How to use

The uploader takes a file as an input (CSV or JSON) and uploads claims described in the file to LBRY. The most simple way to use it is by running : 

`python upload.py --input=input.csv --config=myconfig`

or

```
from lbry_uploader import Uploader
uploader = Uploader(config_name="myconfig") # config_name is optional
uploader.upload("input.json")
```

Note: The config argument is optional. Default settings (default.ini file) will be used if not provided.

## File input format

See sample files in repository for format. The following fields are required (in input or configuration) :
- name : URL of the claim
- file_path : file path of content to publish
- bid : Claim bid, e.g. 1.3.
- description
- author
- language
- license
- nsfw : true or false

Optional fields : fee_amount, fee_currency, fee_address, channel_name, claim_address, preview, thumbnail.

## Default values

Default values can be set in the configuration file. If values are not found or empty in the input file, the uploader will use the values from the configuration file. Edit default.ini to change the default values, or create a new 'ini' file and pass it as an argument to the uploader. The config file must be an 'ini' file. 
If not provided, name and title of the claim will be built from the file name. If file name is 'My Sample Video.mp4', the name of the claim will be 'my-sample-video' and the title will be 'My Sample Video'.
At the very least, the input file can contain only contain file_path, thumbnail and preview fields, with all the other fields coming from the configuration file.

## Stopping/Restarting the uploader

The uploader saves published claims in a database. Stopping and restarting the uploader will only publish the claims once.
