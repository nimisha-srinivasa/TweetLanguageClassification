'''
Can be processed only in python 3 due to the presence of emoticons that cannot be encoded in a UCS-2 python 2.7.
'''
import re,string
import json
import jsonpickle
import os, csv
import pandas as pd

input_fname = "original_tweets.json"
output_fname = "processed_data.json"
category_fname = "uniformly_sampled.tsv"
data_dir_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'all_data'))
input_fname_path = os.path.abspath(os.path.join(data_dir_path, input_fname))
output_fname_path = os.path.abspath(os.path.join(data_dir_path, output_fname))
category_fname_path = os.path.abspath(os.path.join(data_dir_path, category_fname))

def preprocess_data(input_fname_path, category_fname_path):
	category_labels, id_category_map = create_category_labels(category_fname_path)
	#read the contents of the file into a list
	with open(input_fname_path) as f:
	    content = f.readlines()
    
	#set up the regex for preprocessing
	punctuation_regex = re.compile('[%s]' % re.escape(string.punctuation))
	digits_regex = re.compile('[%s]' % re.escape(string.digits))
	emoji_regex = re.compile(u"["
	        u"\U0001F600-\U0001F64F"  # emoticons
	        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
	        u"\U0001F680-\U0001F6FF"  # transport & map symbols
	        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
	        u"\U00002700-\U000027FF"
	        u"\U00002580-\U0000267F"
	        u"\U00002300-\U0000237F"
	        u"\U00002400-\U0000247F" 
	        u"\U00002B00-\U00002B7F]+", flags=re.UNICODE)

	url_regex = re.compile('(\w+:\/\/\S+)')     
	handle_regex = re.compile('(@[A-Za-z0-9_]+)')  
	hashtag_regex = re.compile('(#[A-Za-z0-9_]+)')

	#pre-process each line i.e., tweet individually
	rows = []
	index = []
	for line in content:
        #extract the content of the tweet
		line_content = line.split("\"")
		tweet_id = line_content[1]
		tweet_content = line_content[3]
        
        #remove HTML tags -- so far no HTML tags encountered in the dataset
        
        #remove new lines
		tweet_content = tweet_content.replace('\\n','')
    
        #remove URLs, Handles and Hashtags
		tweet_content = handle_regex.sub('', tweet_content)
		tweet_content = hashtag_regex.sub('', tweet_content)
		tweet_content = url_regex.sub('', tweet_content)
        
        #remove punctuations from the tweets
		tweet_content = punctuation_regex.sub('', tweet_content)
        #remove digits from the tweets
		tweet_content = digits_regex.sub('', tweet_content)
        #remove emojis from tweets
		tweet_content = emoji_regex.sub('', tweet_content)
        
        #write the tweet to file if only it has some content in it
		tweet_content = tweet_content.strip()
		if tweet_content and not(tweet_content.isspace()):
			rows.append({"id":tweet_id, "content":tweet_content, "label":id_category_map[tweet_id]})
			index.append(tweet_id)
    
    #build a dataframe
	data_frame = pd.DataFrame(rows,index=index)   
    #remove unwanted samples
	data_frame = remove_samples(data_frame, category_labels)
	return category_labels, data_frame

'''
remove instances of those languages that have less than 3 samples per language
'''
def create_category_labels(category_fname_path):
    #create the id-to-category map
    id_category_map={}
    category_labels = []
    with open(category_fname_path,'rt') as tsvfile:
        tsvin = csv.reader(tsvfile, delimiter='\t')
        for row in tsvin:
            if row[0] not in category_labels:
                category_labels.append(row[0])
            id_category_map[row[1]] = row[0]
    return category_labels, id_category_map 

def remove_samples(data_frame, category_labels):
    lang_doc_count=[0 for x in category_labels]
    removed_cat = []
    #count number of docs per category
    for index, row in data_frame.iterrows():
        lang_doc_count[category_labels.index(row["label"])]=lang_doc_count[category_labels.index(row["label"])]+1
    for x in range(len(lang_doc_count)):
        if lang_doc_count[x] <3:
            removed_cat.append(category_labels[x])
    #additionally remove bengali for now since it is creating a problem in baseline1
    bengali_label = u'bn'
    if bengali_label not in removed_cat:
    	removed_cat.append(bengali_label)

    #remove those classes from the dataset
    data_frame = data_frame[~data_frame.label.isin(removed_cat)]
    category_labels = [x for x in category_labels if x not in removed_cat] 
    print("final category labels are",len(category_labels),":", category_labels)      
    return data_frame

def write_df_to_file(data_frame, output_fname_path):

	with open(output_fname_path, 'w') as outfile:
	    outfile.write("[\n")
	    for index, row in data_frame.iterrows():
	        row_dict = {"id":index, "content":row["content"], "label":row["label"]}
	        row_json = json.dumps(row_dict, ensure_ascii=False)
	        outfile.write(row_json+",\n")
	#remove the last comma and close the json array
	with open(output_fname_path, 'rb+') as outfile:
	    outfile.seek(-2, os.SEEK_END)
	    outfile.truncate()
	    outfile.write("\n]".encode())

if __name__ == "__main__":
	category_labels = []
	category_labels, data_frame = preprocess_data(input_fname_path, category_fname_path)
	write_df_to_file(data_frame, output_fname_path)
