import re

fin = open("data.txt", "rt")
fout = open('data_parser.txt','wt')
for line in fin:
	fout.write(re.sub('\s+',' ',line) + '\n')
fin.close()
fout.close()