import os
import pandas as pd

class Importer:
	def extract(self, file_name):
		name, extension = os.path.splitext(file_name)
		df = pd.DataFrame()
		if extension == '.csv':
			df = self.extract_csv(file_name)
		return df.to_dict('records')
		
	def extract_csv(self, file_name):
		df = pd.read_csv(file_name)
		return df
		
	def extract_xls(self, file_name):
		pass
		
	def extract_json(self, file_name):
		pass