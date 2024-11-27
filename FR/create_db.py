# Import pandas library
import pandas as pd
 
# initialize list of lists
data = []
 
# Create the pandas DataFrame
image_dataset = pd.DataFrame(data, columns=['Image_Name', 'Crossing_Time'])
#############################################################
csv_path="/home/ubuntu/Downloads/Telegram Desktop/FR/FR_db.csv"
image_dataset.to_csv(csv_path, index=False)