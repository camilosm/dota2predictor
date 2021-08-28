import json
from operator import imod
from os import get_exec_path
import ijson
from tqdm import tqdm
import pandas as pd
from datetime import datetime, date

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics
import matplotlib.pyplot as plt

class Dota2Predictor:
	FEATURES = ['radiant_xp_adv', 'radiant_gold_adv']
	LABEL = 'radiant_win'
	HERO_COLS = ['hero'+str(n) for n in range(10)]

	def __init__(self, data_path, bigdata_filename) -> None:
		self.data_path = data_path
		self.data_filename = data_path+'matches_data.jsonl'
		self.bigdata_filename = bigdata_filename
		self.patches = {}
		with open(data_path+'patches.json', 'r') as patches_file:
			patches_data = json.load(patches_file)
			for patch in patches_data:
				self.patches[patch['name']] = datetime.strptime(patch['date'][:10], '%Y-%m-%d').date()

	
	def get_patch(self, match_date):
		for patch, patch_date in self.patches.items():
			if match_date >= patch_date:
				match_patch = patch
			else:
				break
		return match_patch

	def parse_bigdata(self, number_of_matches:int, patch:str, game_mode:int = 22, lobby_type:int = 7):
		bigdata_path = self.data_path+self.bigdata_filename
		with open(bigdata_path, 'r') as bigdata_file, open(self.data_filename, 'w') as data_file:
			matches = ijson.items(bigdata_file, 'item')
			progress_bar = tqdm(total=number_of_matches, desc='Parsing')
			usefull_matches = 0
			for match in matches:
				if match['human_players'] != 10 or match['game_mode'] != game_mode or match['lobby_type'] != lobby_type:
					continue
				match_date = datetime.fromtimestamp(match['start_time']).date()
				if float(self.get_patch(match_date)) > float(patch):
					break
				elif float(self.get_patch(match_date)) < float(patch):
					continue
				ignore_match = False
				match_data = {}
				for player in match['players']:
					if player['leaver_status'] != 0:
						ignore_match = True
						break
					player_slot = '{0:08b}'.format(player['player_slot'])
					player_pos = str(int(player_slot[5:],2) + (5 if player_slot[0] == '1' else 0))
					match_data['hero'+player_pos] = player['hero_id']
				if ignore_match:
					continue
				for feature in self.FEATURES:
					if feature not in match:
						ignore_match = True
						break
					feature_data = match[feature]
					if type(feature_data) is list:
						feature_data = feature_data[int(len(feature_data)/2)]
					match_data[feature] = feature_data
				if ignore_match:
					continue
				match_data[self.LABEL] = 1 if match[self.LABEL] == True else 0
				json.dump(match_data, data_file)
				data_file.write('\n')
				usefull_matches+=1
				progress_bar.update(1)
				if usefull_matches == number_of_matches:
					break
			progress_bar.close()
	
	def classify(self, classifier, name, train_set, test_set, metrics_data):
		classifier.fit(train_set['features'], train_set['labels'])
		labels_predicted = classifier.predict(test_set['features'])

		metrics_score = {}
		metrics_score['accuracy_score'] = metrics.accuracy_score(test_set['labels'], labels_predicted)
		metrics_score['recall_score'] = metrics.recall_score(test_set['labels'], labels_predicted)
		metrics_score['confusion_matrix'] = metrics.confusion_matrix(test_set['labels'], labels_predicted)

		metrics_data[name] = metrics_score

	def analise_data(self, features = 'all') -> list:
		if features == 'heroes':
			feature_cols = self.HERO_COLS
		elif features == 'advantages':
			feature_cols = self.FEATURES
		else:
			feature_cols = self.HERO_COLS + self.FEATURES
		data_cols =  feature_cols + [self.LABEL]
		matches = pd.DataFrame(columns=data_cols)
		with open(self.data_filename, 'r') as data_file:
			for entry in data_file:
				match = json.loads(entry)
				matches = matches.append(match, ignore_index=True)
		features = matches[feature_cols]
		labels = matches[self.LABEL].astype('int')

		features_train, features_test, labels_train, labels_test = train_test_split(features, labels, test_size=0.25)
		
		train_set = {'features': features_train, 'labels': labels_train}
		test_set = {'features': features_test, 'labels': labels_test}
		
		metrics_data = {}
		classifiers = {}
		
		classifiers['dtc'] = (DecisionTreeClassifier(), 'Decision Tree')
		classifiers['rfc'] = (RandomForestClassifier(), 'Random Forest')
		classifiers['knc'] = (KNeighborsClassifier(), 'K Neighbors')

		for id, (classifier, name)  in classifiers.items():
			self.classify(classifier, id, train_set, test_set, metrics_data)
			metrics.plot_confusion_matrix(classifier, test_set['features'], test_set['labels'])
			plt.suptitle(name)
			plt.show()

		# self.classify(DecisionTreeClassifier(), 'dtc', train_set, test_set, metrics_data)
		# self.classify(RandomForestClassifier(), 'rfc', train_set, test_set, metrics_data)
		# self.classify(KNeighborsClassifier(), 'knc', train_set, test_set, metrics_data)

		return metrics_data

