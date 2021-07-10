import pandas as pd

object = pd.read_csv('data_parser.txt', header=None, sep=' ')
object.to_csv('data.csv',index=False, header=False)
