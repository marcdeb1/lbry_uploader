import pandas as pd
import logging
from tinydb import TinyDB, Query
from pybry import LbryApi
from .importer import Importer
import configparser as cp
import json
from datetime import datetime
import hashlib

REQUIRED_FIELDS = ['name', 'bid', 'title', 'description', 'author', 'language', 'license', 'nsfw']
OPTIONAL_FIELDS = ['fee_amount', 'fee_currency', 'fee_address', 'channel_name', 'claim_address', 'preview']
PUBLISH_FIELDS = ['name', 'file_path', 'bid', 'title', 'description', 'author', 'language', 'license', 'thumbnail', 'preview', 'nsfw', 'license_url', 'channel_name', 'channel_id', 'claim_address']

class Uploader:
	def __init__(self, settings_name="default"):
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.INFO)
		handler = logging.StreamHandler()
		formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)
		self.importer = Importer()
		# Settings
		self.config = cp.ConfigParser()
		settings_file = 'config/' + settings_name + '.ini'
		self.config.read(settings_file)
		self.settings = self.config['MainConfig']
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
			self.logger.info("Exiting uploader...")
			return False

		for i, c in enumerate(claim_data):
			self.logger.info("Uploading claim '" + c.get('title') + "'...")
			# Cleaning claim
			claim = self.clean_claim(c)
			if claim == False:
				self.logger.info("Skipping claim. [" + str(i + 1) + "/" + str(number_claims) + "]")
				continue

			# Checking if claim was already published
			is_published = self.claim_is_published(claim)
			if is_published:
				self.logger.info("Claim '" + claim.get('title') + "' already published. [" + str(i + 1) + "/" + str(number_claims) + "]")
				continue

			# Publishing
			p = self.publish(claim)[0]
			if 'error' in p:
				self.logger.warning("Claim '" + claim.get('title') + "' could not be published. Error: " + p.get('error') + "[" + str(i + 1) + "/" + str(number_claims) + "]")
				continue
			else:
				s = self.save_claim(claim, p)
				number_published += 1
				self.logger.info("Claim '" + claim.get('title') + "' was successfully published. [" + str(i + 1) + "/" + str(number_claims) + "]")

		self.logger.info(str(number_published) + "/" + str(number_claims) + " claims published.")
		self.logger.info("Exiting uploader...")
		return True

	def clean_claim(self, claim):
		for f in REQUIRED_FIELDS:
			if claim.get(f) == None or claim.get(f) == "":
				if f in self.settings and self.settings.get(f) != "null" and self.settings.get(f) != "":
					claim[f] = self.settings[f]
					self.logger.warning("Required field '" + f + "' not found, using default value.")
				else:
					self.logger.error("Required field '" + f + "' not found and no default was provided.")
					return False
		for f in OPTIONAL_FIELDS:
			if claim.get(f) == None or claim.get(f) == "":
				if f in self.settings and self.settings.get(f) != "null" and self.settings.get(f) != "":
					claim[f] = self.settings[f]
					self.logger.info("Optional field '" + f + "' not found, using default value.")
		return claim

	def publish(self, claim):
		publish_data = {}
		for f in PUBLISH_FIELDS:
			publish_data[f] = claim.get(f)
		fee_data = {'currency': claim.get('fee_currency'), 'amount': claim.get('fee_amount'), 'address': claim.get('fee_address') }
		publish_data['fee'] = fee_data
		try:
			publish_result = self.lbry.call('publish', publish_data)
			return publish_result
		except Exception as e:
			self.logger.error('Error when publishing : ' + str(e) + str(e.response))
		
	def claim_is_published(self, claim):
		m = hashlib.md5()
		m.update(json.dumps(claim, sort_keys=True).encode('utf-8'))
		h = m.hexdigest()
		Claim = Query()
		s = self.db.search((Claim.hash == h) & (Claim.title == claim.get('title')))
		if not s:
			return False
		else:
			return True
	
	def save_claim(self, claim, publish_result):
		m = hashlib.md5()
		m.update(json.dumps(claim, sort_keys=True).encode('utf-8'))
		h = m.hexdigest()
		save_data = {'title': claim.get('title'), 'hash': h, 'txid': publish_result.get('txid'), 'claim_id': publish_result.get('claim_id'), 'publish_time': str(datetime.now())}
		return self.db.insert(save_data)
		
	def check_lbry_status(self):
		response = self.lbry.call("status")
		# Rencoyer exception
		if response[0].get('is_running'):
			return True
		return False