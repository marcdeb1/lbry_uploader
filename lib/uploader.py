import pandas as pd
import logging
from tinydb import TinyDB, Query
from pybry import LbryApi
from .importer import Importer
import configparser as cp
import hashlib

REQUIRED_FIELDS = ['name', 'bid', 'title', 'description', 'author', 'language', 'license', 'nsfw']
METADATA_FIELDS = ['fee', 'title', 'description', 'author', 'language', 'license', 'license_url', 'thumbnail', 'preview', 'nsfw', 'sources', 'channel_name', 'channel_id', 'claim_address']

class Uploader:
	def __init__(self, settings_name="default"):
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.INFO)
		self.importer = Importer()
		# Read settings
		self.config = cp.ConfigParser()
		settings_file = 'config/' + settings_name + '.ini'
		self.config.read(settings_file)
		self.settings = self.config['MainSettings']
		# LBRY API
		self.lbry = LbryApi()
		# Database
		self.db = TinyDB('db.json')
		
	def upload(self, file_name):
		self.logger.info("Starting uploader...")
		claim_data = self.importer.extract(file_name) # Importer returns an array of dicts
		number_claims = len(claim_data)
		number_published = 0
		self.logger.info(str(number_claims) + " claims to upload.")
		
		# LBRY daemon status
		status = self.check_lbry_status()
		if status:
			self.logger.info("LBRY Daemon ready for upload.")
		else:
			self.logger.error("Could not reach LBRY daemon. Please check that it is running.")
			return False

		for i, c in enumerate(claim_data):
			# Cleaning claim
			claim = self.clean_claim(c)
			if claim == False:
				self.logger.info("Skipping claim. [" + str(i) + "/" + str(number_claims) + "]")
				continue
				
			# Checking if claim was already published
			is_published = self.claim_is_published(claim)
			if is_published:
				self.logger.info("Claim '" + claim.get('title') + "' already published. [" + str(i) + "/" + str(number_claims) + "]")
				continue
				
			# Publishing
			p = self.publish(claim)[0]
			if 'error' in p:
				self.logger.warning("Claim '" + claim.get('title') + "' could not be published. Error: " + p.get('error') + "[" + str(i) + "/" + str(number_claims) + "]")
				continue
			else:
				s = self.save_claim(claim, p)
				self.logger.info("Claim '" + claim.get('title') + "' was successfully published. [" + str(i) + "/" + str(number_claims) + "]")
					
		self.logger.info("Exiting uploader...")
		return True

	def publish(self, claim):
		metadata = {}
		for m in METADATA_FIELDS:
			metadata[m] = claim.get(m)
		publish_data = {'name': claim.get('name'), 
						'file_path': claim.get('file_path'),
						'bid': claim.get('bid'),
						'metadata': metadata}
		publish_result = self.lbry.call('publish', publish_data)
		return publish_result
		
	def clean_claim(self, claim):
		for f in REQUIRED_FIELDS:
			if not claim.get(f) or claim.get(f) == "":
				if f in self.settings and self.settings.get(f) != "null" and self.settings.get(f) != "":
					claim[f] = self.settings[f]
					self.logger.warning("Field '" + f + "' not found, using default value.")
				else:
					self.logger.error("Field '" + f + "' not found and no default was provided.")
					return False
		return True
			
	def claim_is_published(self, claim):
		hash = hashlib.sha256(claim).hexdigest()
		Claim = Query()
		s = self.db.search((Claim.hash == hash) & (Claim.title == claim.get('title')))
		if not s:
			return False
		else:
			return True
		
	
	def save_claim(self, claim, publish_result):
		hash = hashlib.sha256(claim).hexdigest()
		save_data = {'title': claim.get('title'), 'hash': hash, 'txid': publish_result.get('txid'), 'claim_id': publish_result.get('claim_id')}
		return self.db.insert(save_data)
		
		
	def check_lbry_status(self):
		response = self.lbry.call("status")
		# Rencoyer exception
		if response[0].get('is_running'):
			return True
		return False