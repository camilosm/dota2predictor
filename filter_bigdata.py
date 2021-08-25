import json
from tqdm import tqdm

data_path = 'data/'
bigdata_columns = ['lobby_type', 'game_mode', 'radiant_win']
data_columns = ['hero'+str(n) for n in range(10)] + bigdata_columns

# for testing only
qt_entries = 0

with open(data_path+'bigdata.json', 'r') as bigdata_file, open(data_path+'data.jsonl', 'w') as data_file:
	for line in tqdm(bigdata_file, total=1000065, desc='Filtering'):
		try:
			entry = json.loads(line)
		except:
			continue	
		
		if entry['human_players'] != 10:
			continue
		row = {}
		ignore_entry = False
		for player in entry['players']:
			if player['leaver_status'] != 0:
				ignore_entry=True
				break
			player_slot = '{0:08b}'.format(player['player_slot'])			
			player_pos = str(int(player_slot[5:],2) + (5 if player_slot[0] == '1' else 0))
			row['hero'+player_pos] = player['hero_id']
		if ignore_entry:
			continue
		for key in bigdata_columns:
			if key not in entry:
				break
			row[key] = entry[key]
		win = lambda value : 1 if value == True else 0
		row['radiant_win'] = win(row['radiant_win'])
		json.dump(row, data_file)
		data_file.write('\n')

		# for testing only
		qt_entries+=1
		if qt_entries == 1000:
			break
			
# for testing only
print(qt_entries)